from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, Dict, Any, List
import json
import uuid
from datetime import datetime
from models.student import Student
from models.lesson import Lesson
from models.interaction import Interaction
from api.auth import get_current_user
from services.claude_tutor import ClaudeTutor
from services.voice import ElevenLabsVoiceService
from utils.database import get_db
import logging
import asyncio

router = APIRouter()
logger = logging.getLogger(__name__)
claude_tutor = ClaudeTutor()
voice_service = ElevenLabsVoiceService()


class ConnectionManager:
    """Manage WebSocket connections for live tutoring."""

    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.lesson_sessions: Dict[str, Dict[str, Any]] = {}

    async def connect(self, websocket: WebSocket, lesson_id: str):
        await websocket.accept()
        self.active_connections[lesson_id] = websocket
        self.lesson_sessions[lesson_id] = {
            "conversation_history": [],
            "session_id": str(uuid.uuid4()),
            "start_time": datetime.utcnow()
        }

    def disconnect(self, lesson_id: str):
        if lesson_id in self.active_connections:
            del self.active_connections[lesson_id]
        if lesson_id in self.lesson_sessions:
            del self.lesson_sessions[lesson_id]

    async def send_message(self, lesson_id: str, message: dict):
        if lesson_id in self.active_connections:
            await self.active_connections[lesson_id].send_json(message)

    def get_session(self, lesson_id: str) -> Optional[Dict[str, Any]]:
        return self.lesson_sessions.get(lesson_id)


manager = ConnectionManager()


@router.websocket("/live/{lesson_id}")
async def live_tutoring_session(
    websocket: WebSocket,
    lesson_id: str,
    db: AsyncSession = Depends(get_db)
):
    """WebSocket endpoint for live tutoring."""
    await manager.connect(websocket, lesson_id)

    try:
        # Get lesson and student
        result = await db.execute(
            select(Lesson).where(Lesson.id == uuid.UUID(lesson_id))
        )
        lesson = result.scalar_one_or_none()

        if not lesson:
            await websocket.send_json({"error": "Lesson not found"})
            await websocket.close()
            return

        # Get student profile
        student_result = await db.execute(
            select(Student).where(Student.id == lesson.student_id)
        )
        student = student_result.scalar_one_or_none()

        # Send initial greeting
        await manager.send_message(lesson_id, {
            "type": "system",
            "message": f"Welcome to your lesson, {student.full_name}! Today we'll be working on {lesson.topic}."
        })

        # Main message loop
        while True:
            # Receive message from student
            data = await websocket.receive_json()

            if data["type"] == "end_session":
                break

            if data["type"] == "message":
                await handle_student_message(
                    lesson_id, lesson, student, data["content"], db
                )
            elif data["type"] == "voice":
                await handle_voice_message(
                    lesson_id, lesson, student, data["audio"], db
                )

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for lesson {lesson_id}")
    except Exception as e:
        logger.error(f"Error in live session: {e}")
        await manager.send_message(lesson_id, {
            "type": "error",
            "message": "An error occurred. Please try reconnecting."
        })
    finally:
        manager.disconnect(lesson_id)


async def handle_student_message(
    lesson_id: str,
    lesson: Lesson,
    student: Student,
    message: str,
    db: AsyncSession
):
    """Handle text message from student."""
    session = manager.get_session(lesson_id)
    if not session:
        return

    try:
        # Add to conversation history
        session["conversation_history"].append({
            "role": "user",
            "content": message,
            "timestamp": datetime.utcnow().isoformat()
        })

        # Get AI response
        student_profile = {
            "full_name": student.full_name,
            "english_level": student.english_level,
            "learning_style": student.learning_style,
            "weak_areas": student.weak_areas or [],
            "interests": student.interests or []
        }

        response_data = await claude_tutor.conduct_lesson(
            student_profile=student_profile,
            lesson_plan=lesson.lesson_plan or {},
            conversation_history=session["conversation_history"],
            user_message=message
        )

        ai_response = response_data["response"]
        analysis = response_data["analysis"]

        # Send AI response
        await manager.send_message(lesson_id, {
            "type": "ai_message",
            "content": ai_response,
            "analysis": analysis
        })

        # Add to conversation history
        session["conversation_history"].append({
            "role": "ai",
            "content": ai_response,
            "timestamp": datetime.utcnow().isoformat()
        })

        # Save interaction to database
        interaction = Interaction(
            student_id=student.id,
            lesson_id=lesson.id,
            interaction_type="conversation",
            session_id=uuid.UUID(session["session_id"]),
            student_message=message,
            ai_response=ai_response,
            detected_errors=analysis.get("corrections_made"),
            topic_keywords=analysis.get("keywords", [])
        )
        db.add(interaction)
        await db.commit()

        # Generate voice response if enabled
        if student.preferred_lesson_times and "voice_enabled" in student.preferred_lesson_times:
            asyncio.create_task(send_voice_response(lesson_id, ai_response))

    except Exception as e:
        logger.error(f"Error handling message: {e}")
        await manager.send_message(lesson_id, {
            "type": "error",
            "message": "Failed to process message. Please try again."
        })


