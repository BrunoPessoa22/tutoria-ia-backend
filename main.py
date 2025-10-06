from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
from config import settings
# from api import auth, students, lessons, tutoring, progress, webhooks
from utils.database import init_db, close_db


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Sentry (optional)
try:
    import sentry_sdk
    from sentry_sdk.integrations.fastapi import FastApiIntegration
    if settings.SENTRY_DSN:
        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            integrations=[FastApiIntegration(transaction_style="endpoint")],
            traces_sample_rate=0.1,
            environment=settings.ENVIRONMENT,
            profiles_sample_rate=0.1,
        )
except ImportError:
    logger.info("Sentry not installed, skipping initialization")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle."""
    # Startup
    logger.info("Starting up AI Tutor Platform API...")
    await init_db()
    yield
    # Shutdown
    logger.info("Shutting down AI Tutor Platform API...")
    await close_db()


# Create FastAPI app
app = FastAPI(
    title="AI Tutor Platform API",
    description="Backend API for AI-powered English tutoring platform",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
        "version": "1.0.0"
    }


# Include routers
from routes import voice, tutoring, proactive_tutor
app.include_router(voice.router, prefix="/api/voice", tags=["Voice"])
app.include_router(tutoring.router, prefix="/api/tutoring", tags=["Tutoring"])
app.include_router(proactive_tutor.router, prefix="/api/proactive", tags=["Proactive Tutor"])
# app.include_router(auth.router, prefix=f"/api/{settings.API_VERSION}/auth", tags=["Authentication"])
# app.include_router(students.router, prefix=f"/api/{settings.API_VERSION}/students", tags=["Students"])
# app.include_router(lessons.router, prefix=f"/api/{settings.API_VERSION}/lessons", tags=["Lessons"])
# app.include_router(tutoring.router, prefix=f"/api/{settings.API_VERSION}/tutoring", tags=["Tutoring"])
# app.include_router(progress.router, prefix=f"/api/{settings.API_VERSION}/progress", tags=["Progress"])
# app.include_router(webhooks.router, prefix=f"/api/{settings.API_VERSION}/webhooks", tags=["Webhooks"])


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected error occurred. Please try again later."}
    )


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "AI Tutor Platform API",
        "documentation": "/docs",
        "health": "/health"
    }