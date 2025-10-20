from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from datetime import datetime, date

from database import get_db, User, UserProgress, Conversation, LearningStreak, Achievement
from auth import get_current_user

router = APIRouter(prefix="/api/progress", tags=["Progress"])


@router.get("/")
async def get_user_progress(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get current user's progress."""
    # Find or create user
    result = await db.execute(
        select(User).where(User.clerk_id == current_user["user_id"])
    )
    user = result.scalar_one_or_none()

    if not user:
        # Create new user
        user = User(
            clerk_id=current_user["user_id"],
            email=current_user["email"],
            name=current_user.get("name", "")
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

    # Get or create progress
    result = await db.execute(
        select(UserProgress).where(UserProgress.user_id == user.id)
    )
    progress = result.scalar_one_or_none()

    if not progress:
        progress = UserProgress(user_id=user.id)
        db.add(progress)
        await db.commit()
        await db.refresh(progress)

    # Get streak
    result = await db.execute(
        select(LearningStreak).where(LearningStreak.user_id == user.id)
    )
    streak = result.scalar_one_or_none()

    return {
        "current_level": progress.current_level,
        "current_module": progress.current_module,
        "current_lesson": progress.current_lesson,
        "completed_lessons": progress.completed_lessons or [],
        "total_lessons_completed": progress.total_lessons_completed,
        "current_streak": streak.current_streak if streak else 0,
        "longest_streak": streak.longest_streak if streak else 0,
        "updated_at": progress.updated_at.isoformat() if progress.updated_at else None
    }


@router.post("/save")
async def save_progress(
    level: int = Body(...),
    module: int = Body(...),
    lesson: int = Body(...),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Save user's current position in curriculum."""
    # Get user
    result = await db.execute(
        select(User).where(User.clerk_id == current_user["user_id"])
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Update progress
    result = await db.execute(
        select(UserProgress).where(UserProgress.user_id == user.id)
    )
    progress = result.scalar_one_or_none()

    if progress:
        progress.current_level = level
        progress.current_module = module
        progress.current_lesson = lesson
        progress.updated_at = datetime.utcnow()
    else:
        progress = UserProgress(
            user_id=user.id,
            current_level=level,
            current_module=module,
            current_lesson=lesson
        )
        db.add(progress)

    await db.commit()

    return {"message": "Progress saved successfully"}
