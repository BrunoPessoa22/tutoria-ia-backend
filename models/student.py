from sqlalchemy import Column, String, Integer, Float, DateTime, Boolean, JSON, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from utils.database import Base
from datetime import datetime
import uuid


class Student(Base):
    __tablename__ = "students"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    clerk_user_id = Column(String(255), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    full_name = Column(String(255), nullable=False)
    phone_number = Column(String(50))
    whatsapp_number = Column(String(50))

    # Profile information
    age = Column(Integer)
    native_language = Column(String(50), default="Portuguese")
    english_level = Column(String(20))  # A1, A2, B1, B2, C1, C2
    learning_goals = Column(Text)
    preferred_lesson_times = Column(JSON)  # Array of preferred time slots
    timezone = Column(String(50), default="America/Sao_Paulo")

    # Subscription information
    subscription_status = Column(String(50), default="trial")  # trial, active, paused, canceled
    subscription_plan = Column(String(50))  # basic, standard, premium
    stripe_customer_id = Column(String(255))
    trial_lessons_remaining = Column(Integer, default=2)

    # Progress tracking
    total_lessons_completed = Column(Integer, default=0)
    total_minutes_studied = Column(Integer, default=0)
    current_streak_days = Column(Integer, default=0)
    longest_streak_days = Column(Integer, default=0)
    last_active_date = Column(DateTime)
    placement_test_score = Column(Float)
    placement_test_completed = Column(Boolean, default=False)

    # AI personalization
    learning_style = Column(String(50))  # visual, auditory, reading, kinesthetic
    interests = Column(JSON)  # Array of topics the student is interested in
    weak_areas = Column(JSON)  # Grammar, vocabulary, pronunciation, etc.
    strong_areas = Column(JSON)
    custom_curriculum_preferences = Column(JSON)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    # Relationships
    lessons = relationship("Lesson", back_populates="student", cascade="all, delete-orphan")
    interactions = relationship("Interaction", back_populates="student", cascade="all, delete-orphan")
    progress_records = relationship("Progress", back_populates="student", cascade="all, delete-orphan")