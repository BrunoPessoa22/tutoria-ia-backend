from fastapi import FastAPI, Body
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import os

# Create FastAPI app
app = FastAPI(
    title="AI Tutor Platform API",
    description="Backend API for AI-powered tutoring platform",
    version="1.0.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "AI Tutor Platform API - Tutoria IA",
        "status": "online",
        "documentation": "/docs",
        "health": "/health",
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    elevenlabs_key = os.getenv("ELEVENLABS_API_KEY", "")
    return {
        "status": "healthy",
        "environment": os.getenv("ENVIRONMENT", "production"),
        "version": "1.0.0",
        "anthropic_configured": bool(os.getenv("ANTHROPIC_API_KEY")),
        "elevenlabs_configured": bool(elevenlabs_key),
        "elevenlabs_key_preview": f"{elevenlabs_key[:8]}...{elevenlabs_key[-4:]}" if elevenlabs_key else "NOT_SET"
    }

# Voice generation endpoint
@app.post("/api/voice/generate")
async def generate_voice(
    text: str = Body(..., embed=True),
    voice_id: Optional[str] = Body("EXAVITQu4vr4xnSDxMaL", embed=True)
):
    """Generate voice using ElevenLabs API."""
    import httpx

    elevenlabs_key = os.getenv("ELEVENLABS_API_KEY")
    if not elevenlabs_key:
        return {"error": "ElevenLabs API key not configured"}

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {
        "xi-api-key": elevenlabs_key,
        "Content-Type": "application/json"
    }
    data = {
        "text": text[:500],  # Limit text length
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75
        }
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=data, headers=headers, timeout=30.0)

        if response.status_code == 200:
            from fastapi.responses import Response
            return Response(content=response.content, media_type="audio/mpeg")
        else:
            return {"error": f"ElevenLabs API error: {response.status_code}"}

# Claude chat endpoint
@app.post("/api/tutoring/chat")
async def chat(message: str = Body(..., embed=True)):
    """Chat with Claude AI tutor."""
    from anthropic import Anthropic

    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    if not anthropic_key:
        return {"error": "Anthropic API key not configured"}

    client = Anthropic(api_key=anthropic_key)

    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[{
            "role": "user",
            "content": message
        }]
    )

    return {
        "response": response.content[0].text,
        "model": "claude-3-5-sonnet-20241022"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
