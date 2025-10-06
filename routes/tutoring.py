"""
Tutoring endpoints using Claude API
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict
import anthropic
import os
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

router = APIRouter()
logger = logging.getLogger(__name__)


class TutoringRequest(BaseModel):
    message: str
    context: Optional[str] = None
    language: str = "mixed"  # english, portuguese, or mixed
    topic: Optional[str] = None


class TutoringResponse(BaseModel):
    response: str
    suggestions: Optional[List[str]] = None
    code_examples: Optional[Dict] = None


@router.post("/chat", response_model=TutoringResponse)
async def chat_with_tutor(request: TutoringRequest):
    """Chat with AI tutor using Claude API"""

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="Claude API key not configured")

    try:
        client = anthropic.Anthropic(api_key=api_key)

        # Build the system prompt based on language preference
        system_prompts = {
            "english": "You are an expert English teacher and programming tutor. Help students learn English through coding examples. Always explain concepts clearly and provide examples.",
            "portuguese": "Você é um professor especialista em inglês e programação. Ajude os alunos a aprender inglês através de exemplos de código. Sempre explique os conceitos claramente em português.",
            "mixed": "You are a bilingual tutor (English/Portuguese) specializing in teaching English and programming. Mix both languages naturally, using Portuguese for explanations and English for technical terms. Help students learn English through coding."
        }

        system_prompt = system_prompts.get(request.language, system_prompts["mixed"])

        if request.topic:
            system_prompt += f" Focus on: {request.topic}"

        # Create the conversation with Claude
        messages = [
            {
                "role": "user",
                "content": request.message
            }
        ]

        if request.context:
            messages.insert(0, {
                "role": "assistant",
                "content": request.context
            })

        response = client.messages.create(
            model="claude-3-haiku-20240307",  # Fast and cost-effective
            max_tokens=1000,
            temperature=0.7,
            system=system_prompt,
            messages=messages
        )

        response_text = response.content[0].text

        # Extract code examples if present
        code_examples = {}
        if "```" in response_text:
            import re
            code_blocks = re.findall(r'```(\w+)?\n(.*?)```', response_text, re.DOTALL)
            for i, (lang, code) in enumerate(code_blocks):
                code_examples[f"example_{i+1}"] = {
                    "language": lang or "plaintext",
                    "code": code.strip()
                }

        # Generate suggestions
        suggestions = []
        if "english" in request.language.lower() or request.language == "mixed":
            suggestions = [
                "Try using this phrase in a sentence",
                "Practice pronunciation with voice recording",
                "Write a simple function using these concepts"
            ]

        return TutoringResponse(
            response=response_text,
            suggestions=suggestions if suggestions else None,
            code_examples=code_examples if code_examples else None
        )

    except anthropic.AuthenticationError:
        # The API key might need to be refreshed or is invalid
        raise HTTPException(
            status_code=401,
            detail="Claude API authentication failed. Please check your API key."
        )
    except anthropic.RateLimitError:
        raise HTTPException(
            status_code=429,
            detail="Rate limit reached. Please try again later."
        )
    except Exception as e:
        logger.error(f"Error calling Claude API: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/lesson")
async def generate_lesson(topic: str, level: str = "intermediate"):
    """Generate a complete lesson plan"""

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="Claude API key not configured")

    try:
        client = anthropic.Anthropic(api_key=api_key)

        prompt = f"""Create a comprehensive English lesson plan for {level} level students on the topic: {topic}

        Include:
        1. Learning objectives
        2. Key vocabulary with definitions
        3. Grammar points
        4. Practice exercises with programming examples
        5. Homework assignment

        Make it practical and focused on tech/programming contexts."""

        response = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=1500,
            temperature=0.7,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        return {
            "topic": topic,
            "level": level,
            "lesson_plan": response.content[0].text
        }

    except Exception as e:
        logger.error(f"Error generating lesson: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/correct")
async def correct_text(text: str, language: str = "english"):
    """Correct grammar and provide feedback"""

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="Claude API key not configured")

    try:
        client = anthropic.Anthropic(api_key=api_key)

        prompt = f"""Correct the following text and provide detailed feedback:

        Text: {text}

        Provide:
        1. Corrected version
        2. List of mistakes and corrections
        3. Grammar tips
        4. Suggestions for improvement"""

        response = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=800,
            temperature=0.5,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        return {
            "original": text,
            "feedback": response.content[0].text
        }

    except Exception as e:
        logger.error(f"Error correcting text: {e}")
        raise HTTPException(status_code=500, detail=str(e))