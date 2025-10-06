from sqlalchemy import Column, String, Integer, Float, DateTime, Boolean, JSON, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from utils.database import Base
from datetime import datetime
import uuid


class Lesson(Base):
    __tablename__ = "lessons"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id"), nullable=False)

    # Scheduling
    scheduled_start = Column(DateTime, nullable=False, index=True)
    scheduled_end = Column(DateTime, nullable=False)
    actual_start = Column(DateTime)
    actual_end = Column(DateTime)
    duration_minutes = Column(Integer)

    # Lesson details
    lesson_type = Column(String(50), nullable=False)  # live, self-study, placement, review
    status = Column(String(50), default="scheduled")  # scheduled, in_progress, completed, canceled, no_show
    topic = Column(String(255))
    lesson_plan = Column(JSON)  # Structured lesson plan
    curriculum_module = Column(String(255))
    difficulty_level = Column(String(20))  # A1, A2, B1, B2, C1, C2

    # Content
    materials_used = Column(JSON)  # Links to materials, exercises
    vocabulary_taught = Column(JSON)  # New words introduced
    grammar_points = Column(JSON)  # Grammar concepts covered
    homework_assigned = Column(JSON)

    # AI-generated content
    pre_lesson_summary = Column(Text)  # Avatar video script
    post_lesson_summary = Column(Text)
    follow_up_questions = Column(JSON)
    personalized_exercises = Column(JSON)

    # Performance metrics
    student_engagement_score = Column(Float)  # 0-100
    speaking_time_percentage = Column(Float)
    pronunciation_score = Column(Float)
    grammar_accuracy_score = Column(Float)
    vocabulary_usage_score = Column(Float)
    overall_performance_score = Column(Float)

    # Recording and transcription
    recording_url = Column(String(500))
    transcript = Column(Text)
    key_moments = Column(JSON)  # Timestamps of important moments

    # Feedback
    ai_feedback = Column(Text)
    student_feedback = Column(Text)
    student_rating = Column(Float)

    # Technical details
    connection_quality = Column(String(50))  # excellent, good, fair, poor
    technical_issues = Column(JSON)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    canceled_at = Column(DateTime)
    cancellation_reason = Column(String(255))

    # Relationships
    student = relationship("Student", back_populates="lessons")
    interactions = relationship("Interaction", back_populates="lesson", cascade="all, delete-orphan")