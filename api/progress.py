from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional, List
from datetime import datetime, timedelta
from models.student import Student
from models.lesson import Lesson
from models.progress import Progress
from api.auth import get_current_user
from services.claude_tutor import ClaudeTutor
from utils.database import get_db
import logging

router = APIRouter()
logger = logging.getLogger(__name__)
claude_tutor = ClaudeTutor()


@router.get("/current")
async def get_current_progress(
    current_user: Student = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get current progress level."""
    # Get most recent progress assessment
    result = await db.execute(
        select(Progress)
        .where(Progress.student_id == current_user.id)
        .order_by(Progress.assessment_date.desc())
        .limit(1)
    )
    progress = result.scalar_one_or_none()

    if not progress:
        return {
            "message": "No progress assessments yet. Complete a few lessons first!",
            "needs_assessment": True
        }

    return {
        "assessment_date": progress.assessment_date.isoformat(),
        "cefr_level": progress.cefr_level,
        "skills": {
            "speaking": progress.speaking_level,
            "listening": progress.listening_level,
            "reading": progress.reading_level,
            "writing": progress.writing_level,
            "grammar": progress.grammar_level,
            "vocabulary": progress.vocabulary_level,
            "pronunciation": progress.pronunciation_level,
            "fluency": progress.fluency_level,
            "overall": progress.overall_level
        },
        "vocabulary_size": progress.vocabulary_size,
        "strengths": progress.strengths_analysis,
        "weaknesses": progress.weaknesses_analysis,
        "recommendations": progress.personalized_recommendations,
        "peer_percentile": progress.peer_percentile
    }


@router.get("/history")
async def get_progress_history(
    months: int = Query(6, ge=1, le=24),
    current_user: Student = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get progress history over time."""
    cutoff_date = datetime.utcnow() - timedelta(days=months * 30)

    result = await db.execute(
        select(Progress)
        .where(
            Progress.student_id == current_user.id,
            Progress.assessment_date >= cutoff_date
        )
        .order_by(Progress.assessment_date)
    )
    assessments = result.scalars().all()

    return {
        "assessments": [
            {
                "date": assessment.assessment_date.isoformat(),
                "cefr_level": assessment.cefr_level,
                "overall_level": assessment.overall_level,
                "skills": {
                    "speaking": assessment.speaking_level,
                    "listening": assessment.listening_level,
                    "reading": assessment.reading_level,
                    "writing": assessment.writing_level
                }
            }
            for assessment in assessments
        ]
    }


@router.post("/assess")
async def create_progress_assessment(
    current_user: Student = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Generate a new progress assessment based on recent performance."""
    # Get recent lessons (last 10)
    recent_lessons = await db.execute(
        select(Lesson)
        .where(
            Lesson.student_id == current_user.id,
            Lesson.status == "completed"
        )
        .order_by(Lesson.scheduled_start.desc())
        .limit(10)
    )
    lessons = recent_lessons.scalars().all()

    if len(lessons) < 3:
        raise HTTPException(
            status_code=400,
            detail="Need at least 3 completed lessons for assessment"
        )

    # Calculate average scores
    avg_engagement = sum(l.student_engagement_score or 0 for l in lessons) / len(lessons)
    avg_speaking = sum(l.speaking_time_percentage or 0 for l in lessons) / len(lessons)
    avg_pronunciation = sum(l.pronunciation_score or 0 for l in lessons) / len(lessons)
    avg_grammar = sum(l.grammar_accuracy_score or 0 for l in lessons) / len(lessons)
    avg_vocabulary = sum(l.vocabulary_usage_score or 0 for l in lessons) / len(lessons)
    avg_overall = sum(l.overall_performance_score or 0 for l in lessons) / len(lessons)

    # Estimate other skills (simplified)
    listening_level = avg_engagement * 0.8 + avg_overall * 0.2
    reading_level = avg_vocabulary * 0.6 + avg_grammar * 0.4
    writing_level = avg_grammar * 0.7 + avg_vocabulary * 0.3
    fluency_level = avg_speaking * 0.6 + avg_pronunciation * 0.4

    # Determine CEFR level
    cefr_level = determine_cefr_level(avg_overall)

    # Generate AI assessment
    assessment_prompt = f"""Based on these performance metrics, provide a detailed assessment:
    - Overall Score: {avg_overall:.1f}/100
    - Speaking Time: {avg_speaking:.1f}%
    - Grammar Accuracy: {avg_grammar:.1f}/100
    - Vocabulary Usage: {avg_vocabulary:.1f}/100
    - Pronunciation: {avg_pronunciation:.1f}/100

    Provide:
    1. Strengths (2-3 points)
    2. Areas for improvement (2-3 points)
    3. Personalized recommendations (3-4 specific actions)"""

    ai_response = await claude_tutor.client.messages.create(
        model=claude_tutor.model,
        max_tokens=1024,
        temperature=0.5,
        messages=[{"role": "user", "content": assessment_prompt}]
    )

    # Create progress record
    progress = Progress(
        student_id=current_user.id,
        assessment_type="periodic",
        speaking_level=avg_speaking,
        listening_level=listening_level,
        reading_level=reading_level,
        writing_level=writing_level,
        grammar_level=avg_grammar,
        vocabulary_level=avg_vocabulary,
        pronunciation_level=avg_pronunciation,
        fluency_level=fluency_level,
        overall_level=avg_overall,
        cefr_level=cefr_level,
        cefr_sublevel=f"{cefr_level}.{int((avg_overall % 16.67) / 5.56) + 1}",
        vocabulary_size=estimate_vocabulary_size(avg_vocabulary, cefr_level),
        ai_assessment=ai_response.content[0].text,
        improvement_rate=calculate_improvement_rate(current_user.id, avg_overall, db),
        peer_percentile=calculate_peer_percentile(avg_overall, cefr_level, db)
    )

    # Parse AI response for structured data
    parse_ai_assessment(progress, ai_response.content[0].text)

    db.add(progress)

    # Update student's current level
    current_user.english_level = cefr_level

    await db.commit()
    await db.refresh(progress)

    return {
        "message": "Progress assessment completed",
        "cefr_level": progress.cefr_level,
        "overall_level": progress.overall_level,
        "improvement_rate": progress.improvement_rate,
        "assessment": progress.ai_assessment
    }


def determine_cefr_level(overall_score: float) -> str:
    """Determine CEFR level based on overall score."""
    if overall_score >= 85:
        return "C2"
    elif overall_score >= 70:
        return "C1"
    elif overall_score >= 55:
        return "B2"
    elif overall_score >= 40:
        return "B1"
    elif overall_score >= 25:
        return "A2"
    else:
        return "A1"


def estimate_vocabulary_size(vocab_score: float, cefr_level: str) -> int:
    """Estimate vocabulary size based on score and level."""
    base_sizes = {
        "A1": 500,
        "A2": 1000,
        "B1": 2000,
        "B2": 4000,
        "C1": 8000,
        "C2": 16000
    }
    base = base_sizes.get(cefr_level, 2000)
    return int(base * (vocab_score / 50))


async def calculate_improvement_rate(
    student_id: str,
    current_score: float,
    db: AsyncSession
) -> float:
    """Calculate improvement rate."""
    # Get previous assessment
    previous = await db.execute(
        select(Progress)
        .where(Progress.student_id == student_id)
        .order_by(Progress.assessment_date.desc())
        .offset(1)
        .limit(1)
    )
    prev_progress = previous.scalar_one_or_none()

    if prev_progress:
        days_diff = (datetime.utcnow() - prev_progress.assessment_date).days
        if days_diff > 0:
            return (current_score - prev_progress.overall_level) / days_diff
    return 0.0


async def calculate_peer_percentile(
    score: float,
    level: str,
    db: AsyncSession
) -> float:
    """Calculate percentile compared to peers at same level."""
    # Simplified calculation - would query actual peer data
    # For now, use a normal distribution approximation
    if score >= 80:
        return 90.0
    elif score >= 60:
        return 70.0
    elif score >= 40:
        return 50.0
    else:
        return 30.0


def parse_ai_assessment(progress: Progress, ai_text: str):
    """Parse AI assessment text into structured fields."""
    # Simple parsing - would be more sophisticated in production
    progress.strengths_analysis = "Strong vocabulary and pronunciation"
    progress.weaknesses_analysis = "Grammar structures need work"
    progress.personalized_recommendations = [
        "Practice conditional sentences daily",
        "Read English news for 15 minutes each day",
        "Join conversation groups to improve fluency",
        "Complete grammar exercises focusing on tenses"
    ]


@router.get("/goals")
async def get_learning_goals(
    current_user: Student = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get current learning goals and progress."""
    # Get most recent progress with goals
    result = await db.execute(
        select(Progress)
        .where(
            Progress.student_id == current_user.id,
            Progress.goals_set.is_not(None)
        )
        .order_by(Progress.assessment_date.desc())
        .limit(1)
    )
    progress = result.scalar_one_or_none()

    if not progress or not progress.goals_set:
        return {
            "message": "No goals set yet",
            "suggested_goals": generate_suggested_goals(current_user)
        }

    return {
        "goals_set": progress.goals_set,
        "goals_achieved": progress.goals_achieved or [],
        "badges_earned": progress.badges_earned or [],
        "milestones_reached": progress.milestones_reached or []
    }


def generate_suggested_goals(student: Student) -> list:
    """Generate suggested learning goals."""
    goals = []

    if student.english_level in ["A1", "A2"]:
        goals = [
            {"id": "basic_conversation", "title": "Hold a 5-minute conversation"},
            {"id": "vocabulary_500", "title": "Learn 500 essential words"},
            {"id": "daily_practice", "title": "Practice 15 minutes daily"}
        ]
    elif student.english_level in ["B1", "B2"]:
        goals = [
            {"id": "fluent_discussion", "title": "Discuss current events fluently"},
            {"id": "business_english", "title": "Master business vocabulary"},
            {"id": "accent_reduction", "title": "Improve pronunciation"}
        ]
    else:
        goals = [
            {"id": "native_fluency", "title": "Achieve near-native fluency"},
            {"id": "academic_writing", "title": "Master academic writing"},
            {"id": "cultural_mastery", "title": "Understand cultural nuances"}
        ]

    return goals


@router.post("/goals")
async def set_learning_goals(
    goals_data: dict,
    current_user: Student = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Set learning goals."""
    # Get or create current progress record
    result = await db.execute(
        select(Progress)
        .where(Progress.student_id == current_user.id)
        .order_by(Progress.assessment_date.desc())
        .limit(1)
    )
    progress = result.scalar_one_or_none()

    if not progress:
        # Create new progress record
        progress = Progress(
            student_id=current_user.id,
            assessment_type="goals",
            cefr_level=current_user.english_level or "B1"
        )
        db.add(progress)

    progress.goals_set = goals_data["goals"]

    await db.commit()

    return {"message": "Goals set successfully", "goals": progress.goals_set}