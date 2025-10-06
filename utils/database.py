from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import NullPool
from config import settings
import logging

logger = logging.getLogger(__name__)

# Handle database URL based on type
if settings.DATABASE_URL.startswith("sqlite"):
    # SQLite for local development
    database_url = settings.DATABASE_URL.replace("sqlite://", "sqlite+aiosqlite://")
    connect_args = {"check_same_thread": False}
else:
    # PostgreSQL for production
    database_url = settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
    connect_args = {}

# Create async engine
engine = create_async_engine(
    database_url,
    echo=settings.DEBUG,
    connect_args=connect_args if settings.DATABASE_URL.startswith("sqlite") else {},
    pool_pre_ping=True if not settings.DATABASE_URL.startswith("sqlite") else False,
)

# Create session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Base class for models
Base = declarative_base()


async def get_db():
    """Dependency for getting database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """Initialize database connection."""
    try:
        async with engine.begin() as conn:
            # Import all models to ensure they're registered
            from models import student, lesson, interaction, progress, curriculum
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


async def close_db():
    """Close database connection."""
    await engine.dispose()
    logger.info("Database connection closed")