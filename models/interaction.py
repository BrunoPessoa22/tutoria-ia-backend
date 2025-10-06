from sqlalchemy import Column, String, Integer, Float, DateTime, Boolean, JSON, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from utils.database import Base
from datetime import datetime
import uuid


class Interaction(Base):
    __tablename__ = "interactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id"), nullable=False)
    lesson_id = Column(UUID(as_uuid=True), ForeignKey("lessons.id"))

    # Interaction details
    interaction_type = Column(String(50), nullable=False)  # question, answer, correction, explanation, practice
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    session_id = Column(UUID(as_uuid=True), index=True)  # Groups interactions in same session

    # Content
    student_message = Column(Text)
    ai_response = Column(Text)
    audio_url = Column(String(500))  # If voice interaction

    # Analysis
    detected_errors = Column(JSON)  # Grammar, pronunciation, vocabulary errors
    corrections_provided = Column(JSON)
    emotion_detected = Column(String(50))  # frustrated, confused, confident, happy
    topic_keywords = Column(JSON)

    # Embeddings for semantic search
    message_embedding = Column(JSON)  # Vector representation for similarity search

    # Performance metrics
    response_time_ms = Column(Integer)
    ai_confidence_score = Column(Float)
    relevance_score = Column(Float)

    # Context
    conversation_context = Column(JSON)  # Previous messages for context
    learning_objective = Column(String(255))

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    is_flagged = Column(Boolean, default=False)  # For review or inappropriate content
    flag_reason = Column(String(255))

    # Relationships
    student = relationship("Student", back_populates="interactions")
    lesson = relationship("Lesson", back_populates="interactions")