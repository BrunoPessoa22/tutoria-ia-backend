from fastapi import FastAPI, Body, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import os
import json
import asyncio
from dotenv import load_dotenv
from curriculum import get_curriculum, get_level, get_placement_test

# Phase 3: Database and Auth
try:
    from database import init_db
    from api.progress import router as progress_router
    PHASE_3_ENABLED = True
except ImportError:
    PHASE_3_ENABLED = False
    print("Phase 3 modules not available, running without database")

# Load environment variables
load_dotenv()

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

# Phase 3: Initialize database on startup
if PHASE_3_ENABLED:
    @app.on_event("startup")
    async def startup():
        await init_db()
        print("✅ Database initialized")

    # Include Progress API routes
    app.include_router(progress_router)

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

@app.get("/api/analytics/questions")
async def get_all_questions(
    limit: int = 100,
    level: Optional[str] = None
):
    """Get all student questions for analytics."""
    import sqlite3

    conn = sqlite3.connect('tutoria_analytics.db')
    cursor = conn.cursor()

    # Create table if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS student_questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            student_level TEXT,
            lesson_number INTEGER,
            question TEXT NOT NULL,
            response TEXT NOT NULL,
            module TEXT,
            lesson_name TEXT
        )
    ''')

    if level:
        cursor.execute('''
            SELECT * FROM student_questions
            WHERE student_level = ?
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (level, limit))
    else:
        cursor.execute('''
            SELECT * FROM student_questions
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (limit,))

    rows = cursor.fetchall()
    conn.close()

    questions = []
    for row in rows:
        questions.append({
            "id": row[0],
            "timestamp": row[1],
            "student_level": row[2],
            "lesson_number": row[3],
            "question": row[4],
            "response": row[5],
            "module": row[6],
            "lesson_name": row[7]
        })

    return {"questions": questions, "total": len(questions)}

@app.get("/api/analytics/stats")
async def get_stats():
    """Get overall statistics."""
    import sqlite3

    conn = sqlite3.connect('tutoria_analytics.db')
    cursor = conn.cursor()

    # Create table if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS student_questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            student_level TEXT,
            lesson_number INTEGER,
            question TEXT NOT NULL,
            response TEXT NOT NULL,
            module TEXT,
            lesson_name TEXT
        )
    ''')

    # Total questions
    cursor.execute('SELECT COUNT(*) FROM student_questions')
    total = cursor.fetchone()[0]

    # Questions by level
    cursor.execute('''
        SELECT student_level, COUNT(*)
        FROM student_questions
        GROUP BY student_level
    ''')
    by_level = {row[0]: row[1] for row in cursor.fetchall()}

    # Most common topics (by module)
    cursor.execute('''
        SELECT module, COUNT(*) as count
        FROM student_questions
        GROUP BY module
        ORDER BY count DESC
        LIMIT 10
    ''')
    top_topics = [{"module": row[0], "count": row[1]} for row in cursor.fetchall()]

    conn.close()

    return {
        "total_questions": total,
        "by_level": by_level,
        "top_topics": top_topics
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
    system_prompt = """Você é o Professor Pedro, um tutor brasileiro de IA especializado em RESPONDER DÚVIDAS dos alunos.

SEU PAPEL:
Você é um TUTOR SOCRÁTICO, não um palestrante. Você RESPONDE às perguntas dos alunos de forma clara e didática.

CONTEXTO DO CURRÍCULO:
Nível: {level_name}
Módulo: {module_name}
Lição {lesson_num}: {lesson_name}

Objetivos de aprendizagem deste nível:
{objectives}

INSTRUÇÕES IMPORTANTES:
1. RESPONDA à pergunta do aluno de forma clara e concisa
2. Use exemplos brasileiros concretos (Magazine Luiza, Nubank, iFood, Mercado Livre)
3. Adapte a complexidade da resposta ao nível do aluno
4. Se a pergunta está fora do escopo do currículo, responda mesmo assim mas conecte ao currículo
5. Seja encorajador e motivador
6. Mantenha respostas em 3-5 frases para facilitar a compreensão
7. Termine perguntando se ficou claro ou se o aluno tem mais dúvidas

FORMATO DA PRIMEIRA MENSAGEM (quando o aluno se apresenta):
"Oi! Eu sou o Professor Pedro, seu tutor de IA. Estou aqui para responder suas dúvidas sobre {level_name}.

Pode me perguntar qualquer coisa sobre Inteligência Artificial! Como posso te ajudar hoje?"

FORMATO DAS RESPOSTAS:
[RESPOSTA CLARA E DIRETA à pergunta]

[EXEMPLO PRÁTICO brasileiro se relevante]

Ficou claro? Tem mais alguma dúvida?""".format(
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
        model="claude-sonnet-4-5-20250929",  # Using Sonnet 4.5
        max_tokens=500,
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

    anthropic_key = os.getenv("ANTHROPIC_API_KEY")

    if not anthropic_key:
        await websocket.send_json({"error": "Anthropic API key not configured"})
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

                system_prompt = """Você é o Professor Pedro, um tutor brasileiro de IA especializado em RESPONDER DÚVIDAS dos alunos.

SEU PAPEL:
Você é um TUTOR SOCRÁTICO, não um palestrante. Você RESPONDE às perguntas dos alunos de forma clara e didática.

CONTEXTO DO CURRÍCULO:
Nível: {level_name}
Módulo: {module_name}
Lição {lesson_num}: {lesson_name}

Objetivos de aprendizagem deste nível:
{objectives}

INSTRUÇÕES IMPORTANTES:
1. RESPONDA à pergunta do aluno de forma clara e concisa
2. Use exemplos brasileiros concretos (Magazine Luiza, Nubank, iFood, Mercado Livre)
3. Adapte a complexidade da resposta ao nível do aluno
4. Se a pergunta está fora do escopo do currículo, responda mesmo assim mas conecte ao currículo
5. Seja encorajador e motivador
6. Mantenha respostas em 3-5 frases para facilitar a compreensão
7. Termine perguntando se ficou claro ou se o aluno tem mais dúvidas

FORMATO DA PRIMEIRA MENSAGEM (quando o aluno se apresenta):
"Oi! Eu sou o Professor Pedro, seu tutor de IA. Estou aqui para responder suas dúvidas sobre {level_name}.

Pode me perguntar qualquer coisa sobre Inteligência Artificial! Como posso te ajudar hoje?"

FORMATO DAS RESPOSTAS:
[RESPOSTA CLARA E DIRETA à pergunta]

[EXEMPLO PRÁTICO brasileiro se relevante]

Ficou claro? Tem mais alguma dúvida?""".format(
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
                    model="claude-sonnet-4-5-20250929",  # Using Sonnet 4.5
                    max_tokens=500,
                    system=system_prompt,
                    messages=messages
                )

                # Store student question for analytics
                try:
                    from datetime import datetime
                    import sqlite3

                    conn = sqlite3.connect('tutoria_analytics.db')
                    cursor = conn.cursor()

                    # Create table if it doesn't exist
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS student_questions (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            timestamp TEXT NOT NULL,
                            student_level TEXT,
                            lesson_number INTEGER,
                            question TEXT NOT NULL,
                            response TEXT NOT NULL,
                            module TEXT,
                            lesson_name TEXT
                        )
                    ''')

                    # Insert question and response
                    cursor.execute('''
                        INSERT INTO student_questions
                        (timestamp, student_level, lesson_number, question, response, module, lesson_name)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        datetime.now().isoformat(),
                        student_level,
                        lesson_number,
                        message,
                        response.content[0].text,
                        current_lesson['module'],
                        current_lesson['lesson']
                    ))

                    conn.commit()
                    conn.close()
                except Exception as e:
                    print(f"Error storing question: {e}")

                assistant_text = response.content[0].text

                # Send transcript to frontend (HeyGen will handle TTS)
                await websocket.send_json({
                    "type": "transcript",
                    "text": assistant_text
                })

                # Audio generation is now handled by HeyGen on the frontend
                # No need for ElevenLabs streaming

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
