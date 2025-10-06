import os
from typing import Optional
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str
    DATABASE_URL_POOLED: Optional[str] = None

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # AI Services
    ANTHROPIC_API_KEY: str
    OPENAI_API_KEY: str
    ELEVENLABS_API_KEY: Optional[str] = None
    HEYGEN_API_KEY: Optional[str] = None
    PERPLEXITY_API_KEY: Optional[str] = None

    # Authentication
    CLERK_SECRET_KEY: str
    CLERK_WEBHOOK_SECRET: Optional[str] = None
    JWT_SECRET_KEY: str = "your-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24

    # Payments
    STRIPE_SECRET_KEY: Optional[str] = None
    STRIPE_WEBHOOK_SECRET: Optional[str] = None

    # Notifications
    RESEND_API_KEY: Optional[str] = None
    TWILIO_ACCOUNT_SID: Optional[str] = None
    TWILIO_AUTH_TOKEN: Optional[str] = None
    TWILIO_WHATSAPP_NUMBER: Optional[str] = None

    # Monitoring
    SENTRY_DSN: Optional[str] = None
    POSTHOG_API_KEY: Optional[str] = None
    LOGTAIL_TOKEN: Optional[str] = None

    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    ALLOWED_ORIGINS: str = "http://localhost:3000"
    FRONTEND_URL: Optional[str] = "http://localhost:3001"
    API_VERSION: str = "v1"

    # AI Configuration
    CLAUDE_MODEL: str = "claude-3-opus-20240229"
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    MAX_TOKENS: int = 4096
    TEMPERATURE: float = 0.7

    # Application Settings
    MAX_LESSON_DURATION_MINUTES: int = 60
    MIN_LESSON_DURATION_MINUTES: int = 15
    ADVANCE_SCHEDULING_DAYS: int = 30
    PLACEMENT_TEST_QUESTIONS: int = 20

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()