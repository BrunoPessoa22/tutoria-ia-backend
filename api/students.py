from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional, List
from datetime import datetime, timedelta
from models.student import Student
from models.lesson import Lesson
from models.progress import Progress
from api.auth import get_current_user
from utils.database import get_db
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/dashboard")
async def get_dashboard(
    current_user: Student = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get student dashboard data."""
    # Get upcoming lessons
    upcoming_lessons = await db.execute(
        select(Lesson)
        .where(
            Lesson.student_id == current_user.id,
            Lesson.scheduled_start > datetime.utcnow(),
            Lesson.status.in_(["scheduled"])
        )
        .order_by(Lesson.scheduled_start)
        .limit(5)
    )
    upcoming = upcoming_lessons.scalars().all()

    # Get recent progress
    recent_progress = await db.execute(
        select(Progress)
        .where(Progress.student_id == current_user.id)
        .order_by(Progress.assessment_date.desc())
        .limit(1)
    )
    progress = recent_progress.scalar_one_or_none()

    # Calculate study streak
    today = datetime.utcnow().date()
    streak = current_user.current_streak_days

    return {
        "student": {
            "name": current_user.full_name,
            "level": current_user.english_level,
            "subscription_status": current_user.subscription_status,
            "trial_lessons_remaining": current_user.trial_lessons_remaining
        },
        "stats": {
            "total_lessons": current_user.total_lessons_completed,
            "total_minutes": current_user.total_minutes_studied,
            "current_streak": streak,
            "longest_streak": current_user.longest_streak_days
        },
        "upcoming_lessons": [
            {
                "id": str(lesson.id),
                "scheduled_start": lesson.scheduled_start.isoformat(),
                "topic": lesson.topic,
                "duration_minutes": lesson.duration_minutes
            }
            for lesson in upcoming
        ],
        "recent_progress": {
            "overall_level": progress.overall_level if progress else None,
            "cefr_level": progress.cefr_level if progress else None,
            "last_assessment": progress.assessment_date.isoformat() if progress else None
        }
    }


@router.get("/learning-history")
async def get_learning_history(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: Student = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get student's learning history."""
    offset = (page - 1) * limit

    # Get completed lessons
    result = await db.execute(
        select(Lesson)
        .where(
            Lesson.student_id == current_user.id,
            Lesson.status == "completed"
        )
        .order_by(Lesson.scheduled_start.desc())
        .offset(offset)
        .limit(limit)
    )
    lessons = result.scalars().all()

    # Get total count
    count_result = await db.execute(
        select(func.count())
        .select_from(Lesson)
        .where(
            Lesson.student_id == current_user.id,
            Lesson.status == "completed"
        )
    )
    total = count_result.scalar()

    return {
        "lessons": [
            {
                "id": str(lesson.id),
                "date": lesson.scheduled_start.isoformat(),
                "topic": lesson.topic,
                "duration_minutes": lesson.duration_minutes,
                "performance_score": lesson.overall_performance_score,
                "student_rating": lesson.student_rating
            }
            for lesson in lessons
        ],
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total,
            "pages": (total + limit - 1) // limit
        }
    }


@router.get("/achievements")
async def get_achievements(
    current_user: Student = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get student achievements and badges."""
    achievements = []

    # Check various achievements
    if current_user.total_lessons_completed >= 10:
        achievements.append({
            "id": "10_lessons",
            "name": "Getting Started",
            "description": "Complete 10 lessons",
            "icon": "🎯",
            "earned_at": datetime.utcnow().isoformat()
        })

    if current_user.total_lessons_completed >= 50:
        achievements.append({
            "id": "50_lessons",
            "name": "Dedicated Learner",
            "description": "Complete 50 lessons",
            "icon": "⭐",
            "earned_at": datetime.utcnow().isoformat()
        })

    if current_user.current_streak_days >= 7:
        achievements.append({
            "id": "7_day_streak",
            "name": "Week Warrior",
            "description": "7-day learning streak",
            "icon": "🔥",
            "earned_at": datetime.utcnow().isoformat()
        })

    if current_user.total_minutes_studied >= 600:
        achievements.append({
            "id": "10_hours",
            "name": "Time Investor",
            "description": "Study for 10 hours",
            "icon": "⏰",
            "earned_at": datetime.utcnow().isoformat()
        })

    return {"achievements": achievements}


@router.get("/study-stats")
async def get_study_stats(
    period: str = Query("month", regex="^(week|month|year|all)$"),
    current_user: Student = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get detailed study statistics."""
    # Calculate date range
    end_date = datetime.utcnow()
    if period == "week":
        start_date = end_date - timedelta(days=7)
    elif period == "month":
        start_date = end_date - timedelta(days=30)
    elif period == "year":
        start_date = end_date - timedelta(days=365)
    else:  # all
        start_date = current_user.created_at

    # Get lessons in period
    result = await db.execute(
        select(Lesson)
        .where(
            Lesson.student_id == current_user.id,
            Lesson.status == "completed",
            Lesson.scheduled_start >= start_date,
            Lesson.scheduled_start <= end_date
        )
    )
    lessons = result.scalars().all()

    # Calculate statistics
    total_lessons = len(lessons)
    total_minutes = sum(lesson.duration_minutes or 0 for lesson in lessons)
    avg_performance = (
        sum(lesson.overall_performance_score or 0 for lesson in lessons) / total_lessons
        if total_lessons > 0 else 0
    )

    # Group by day for chart data
    daily_stats = {}
    for lesson in lessons:
        day = lesson.scheduled_start.date().isoformat()
        if day not in daily_stats:
            daily_stats[day] = {"lessons": 0, "minutes": 0}
        daily_stats[day]["lessons"] += 1
        daily_stats[day]["minutes"] += lesson.duration_minutes or 0

    return {
        "period": period,
        "total_lessons": total_lessons,
        "total_minutes": total_minutes,
        "average_performance": round(avg_performance, 1),
        "daily_stats": daily_stats
    }


@router.post("/preferences")
async def update_preferences(
    preferences: dict,
    current_user: Student = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update learning preferences."""
    try:
        # Update preferences
        if "preferred_lesson_times" in preferences:
            current_user.preferred_lesson_times = preferences["preferred_lesson_times"]
        if "learning_style" in preferences:
            current_user.learning_style = preferences["learning_style"]
        if "interests" in preferences:
            current_user.interests = preferences["interests"]
        if "custom_curriculum_preferences" in preferences:
            current_user.custom_curriculum_preferences = preferences["custom_curriculum_preferences"]

        await db.commit()
        return {"message": "Preferences updated successfully"}

    except Exception as e:
        logger.error(f"Error updating preferences: {e}")
        raise HTTPException(status_code=400, detail=str(e))