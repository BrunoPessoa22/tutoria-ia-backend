from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import Optional, List
from datetime import datetime, timedelta
from models.student import Student
from models.lesson import Lesson
from models.curriculum import Curriculum
from api.auth import get_current_user
from services.claude_tutor import ClaudeTutor
from utils.database import get_db
import logging
import uuid

router = APIRouter()
logger = logging.getLogger(__name__)
claude_tutor = ClaudeTutor()


@router.post("/schedule")
async def schedule_lesson(
    lesson_data: dict,
    current_user: Student = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Schedule a new lesson."""
    try:
        # Check if time slot is available
        scheduled_start = datetime.fromisoformat(lesson_data["scheduled_start"])
        duration_minutes = lesson_data.get("duration_minutes", 60)
        scheduled_end = scheduled_start + timedelta(minutes=duration_minutes)

        # Check for conflicts
        conflict = await db.execute(
            select(Lesson).where(
                and_(
                    Lesson.student_id == current_user.id,
                    Lesson.status.in_(["scheduled", "in_progress"]),
                    Lesson.scheduled_start < scheduled_end,
                    Lesson.scheduled_end > scheduled_start
                )
            )
        )

        if conflict.scalar_one_or_none():
            raise HTTPException(
                status_code=400,
                detail="Time slot conflicts with existing lesson"
            )

        # Check subscription or trial lessons
        if current_user.subscription_status == "trial":
            if current_user.trial_lessons_remaining <= 0:
                raise HTTPException(
                    status_code=403,
                    detail="No trial lessons remaining. Please subscribe."
                )

        # Get curriculum module if specified
        curriculum_module = None
        if lesson_data.get("curriculum_module"):
            result = await db.execute(
                select(Curriculum).where(
                    Curriculum.module_code == lesson_data["curriculum_module"]
                )
            )
            curriculum_module = result.scalar_one_or_none()

        # Generate lesson plan
        student_profile = {
            "full_name": current_user.full_name,
            "english_level": current_user.english_level or "B1",
            "learning_style": current_user.learning_style,
            "weak_areas": current_user.weak_areas or [],
            "interests": current_user.interests or []
        }

        lesson_plan = await claude_tutor.generate_lesson_plan(
            student_profile=student_profile,
            topic=lesson_data.get("topic", "General English Practice"),
            duration_minutes=duration_minutes,
            curriculum_module=lesson_data.get("curriculum_module")
        )

        # Create lesson
        lesson = Lesson(
            student_id=current_user.id,
            scheduled_start=scheduled_start,
            scheduled_end=scheduled_end,
            duration_minutes=duration_minutes,
            lesson_type=lesson_data.get("lesson_type", "live"),
            status="scheduled",
            topic=lesson_data.get("topic"),
            lesson_plan=lesson_plan,
            curriculum_module=lesson_data.get("curriculum_module"),
            difficulty_level=current_user.english_level
        )

        db.add(lesson)

        # Decrement trial lessons if applicable
        if current_user.subscription_status == "trial":
            current_user.trial_lessons_remaining -= 1

        await db.commit()
        await db.refresh(lesson)

        return {
            "message": "Lesson scheduled successfully",
            "lesson_id": str(lesson.id),
            "scheduled_start": lesson.scheduled_start.isoformat(),
            "scheduled_end": lesson.scheduled_end.isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error scheduling lesson: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/upcoming")
async def get_upcoming_lessons(
    limit: int = Query(10, ge=1, le=50),
    current_user: Student = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get upcoming lessons."""
    result = await db.execute(
        select(Lesson)
        .where(
            Lesson.student_id == current_user.id,
            Lesson.scheduled_start > datetime.utcnow(),
            Lesson.status == "scheduled"
        )
        .order_by(Lesson.scheduled_start)
        .limit(limit)
    )
    lessons = result.scalars().all()

    return {
        "lessons": [
            {
                "id": str(lesson.id),
                "scheduled_start": lesson.scheduled_start.isoformat(),
                "scheduled_end": lesson.scheduled_end.isoformat(),
                "duration_minutes": lesson.duration_minutes,
                "topic": lesson.topic,
                "lesson_type": lesson.lesson_type,
                "curriculum_module": lesson.curriculum_module
            }
            for lesson in lessons
        ]
    }


@router.get("/{lesson_id}")
async def get_lesson(
    lesson_id: str,
    current_user: Student = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get lesson details."""
    result = await db.execute(
        select(Lesson).where(
            Lesson.id == uuid.UUID(lesson_id),
            Lesson.student_id == current_user.id
        )
    )
    lesson = result.scalar_one_or_none()

    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    return {
        "id": str(lesson.id),
        "scheduled_start": lesson.scheduled_start.isoformat(),
        "scheduled_end": lesson.scheduled_end.isoformat(),
        "actual_start": lesson.actual_start.isoformat() if lesson.actual_start else None,
        "actual_end": lesson.actual_end.isoformat() if lesson.actual_end else None,
        "status": lesson.status,
        "topic": lesson.topic,
        "lesson_plan": lesson.lesson_plan,
        "materials_used": lesson.materials_used,
        "vocabulary_taught": lesson.vocabulary_taught,
        "grammar_points": lesson.grammar_points,
        "homework_assigned": lesson.homework_assigned,
        "performance_metrics": {
            "engagement_score": lesson.student_engagement_score,
            "speaking_time": lesson.speaking_time_percentage,
            "pronunciation": lesson.pronunciation_score,
            "grammar_accuracy": lesson.grammar_accuracy_score,
            "vocabulary_usage": lesson.vocabulary_usage_score,
            "overall": lesson.overall_performance_score
        },
        "ai_feedback": lesson.ai_feedback,
        "student_rating": lesson.student_rating
    }


@router.post("/{lesson_id}/start")
async def start_lesson(
    lesson_id: str,
    current_user: Student = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Start a scheduled lesson."""
    result = await db.execute(
        select(Lesson).where(
            Lesson.id == uuid.UUID(lesson_id),
            Lesson.student_id == current_user.id,
            Lesson.status == "scheduled"
        )
    )
    lesson = result.scalar_one_or_none()

    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found or already started")

    # Update lesson status
    lesson.status = "in_progress"
    lesson.actual_start = datetime.utcnow()

    await db.commit()

    return {
        "message": "Lesson started",
        "lesson_id": str(lesson.id),
        "lesson_plan": lesson.lesson_plan
    }


@router.post("/{lesson_id}/end")
async def end_lesson(
    lesson_id: str,
    summary_data: dict,
    current_user: Student = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """End a lesson and save summary."""
    result = await db.execute(
        select(Lesson).where(
            Lesson.id == uuid.UUID(lesson_id),
            Lesson.student_id == current_user.id,
            Lesson.status == "in_progress"
        )
    )
    lesson = result.scalar_one_or_none()

    if not lesson:
        raise HTTPException(status_code=404, detail="Active lesson not found")

    # Update lesson with summary data
    lesson.status = "completed"
    lesson.actual_end = datetime.utcnow()
    lesson.duration_minutes = int(
        (lesson.actual_end - lesson.actual_start).total_seconds() / 60
    )

    # Save performance metrics
    if "performance" in summary_data:
        lesson.student_engagement_score = summary_data["performance"].get("engagement")
        lesson.speaking_time_percentage = summary_data["performance"].get("speaking_time")
        lesson.pronunciation_score = summary_data["performance"].get("pronunciation")
        lesson.grammar_accuracy_score = summary_data["performance"].get("grammar")
        lesson.vocabulary_usage_score = summary_data["performance"].get("vocabulary")
        lesson.overall_performance_score = summary_data["performance"].get("overall")

    # Save content covered
    if "content" in summary_data:
        lesson.vocabulary_taught = summary_data["content"].get("vocabulary")
        lesson.grammar_points = summary_data["content"].get("grammar")
        lesson.homework_assigned = summary_data["content"].get("homework")

    # Save AI feedback
    if "ai_feedback" in summary_data:
        lesson.ai_feedback = summary_data["ai_feedback"]

    # Update student statistics
    current_user.total_lessons_completed += 1
    current_user.total_minutes_studied += lesson.duration_minutes
    current_user.last_active_date = datetime.utcnow()

    await db.commit()

    return {
        "message": "Lesson completed successfully",
        "duration_minutes": lesson.duration_minutes,
        "overall_score": lesson.overall_performance_score
    }


@router.post("/{lesson_id}/cancel")
async def cancel_lesson(
    lesson_id: str,
    reason: Optional[str] = None,
    current_user: Student = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Cancel a scheduled lesson."""
    result = await db.execute(
        select(Lesson).where(
            Lesson.id == uuid.UUID(lesson_id),
            Lesson.student_id == current_user.id,
            Lesson.status == "scheduled"
        )
    )
    lesson = result.scalar_one_or_none()

    if not lesson:
        raise HTTPException(status_code=404, detail="Scheduled lesson not found")

    # Check cancellation policy (24 hours notice)
    if (lesson.scheduled_start - datetime.utcnow()).total_seconds() < 86400:
        # Less than 24 hours notice
        if current_user.subscription_status == "trial":
            # Don't refund trial lesson
            pass
        else:
            # Apply cancellation policy for paid users
            pass

    lesson.status = "canceled"
    lesson.canceled_at = datetime.utcnow()
    lesson.cancellation_reason = reason

    # Refund trial lesson if applicable
    if current_user.subscription_status == "trial":
        if (lesson.scheduled_start - datetime.utcnow()).total_seconds() >= 86400:
            current_user.trial_lessons_remaining += 1

    await db.commit()

    return {"message": "Lesson canceled successfully"}


@router.post("/{lesson_id}/rate")
async def rate_lesson(
    lesson_id: str,
    rating_data: dict,
    current_user: Student = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Rate a completed lesson."""
    result = await db.execute(
        select(Lesson).where(
            Lesson.id == uuid.UUID(lesson_id),
            Lesson.student_id == current_user.id,
            Lesson.status == "completed"
        )
    )
    lesson = result.scalar_one_or_none()

    if not lesson:
        raise HTTPException(status_code=404, detail="Completed lesson not found")

    lesson.student_rating = rating_data["rating"]
    lesson.student_feedback = rating_data.get("feedback")

    await db.commit()

    return {"message": "Thank you for your feedback!"}