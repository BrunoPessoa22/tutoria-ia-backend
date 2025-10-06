from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
import httpx
import logging
from utils.database import get_db
from models.student import Student
from config import settings
import json

router = APIRouter()
security = HTTPBearer()
logger = logging.getLogger(__name__)


async def verify_clerk_token(token: str) -> dict:
    """Verify token with Clerk."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://api.clerk.com/v1/sessions/verify",
            headers={
                "Authorization": f"Bearer {settings.CLERK_SECRET_KEY}",
                "Content-Type": "application/json"
            },
            params={"token": token}
        )

        if response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token"
            )

        return response.json()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> Student:
    """Get current authenticated user."""
    token = credentials.credentials

    # Verify token with Clerk
    clerk_data = await verify_clerk_token(token)
    user_id = clerk_data.get("user_id")

    # Get or create student record
    result = await db.execute(
        select(Student).where(Student.clerk_user_id == user_id)
    )
    student = result.scalar_one_or_none()

    if not student:
        # Create new student record
        student = Student(
            clerk_user_id=user_id,
            email=clerk_data.get("email"),
            full_name=clerk_data.get("name", "Student")
        )
        db.add(student)
        await db.commit()
        await db.refresh(student)

    return student


@router.post("/register")
async def register(
    user_data: dict,
    db: AsyncSession = Depends(get_db)
):
    """Register a new user after Clerk signup."""
    try:
        # Create student record
        student = Student(
            clerk_user_id=user_data["clerk_user_id"],
            email=user_data["email"],
            full_name=user_data["full_name"],
            phone_number=user_data.get("phone_number"),
            whatsapp_number=user_data.get("whatsapp_number"),
            age=user_data.get("age"),
            native_language=user_data.get("native_language", "Portuguese"),
            timezone=user_data.get("timezone", "America/Sao_Paulo")
        )

        db.add(student)
        await db.commit()
        await db.refresh(student)

        return {
            "message": "User registered successfully",
            "student_id": str(student.id),
            "needs_placement_test": True
        }

    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/me")
async def get_me(
    current_user: Student = Depends(get_current_user)
):
    """Get current user profile."""
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "full_name": current_user.full_name,
        "english_level": current_user.english_level,
        "subscription_status": current_user.subscription_status,
        "trial_lessons_remaining": current_user.trial_lessons_remaining,
        "total_lessons_completed": current_user.total_lessons_completed,
        "placement_test_completed": current_user.placement_test_completed
    }


@router.put("/profile")
async def update_profile(
    profile_data: dict,
    current_user: Student = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update user profile."""
    try:
        # Update allowed fields
        allowed_fields = [
            "full_name", "phone_number", "whatsapp_number",
            "age", "learning_goals", "preferred_lesson_times",
            "timezone", "learning_style", "interests"
        ]

        for field in allowed_fields:
            if field in profile_data:
                setattr(current_user, field, profile_data[field])

        await db.commit()
        await db.refresh(current_user)

        return {"message": "Profile updated successfully"}

    except Exception as e:
        logger.error(f"Profile update error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )