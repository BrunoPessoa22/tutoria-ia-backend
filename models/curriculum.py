from sqlalchemy import Column, String, Integer, Float, DateTime, Boolean, JSON, Text
from sqlalchemy.dialects.postgresql import UUID
from utils.database import Base
from datetime import datetime
import uuid


class Curriculum(Base):
    __tablename__ = "curriculum"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Module information
    module_code = Column(String(50), unique=True, nullable=False, index=True)
    module_name = Column(String(255), nullable=False)
    description = Column(Text)
    level = Column(String(10), nullable=False)  # A1, A2, B1, B2, C1, C2
    sublevel = Column(Integer)  # 1, 2, 3 within each level

    # Structure
    category = Column(String(100))  # Grammar, Vocabulary, Conversation, Business, etc.
    subcategory = Column(String(100))
    estimated_hours = Column(Float)
    prerequisite_modules = Column(JSON)  # List of module codes

    # Content
    learning_objectives = Column(JSON)
    key_vocabulary = Column(JSON)
    grammar_points = Column(JSON)
    cultural_notes = Column(JSON)

    # Materials
    lesson_plans = Column(JSON)  # Structured lesson plans
    exercises = Column(JSON)  # Practice exercises
    assessments = Column(JSON)  # Tests and quizzes
    multimedia_resources = Column(JSON)  # Videos, audio, images
    external_resources = Column(JSON)  # Links to external content

    # AI Configuration
    ai_prompts = Column(JSON)  # Custom prompts for this module
    conversation_starters = Column(JSON)
    role_play_scenarios = Column(JSON)
    discussion_topics = Column(JSON)

    # Gamification
    points_value = Column(Integer, default=100)
    badges_available = Column(JSON)
    achievement_criteria = Column(JSON)

    # Customization
    adaptable_elements = Column(JSON)  # Elements that can be customized per student
    difficulty_variations = Column(JSON)  # Easy, medium, hard versions

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    version = Column(String(20), default="1.0.0")

    # Usage statistics
    times_completed = Column(Integer, default=0)
    average_completion_time = Column(Float)
    average_score = Column(Float)
    student_rating = Column(Float)