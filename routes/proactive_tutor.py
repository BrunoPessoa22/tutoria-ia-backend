"""
Proactive AI Tutor - Structured 45-minute lessons based on Cultura Builder
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Literal
import anthropic
import os
import logging
from dotenv import load_dotenv
import json
from datetime import datetime

load_dotenv()

router = APIRouter()
logger = logging.getLogger(__name__)


class LessonState(BaseModel):
    module_id: int
    lesson_id: int
    section_index: int = 0  # Track which section of the lesson we're in
    elapsed_time: int = 0  # Minutes elapsed in lesson
    stage: Literal["intro", "section1", "section2", "section3", "practice", "review", "closing"]
    student_responses: List[str] = []
    interaction_count: int = 0  # Track interactions for pacing
    awaiting_response: bool = False


class StudentInput(BaseModel):
    message: str
    lesson_state: LessonState
    is_voice: bool = True


class TeacherResponse(BaseModel):
    message: str
    action_type: Literal["lecture", "interactive", "practice", "review", "closing"]
    expects_response: bool
    next_stage: Optional[str] = None
    lesson_progress: float
    estimated_time_remaining: int  # Minutes remaining
    section_title: Optional[str] = None


# Structured 45-minute lesson plan based on Cultura Builder manuscript
LESSON_PLAN = {
    "1": {  # Lesson 1: Introdução ao Mundo dos Builders
        "title": "Bem-vindo ao Cultura Builder: Sua Jornada Começa Aqui",
        "duration": 45,  # minutes
        "sections": [
            {
                "stage": "intro",
                "duration": 5,
                "title": "Abertura e Boas-vindas",
                "content": """Olá! Eu sou sua professora de IA e estou muito animada para nossa primeira aula!

                Nos próximos 45 minutos, vamos explorar o fascinante mundo dos Builders - pessoas como você que estão usando IA para transformar suas vidas e carreiras.

                Você sabia que mais de 3.500 brasileiros já se tornaram Builders? Hoje você começa sua jornada!

                Vamos começar com uma pergunta simples: O que te trouxe aqui hoje? O que você espera aprender?""",
                "interactive": True
            },
            {
                "stage": "section1",
                "duration": 10,
                "title": "O Impacto da IA no Trabalho Brasileiro",
                "content": """Agora vou compartilhar algo importante: a IA não está vindo para roubar empregos, está vindo para amplificar suas capacidades!

                Veja o caso da Lu, do Magazine Luiza. Ela é uma IA que atende milhões de clientes, mas não substituiu vendedores - ela os liberou para tarefas mais estratégicas e humanas.

                No Brasil, temos vantagens únicas:
                1. Nossa criatividade e "jeitinho brasileiro" - impossível de automatizar
                2. Nossa diversidade cultural - nos torna adaptáveis
                3. Nossa capacidade de conexão humana - sempre será necessária

                Pense comigo: se você pudesse ter um assistente super inteligente trabalhando com você 24/7, o que você faria diferente?""",
                "interactive": True
            },
            {
                "stage": "section2",
                "duration": 10,
                "title": "O que é ser um Builder?",
                "content": """Builder não é programador. Builder é alguém que constrói soluções usando as ferramentas disponíveis.

                Deixe eu contar a história do João, um contador de São Paulo. Ele usou IA para automatizar relatórios que levavam 3 dias para fazer. Agora faz em 30 minutos. Com o tempo livre, criou uma consultoria e triplicou sua renda.

                Ou a Maria, professora de inglês no interior de Minas. Criou um assistente de IA para corrigir redações. Hoje atende 10x mais alunos online.

                Builders têm 3 características:
                1. Curiosidade - sempre perguntam "e se...?"
                2. Coragem - não têm medo de experimentar
                3. Comunidade - aprendem e ensinam outros

                Qual dessas características você já tem? E qual precisa desenvolver?""",
                "interactive": True
            },
            {
                "stage": "section3",
                "duration": 10,
                "title": "IA Generativa: Seu Novo Superpoder",
                "content": """Agora o mais empolgante: IA Generativa é como ter uma equipe inteira no seu computador!

                Imagine:
                - Um designer que cria logos em segundos
                - Um escritor que nunca tem bloqueio criativo
                - Um programador que codifica suas ideias
                - Um tradutor fluente em 100 idiomas

                Tudo isso está disponível AGORA, para VOCÊ!

                ChatGPT, Claude, Gemini - são ferramentas que qualquer pessoa pode usar. Não precisa ser técnico!

                Vou dar um exemplo prático: um restaurante aqui de São Paulo usou IA para criar todo seu cardápio, incluindo descrições e fotos. Economizou R$ 15.000 em design.

                Que problema do seu dia a dia você gostaria de resolver com IA?""",
                "interactive": True
            },
            {
                "stage": "practice",
                "duration": 8,
                "title": "Exercício Prático: Sua Primeira Interação com IA",
                "content": """Hora de colocar a mão na massa! Vamos fazer um exercício juntos.

                Quero que você imagine um problema real que você tem. Pode ser pessoal ou profissional.

                Agora vamos estruturar como pedir ajuda para uma IA resolver isso:

                1. Defina o problema claramente
                2. Diga o resultado desejado
                3. Dê contexto relevante

                Por exemplo: "Preciso criar posts para Instagram sobre culinária vegana. Quero 5 ideias criativas para a semana, com textos curtos e sugestões de hashtags."

                Agora é sua vez! Me conta seu problema e vamos estruturar juntos a melhor forma de resolvê-lo com IA.""",
                "interactive": True
            },
            {
                "stage": "review",
                "duration": 5,
                "title": "Revisão e Aprendizados",
                "content": """Excelente trabalho! Vamos revisar o que aprendemos hoje:

                ✓ IA é ferramenta de ampliação, não substituição
                ✓ Brasil tem vantagens competitivas únicas
                ✓ Ser Builder é sobre resolver problemas, não programar
                ✓ IA Generativa já está acessível para todos

                Você deu o primeiro passo importante hoje. De 0 a 10, como você avalia seu entendimento sobre o potencial da IA agora?

                Baseado no que aprendemos, qual será sua primeira ação prática depois desta aula?""",
                "interactive": True
            },
            {
                "stage": "closing",
                "duration": 2,
                "title": "Encerramento e Próximos Passos",
                "content": """Parabéns por completar sua primeira aula do Cultura Builder! 🎉

                Você já faz parte de uma comunidade de mais de 3.500 Builders brasileiros!

                Sua tarefa para casa:
                1. Crie uma conta gratuita no ChatGPT ou Claude
                2. Faça 3 perguntas diferentes para a IA
                3. Anote uma ideia de como usar IA no seu trabalho

                Na próxima aula, vamos aprofundar em "Prompt Engineering" - a arte de conversar com IA para obter resultados incríveis!

                Lembre-se: Você não está aprendendo apenas sobre IA, está construindo seu futuro!

                Até a próxima aula! Continue curioso e continue construindo! 🚀""",
                "interactive": False
            }
        ]
    }
}


@router.post("/lead-class")
async def lead_class(student_input: StudentInput) -> TeacherResponse:
    """
    Delivers a structured 45-minute lesson based on Cultura Builder content
    """

    # Get the lesson plan
    lesson = LESSON_PLAN.get(str(student_input.lesson_state.lesson_id), LESSON_PLAN["1"])

    # Get current section based on stage
    current_section = None
    for section in lesson["sections"]:
        if section["stage"] == student_input.lesson_state.stage:
            current_section = section
            break

    if not current_section:
        current_section = lesson["sections"][0]

    # Calculate time remaining
    elapsed = student_input.lesson_state.elapsed_time
    time_remaining = lesson["duration"] - elapsed

    # Calculate lesson progress
    stage_to_progress = {
        "intro": 0.1,
        "section1": 0.25,
        "section2": 0.45,
        "section3": 0.65,
        "practice": 0.80,
        "review": 0.90,
        "closing": 1.0
    }
    progress = stage_to_progress.get(student_input.lesson_state.stage, 0.5)

    # Determine action type based on stage
    action_type_map = {
        "intro": "lecture",
        "section1": "interactive",
        "section2": "interactive",
        "section3": "interactive",
        "practice": "practice",
        "review": "review",
        "closing": "closing"
    }
    action_type = action_type_map.get(student_input.lesson_state.stage, "lecture")

    # If it's the first interaction in this section, deliver the content directly
    if student_input.lesson_state.interaction_count == 0 or not student_input.lesson_state.awaiting_response:
        teacher_message = current_section["content"]
        expects_response = current_section.get("interactive", False)
    else:
        # Use Claude to respond to student and continue the lesson
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            teacher_message = f"Muito bem! {current_section['content']}"
            expects_response = current_section.get("interactive", False)
        else:
            try:
                client = anthropic.Anthropic(api_key=api_key)

                system_prompt = f"""Você é uma professora experiente do Cultura Builder ministrando uma aula estruturada.

                Seção atual: {current_section['title']}
                Tempo de aula decorrido: {elapsed} minutos de 45 minutos

                IMPORTANTE:
                1. Você está MINISTRANDO uma aula, não apenas conversando
                2. Mantenha o foco no conteúdo da seção atual
                3. Responda brevemente ao aluno e CONTINUE com o conteúdo da aula
                4. Use exemplos práticos brasileiros
                5. Mantenha o ritmo - temos {time_remaining} minutos restantes
                6. Seja calorosa mas profissional

                Conteúdo desta seção que você deve cobrir:
                {current_section['content']}
                """

                messages = [{"role": "user", "content": f"Resposta do aluno: {student_input.message}"}]

                response = client.messages.create(
                    model="claude-3-haiku-20240307",
                    max_tokens=400,
                    temperature=0.7,
                    system=system_prompt,
                    messages=messages
                )

                teacher_message = response.content[0].text
                expects_response = current_section.get("interactive", False)

            except Exception as e:
                logger.error(f"Error getting Claude response: {e}")
                teacher_message = f"Excelente resposta! {current_section['content']}"
                expects_response = current_section.get("interactive", False)

    # Determine next stage
    stage_order = ["intro", "section1", "section2", "section3", "practice", "review", "closing"]
    current_index = stage_order.index(student_input.lesson_state.stage)
    next_stage = stage_order[current_index + 1] if current_index < len(stage_order) - 1 else None

    return TeacherResponse(
        message=teacher_message,
        action_type=action_type,
        expects_response=expects_response,
        next_stage=next_stage,
        lesson_progress=progress,
        estimated_time_remaining=time_remaining,
        section_title=current_section["title"]
    )


@router.post("/start-lesson")
async def start_lesson(module_id: int = 1, lesson_id: int = 1) -> TeacherResponse:
    """
    Start a structured 45-minute lesson
    """
    lesson = LESSON_PLAN.get(str(lesson_id), LESSON_PLAN["1"])
    intro_section = lesson["sections"][0]

    return TeacherResponse(
        message=intro_section["content"],
        action_type="lecture",
        expects_response=intro_section.get("interactive", True),
        next_stage="section1",
        lesson_progress=0.0,
        estimated_time_remaining=45,
        section_title=intro_section["title"]
    )