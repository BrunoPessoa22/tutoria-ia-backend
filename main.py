from fastapi import FastAPI, Body, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import os
import json
import asyncio
import websockets
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
    # Add natural pauses for better teaching rhythm
    text_with_pauses = text.replace('. ', '.<break time="600ms"/> ')
    text_with_pauses = text_with_pauses.replace('? ', '?<break time="800ms"/> ')
    text_with_pauses = text_with_pauses.replace('! ', '!<break time="600ms"/> ')

    data = {
        "text": text_with_pauses[:1200],  # Increased limit for pauses
        "model_id": "eleven_turbo_v2_5",  # Much faster generation
        "voice_settings": {
            "stability": 0.65,  # Slightly more stable for teaching
            "similarity_boost": 0.8,  # More natural
            "style": 0.35,  # Add expressiveness
            "use_speaker_boost": True,  # Better clarity
            "speaking_rate": 0.85  # Slow down 15% for natural pacing
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
    student_level: Optional[str] = Body("0", embed=True),
    lesson_number: Optional[int] = Body(1, embed=True)
):
    """Chat with Professor Caio - Conversational AI tutor with personality."""
    from anthropic import Anthropic

    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    if not anthropic_key:
        return {"error": "Anthropic API key not configured"}

    client = Anthropic(api_key=anthropic_key)

    # Get curriculum for this level
    from curriculum import get_level
    level_data = get_level(int(student_level))

    if not level_data:
        level_data = get_level(0)  # Default to level 0

    # Build lesson context
    level_name = level_data.get('name', 'Fundamentos de IA')
    modules = level_data.get('modules', [])
    learning_objectives = level_data.get('learning_objectives', [])

    # Get specific lesson content
    all_lessons = []
    for module in modules:
        for lesson in module.get('lessons', []):
            all_lessons.append({
                'module': module['title'],
                'lesson': lesson
            })

    current_lesson_index = min(lesson_number - 1, len(all_lessons) - 1)
    current_lesson = all_lessons[current_lesson_index] if all_lessons else {'module': 'Introdução', 'lesson': 'Fundamentos de IA'}

    # Professor Caio's personality and teaching style with STRUCTURED LESSON PLAN
    system_prompt = """Você é o Professor Caio, um professor brasileiro de IA que ENSINA CONTEÚDO ESTRUTURADO.

SEU PAPEL:
Você NÃO é um chatbot conversacional genérico. Você é um PROFESSOR com um PLANO DE AULA específico.

CONTEÚDO ATUAL DA AULA:
Nível: {level_name}
Módulo: {module_name}
Lição {lesson_num}: {lesson_name}

Objetivos de aprendizagem deste nível:
{objectives}

INSTRUÇÕES IMPORTANTES:
1. SEMPRE comece explicando o tópico da lição atual
2. NÃO pergunte "o que você já sabe" - ENSINE o conteúdo
3. Use exemplos brasileiros concretos (Magazine Luiza, Nubank, iFood)
4. Depois de explicar, faça UMA pergunta para verificar compreensão
5. Se o aluno responder, dê feedback E continue ensinando o próximo ponto
6. Mantenha foco no CONTEÚDO da lição, não em conversa genérica

FORMATO DA PRIMEIRA MENSAGEM:
"Oi! Vamos começar nossa aula sobre [TÓPICO]. Hoje você vai aprender [OBJETIVO].

[EXPLICAÇÃO DO CONCEITO com exemplo brasileiro]

[PERGUNTA para verificar entendimento]"

IMPORTANTE: Seja direto e didático. O aluno já fez o teste de nivelamento. Vá direto ao conteúdo da aula.

Mantenha explicações em 3-5 frases. Após explicar um ponto, pergunte algo específico sobre o que acabou de ensinar.""".format(
        level_name=level_name,
        module_name=current_lesson['module'],
        lesson_num=lesson_number,
        lesson_name=current_lesson['lesson'],
        objectives="\n".join(f"- {obj}" for obj in learning_objectives[:3])
    )

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

# WebSocket endpoint for real-time conversation
@app.websocket("/ws/conversation")
async def websocket_conversation(websocket: WebSocket):
    """Real-time conversational tutoring with streaming audio."""
    await websocket.accept()

    elevenlabs_key = os.getenv("ELEVENLABS_API_KEY")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")

    if not elevenlabs_key or not anthropic_key:
        await websocket.send_json({"error": "API keys not configured"})
        await websocket.close()
        return

    try:
        while True:
            # Receive message from frontend
            data = await websocket.receive_json()

            message_type = data.get("type")

            if message_type == "chat":
                # Get student message and context
                message = data.get("message", "")
                conversation_history = data.get("conversation_history", [])
                student_level = data.get("student_level", "0")
                lesson_number = data.get("lesson_number", 1)
                voice_id = data.get("voice_id", "J7NSF1cIlVrVyE8KOute")

                # 1. Generate AI response with Claude
                from anthropic import Anthropic
                client = Anthropic(api_key=anthropic_key)

                # Get curriculum context (same as existing chat endpoint)
                from curriculum import get_level
                level_data = get_level(int(student_level))
                if not level_data:
                    level_data = get_level(0)

                level_name = level_data.get('name', 'Fundamentos de IA')
                modules = level_data.get('modules', [])
                learning_objectives = level_data.get('learning_objectives', [])

                all_lessons = []
                for module in modules:
                    for lesson in module.get('lessons', []):
                        all_lessons.append({
                            'module': module['title'],
                            'lesson': lesson
                        })

                current_lesson_index = min(lesson_number - 1, len(all_lessons) - 1)
                current_lesson = all_lessons[current_lesson_index] if all_lessons else {
                    'module': 'Introdução',
                    'lesson': 'Fundamentos de IA'
                }

                system_prompt = """Você é o Professor Caio, um professor brasileiro de IA que ENSINA CONTEÚDO ESTRUTURADO.

SEU PAPEL:
Você NÃO é um chatbot conversacional genérico. Você é um PROFESSOR com um PLANO DE AULA específico.

CONTEÚDO ATUAL DA AULA:
Nível: {level_name}
Módulo: {module_name}
Lição {lesson_num}: {lesson_name}

Objetivos de aprendizagem deste nível:
{objectives}

INSTRUÇÕES IMPORTANTES:
1. SEMPRE comece explicando o tópico da lição atual
2. NÃO pergunte "o que você já sabe" - ENSINE o conteúdo
3. Use exemplos brasileiros concretos (Magazine Luiza, Nubank, iFood)
4. Depois de explicar, faça UMA pergunta para verificar compreensão
5. Se o aluno responder, dê feedback E continue ensinando o próximo ponto
6. Mantenha foco no CONTEÚDO da lição, não em conversa genérica

FORMATO DA PRIMEIRA MENSAGEM:
"Oi! Vamos começar nossa aula sobre [TÓPICO]. Hoje você vai aprender [OBJETIVO].

[EXPLICAÇÃO DO CONCEITO com exemplo brasileiro]

[PERGUNTA para verificar entendimento]"

IMPORTANTE: Seja direto e didático. O aluno já fez o teste de nivelamento. Vá direto ao conteúdo da aula.

Mantenha explicações em 3-5 frases. Após explicar um ponto, pergunte algo específico sobre o que acabou de ensinar.""".format(
                    level_name=level_name,
                    module_name=current_lesson['module'],
                    lesson_num=lesson_number,
                    lesson_name=current_lesson['lesson'],
                    objectives="\n".join(f"- {obj}" for obj in learning_objectives[:3])
                )

                # Build messages
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

                # Generate response
                response = client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=500,
                    system=system_prompt,
                    messages=messages
                )

                assistant_text = response.content[0].text

                # Send transcript to frontend
                await websocket.send_json({
                    "type": "transcript",
                    "text": assistant_text
                })

                # 2. Stream audio from ElevenLabs WebSocket
                elevenlabs_url = f"wss://api.elevenlabs.io/v1/text-to-speech/{voice_id}/stream-input?model_id=eleven_flash_v2_5"

                async with websockets.connect(elevenlabs_url) as elevenlabs_ws:
                    # Send initial configuration
                    await elevenlabs_ws.send(json.dumps({
                        "text": " ",
                        "voice_settings": {
                            "stability": 0.65,
                            "similarity_boost": 0.8,
                            "style": 0.35,
                            "use_speaker_boost": True
                        },
                        "xi_api_key": elevenlabs_key
                    }))

                    # Add natural pauses
                    text_with_pauses = assistant_text.replace('. ', '.<break time="600ms"/> ')
                    text_with_pauses = text_with_pauses.replace('? ', '?<break time="800ms"/> ')
                    text_with_pauses = text_with_pauses.replace('! ', '!<break time="600ms"/> ')

                    # Send text to generate
                    await elevenlabs_ws.send(json.dumps({
                        "text": text_with_pauses[:1200],
                        "flush": True
                    }))

                    # Stream audio chunks to frontend
                    try:
                        while True:
                            response_data = await asyncio.wait_for(elevenlabs_ws.recv(), timeout=30.0)
                            response_json = json.loads(response_data)

                            if response_json.get("audio"):
                                # Forward audio chunk to frontend
                                await websocket.send_json({
                                    "type": "audio",
                                    "audio": response_json["audio"]
                                })

                            if response_json.get("isFinal"):
                                break

                    except asyncio.TimeoutError:
                        await websocket.send_json({"type": "error", "message": "Audio generation timeout"})

                    # Signal audio complete
                    await websocket.send_json({"type": "audio_complete"})

            elif message_type == "ping":
                # Keep-alive
                await websocket.send_json({"type": "pong"})

    except WebSocketDisconnect:
        print("Client disconnected")
    except Exception as e:
        print(f"WebSocket error: {e}")
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
        except:
            pass

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