async def send_voice_response(lesson_id: str, text: str):
    """Send voice response for AI message."""
    try:
        # Generate voice
        audio_data = await voice_service.text_to_speech(text)

        # Send audio to client
        await manager.send_message(lesson_id, {
            "type": "ai_voice",
            "audio": audio_data.hex()  # Convert bytes to hex string
        })
    except Exception as e:
        logger.error(f"Error generating voice: {e}")


async def handle_voice_message(
    lesson_id: str,
    lesson: Lesson,
    student: Student,
    audio_data: str,
    db: AsyncSession
):
    """Handle voice message from student."""
    # This would integrate with speech-to-text service
    # For now, we'll send a placeholder response
    await manager.send_message(lesson_id, {
        "type": "system",
        "message": "Voice message received. Processing..."
    })


@router.post("/practice/conversation")
async def practice_conversation(
    practice_data: dict,
    current_user: Student = Depends(get_current_user)
):
    """Start a practice conversation on a topic."""
    topic = practice_data["topic"]
    difficulty = practice_data.get("difficulty", current_user.english_level)

    # Generate conversation starter
    prompt = f"""Create a conversation starter for English practice.
Topic: {topic}
Student Level: {difficulty}
Format: A realistic scenario or question to start practicing."""

    response = await claude_tutor.client.messages.create(
        model=claude_tutor.model,
        max_tokens=512,
        temperature=0.8,
        messages=[{"role": "user", "content": prompt}]
    )

    return {
        "topic": topic,
        "starter": response.content[0].text,
        "suggested_vocabulary": ["example", "words"],  # Would be generated
        "grammar_focus": ["present perfect", "conditionals"]  # Would be generated
    }


@router.post("/practice/grammar")
async def practice_grammar(
    practice_data: dict,
    current_user: Student = Depends(get_current_user)
):
    """Generate grammar practice exercises."""
    grammar_point = practice_data["grammar_point"]
    num_exercises = practice_data.get("num_exercises", 5)

    exercises = []
    for i in range(num_exercises):
        # Generate exercise
        prompt = f"""Create a grammar exercise for: {grammar_point}
Student Level: {current_user.english_level}
Exercise type: varied (fill-in-blank, correction, transformation)
Include the answer."""

        response = await claude_tutor.client.messages.create(
            model=claude_tutor.model,
            max_tokens=256,
            temperature=0.7,
            messages=[{"role": "user", "content": prompt}]
        )

        # Parse exercise (simplified)
        exercises.append({
            "type": "fill_blank",
            "question": "Example question",
            "answer": "correct answer",
            "explanation": "Why this is correct"
        })

    return {
        "grammar_point": grammar_point,
        "exercises": exercises
    }


@router.post("/assess")
async def assess_response(
    assessment_data: dict,
    current_user: Student = Depends(get_current_user)
):
    """Assess a student's response."""
    response = await claude_tutor.assess_student_response(
        student_message=assessment_data["response"],
        expected_response=assessment_data.get("expected"),
        assessment_criteria=assessment_data.get("criteria")
    )

    return response


@router.get("/feedback/{lesson_id}")
async def get_lesson_feedback(
    lesson_id: str,
    current_user: Student = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get detailed feedback for a completed lesson."""
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

    # Get all interactions from the lesson
    interactions_result = await db.execute(
        select(Interaction).where(
            Interaction.lesson_id == lesson.id
        ).order_by(Interaction.timestamp)
    )
    interactions = interactions_result.scalars().all()

    # Analyze interactions for detailed feedback
    total_errors = 0
    error_types = {}
    topics_covered = set()

    for interaction in interactions:
        if interaction.detected_errors:
            total_errors += len(interaction.detected_errors)
            for error in interaction.detected_errors:
                error_type = error.get("type", "other")
                error_types[error_type] = error_types.get(error_type, 0) + 1

        if interaction.topic_keywords:
            topics_covered.update(interaction.topic_keywords)

    return {
        "lesson_id": lesson_id,
        "overall_score": lesson.overall_performance_score,
        "ai_feedback": lesson.ai_feedback,
        "metrics": {
            "engagement": lesson.student_engagement_score,
            "speaking_time": lesson.speaking_time_percentage,
            "pronunciation": lesson.pronunciation_score,
            "grammar_accuracy": lesson.grammar_accuracy_score,
            "vocabulary_usage": lesson.vocabulary_usage_score
        },
        "analysis": {
            "total_interactions": len(interactions),
            "total_errors": total_errors,
            "error_breakdown": error_types,
            "topics_covered": list(topics_covered)
        },
        "recommendations": [
            "Focus on present perfect tense",
            "Practice pronunciation of 'th' sounds",
            "Expand vocabulary related to business"
        ]  # Would be generated based on analysis
    }