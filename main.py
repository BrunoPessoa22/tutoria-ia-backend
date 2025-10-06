from fastapi import FastAPI, Body
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import os
from curriculum import get_curriculum, get_level, get_placement_test

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
        "text": text[:1000],  # Increased limit for better flow
        "model_id": "eleven_turbo_v2_5",  # Much faster generation
        "voice_settings": {
            "stability": 0.6,  # Slightly more stable for teaching
            "similarity_boost": 0.8,  # More natural
            "style": 0.3,  # Add expressiveness
            "use_speaker_boost": True  # Better clarity
        }
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=data, headers=headers, timeout=30.0)

        if response.status_code == 200:
            from fastapi.responses import Response
            return Response(content=response.content, media_type="audio/mpeg")
        else:
            return {"error": f"ElevenLabs API error: {response.status_code}"}

# Claude conversational tutor endpoint
@app.post("/api/tutoring/chat")
async def chat(
    message: str = Body(..., embed=True),
    conversation_history: list = Body([], embed=True),
    student_level: Optional[str] = Body("beginner", embed=True)
):
    """Chat with Professor Caio - Conversational AI tutor with personality."""
    from anthropic import Anthropic

    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    if not anthropic_key:
        return {"error": "Anthropic API key not configured"}

    client = Anthropic(api_key=anthropic_key)

    # Professor Caio's personality and teaching style
    system_prompt = """Você é o Professor Caio, um tutor brasileiro de IA carismático e acolhedor.

PERSONALIDADE:
- Caloroso, empático e encorajador
- Usa exemplos do dia a dia brasileiro
- Faz perguntas para engajar o aluno
- Celebra pequenas vitórias
- Adapta explicações ao nível do aluno
- Usa analogias criativas e humor leve

ESTILO DE ENSINO:
- Sempre inicia conversas perguntando como o aluno está
- Conecta conceitos técnicos com situações reais
- Usa storytelling para explicar conceitos
- Faz perguntas socráticas para estimular pensamento
- Dá feedback específico e construtivo
- Mantém tom conversacional, nunca robotizado

CONTEXTO:
Você ensina através da metodologia Cultura Builder - ajudando brasileiros a construir aplicações e automações com IA em 18 meses.

Nível atual do aluno: {level}

Mantenha respostas em 2-4 frases para manter o diálogo fluido.""".format(level=student_level)

    # Build conversation with history
    messages = []
    for msg in conversation_history:
        messages.append({
            "role": msg["role"],
            "content": msg["content"]
        })

    messages.append({
        "role": "user",
        "content": message
    })

    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=500,  # Shorter for conversational flow
        system=system_prompt,
        messages=messages
    )

    return {
        "response": response.content[0].text,
        "model": "claude-3-5-sonnet-20241022"
    }

# Curriculum endpoints
@app.get("/api/curriculum")
async def get_full_curriculum():
    """Get complete 18-month curriculum structure"""
    return get_curriculum()

@app.get("/api/curriculum/level/{level_number}")
async def get_curriculum_level(level_number: int):
    """Get specific level details"""
    level = get_level(level_number)
    if not level:
        return {"error": "Level not found"}
    return level

@app.get("/api/assessment/placement-test")
async def get_assessment():
    """Get placement test structure"""
    return get_placement_test()

@app.post("/api/assessment/evaluate")
async def evaluate_placement(
    answers: dict = Body(..., embed=True)
):
    """Evaluate placement test and recommend starting level"""
    # Simple scoring logic - can be enhanced with AI
    score = 0
    total = 0

    for section, section_answers in answers.items():
        for answer in section_answers:
            total += 1
            if answer.get("correct", False):
                score += 1

    percentage = (score / total) * 100 if total > 0 else 0

    # Determine level based on score
    if percentage <= 30:
        level = 0
    elif percentage <= 45:
        level = 1
    elif percentage <= 60:
        level = 3
    elif percentage <= 75:
        level = 4
    elif percentage <= 85:
        level = 6
    else:
        level = 7

    recommended_level = get_level(level)

    return {
        "score": score,
        "total": total,
        "percentage": round(percentage, 1),
        "recommended_level": level,
        "level_details": recommended_level
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
