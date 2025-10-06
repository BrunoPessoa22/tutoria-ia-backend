from sqlalchemy import Column, String, Integer, Float, DateTime, Boolean, JSON, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from utils.database import Base
from datetime import datetime
import uuid


class Progress(Base):
    __tablename__ = "progress"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id"), nullable=False)

    # Progress tracking
    assessment_date = Column(DateTime, default=datetime.utcnow, index=True)
    assessment_type = Column(String(50))  # weekly, monthly, milestone, placement

    # Skill levels (0-100)
    speaking_level = Column(Float)
    listening_level = Column(Float)
    reading_level = Column(Float)
    writing_level = Column(Float)
    grammar_level = Column(Float)
    vocabulary_level = Column(Float)
    pronunciation_level = Column(Float)
    fluency_level = Column(Float)
    overall_level = Column(Float)

    # CEFR mapping
    cefr_level = Column(String(10))  # A1, A2, B1, B2, C1, C2
    cefr_sublevel = Column(String(20))  # A1.1, A1.2, etc.

    # Detailed metrics
    vocabulary_size = Column(Integer)  # Estimated number of words known
    grammar_points_mastered = Column(JSON)  # List of mastered grammar topics
    common_errors = Column(JSON)  # Recurring mistakes
    improvement_areas = Column(JSON)  # Suggested focus areas

    # Goals and achievements
    goals_set = Column(JSON)
    goals_achieved = Column(JSON)
    badges_earned = Column(JSON)
    milestones_reached = Column(JSON)

    # AI Analysis
    ai_assessment = Column(Text)  # Detailed AI-generated progress report
    strengths_analysis = Column(Text)
    weaknesses_analysis = Column(Text)
    personalized_recommendations = Column(JSON)
    predicted_next_level_date = Column(DateTime)

    # Comparison metrics
    peer_percentile = Column(Float)  # Compared to other students at same level
    improvement_rate = Column(Float)  # Rate of progress
    consistency_score = Column(Float)  # How consistent the student is

    # Study patterns
    most_productive_time = Column(String(50))
    average_session_duration = Column(Integer)
    preferred_content_type = Column(String(50))
    learning_velocity = Column(Float)  # How quickly student learns new concepts

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    student = relationship("Student", back_populates="progress_records")