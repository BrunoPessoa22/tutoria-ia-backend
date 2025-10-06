import aiohttp
import asyncio
import json
import logging
from typing import Optional, Dict, Any, List
from config import settings
import uuid

logger = logging.getLogger(__name__)


class HeyGenAvatarService:
    """Service for creating AI avatar videos with HeyGen API."""

    def __init__(self):
        self.api_key = settings.HEYGEN_API_KEY
        self.base_url = "https://api.heygen.com/v2"
        self.default_avatar_id = "Angela"  # Default avatar

    async def create_lesson_video(
        self,
        script: str,
        avatar_id: Optional[str] = None,
        voice_id: Optional[str] = None,
        lesson_metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Create a lesson video with an avatar teacher."""
        avatar_id = avatar_id or self.default_avatar_id

        url = f"{self.base_url}/video_translations"

        headers = {
            "X-Api-Key": self.api_key,
            "Content-Type": "application/json"
        }

        data = {
            "video_inputs": [{
                "character": {
                    "type": "avatar",
                    "avatar_id": avatar_id,
                    "avatar_style": "business"
                },
                "voice": {
                    "type": "text",
                    "input_text": script,
                    "voice_id": voice_id or "en-US-JennyNeural",
                    "speed": 1.0
                },
                "background": {
                    "type": "color",
                    "value": "#4F46E5"  # Indigo background
                }
            }],
            "dimension": {
                "width": 1920,
                "height": 1080
            },
            "metadata": lesson_metadata or {}
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        return {
                            "video_id": result.get("video_id"),
                            "status": "processing",
                            "estimated_time": result.get("estimated_time", 120)
                        }
                    else:
                        error = await response.text()
                        logger.error(f"HeyGen API error: {error}")
                        raise Exception(f"Failed to create avatar video: {error}")
        except Exception as e:
            logger.error(f"Error creating avatar video: {e}")
            raise

    async def get_video_status(self, video_id: str) -> Dict[str, Any]:
        """Check the status of a video generation."""
        url = f"{self.base_url}/video_status"

        headers = {
            "X-Api-Key": self.api_key
        }

        params = {
            "video_id": video_id
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params) as response:
                if response.status == 200:
                    result = await response.json()
                    return {
                        "status": result.get("status"),
                        "video_url": result.get("video_url"),
                        "thumbnail_url": result.get("thumbnail_url"),
                        "duration": result.get("duration")
                    }
                else:
                    error = await response.text()
                    logger.error(f"Failed to get video status: {error}")
                    raise Exception(f"Failed to get video status: {error}")

    async def create_interactive_avatar_session(
        self,
        avatar_id: Optional[str] = None,
        student_profile: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Create an interactive avatar session for real-time teaching."""
        avatar_id = avatar_id or self.default_avatar_id

        # In production, this would create a real-time streaming session
        # For now, return mock session data
        session_id = str(uuid.uuid4())

        return {
            "session_id": session_id,
            "avatar_id": avatar_id,
            "websocket_url": f"wss://stream.heygen.com/v1/sessions/{session_id}",
            "token": "mock_token_" + session_id,
            "expires_in": 3600  # 1 hour
        }

    async def send_avatar_response(
        self,
        session_id: str,
        text: str,
        emotion: Optional[str] = "neutral"
    ) -> Dict[str, Any]:
        """Send text for the avatar to speak in real-time."""
        url = f"{self.base_url}/sessions/{session_id}/speak"

        headers = {
            "X-Api-Key": self.api_key,
            "Content-Type": "application/json"
        }

        data = {
            "text": text,
            "emotion": emotion,  # happy, sad, angry, surprised, neutral
            "gesture": "auto"  # Automatic gestures based on text
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=data) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error = await response.text()
                    logger.error(f"Failed to send avatar response: {error}")
                    raise Exception(f"Failed to send avatar response: {error}")

    async def create_lesson_intro(
        self,
        student_name: str,
        lesson_topic: str,
        lesson_objectives: List[str]
    ) -> Dict[str, Any]:
        """Create a personalized lesson introduction video."""
        script = f"""Hello {student_name}! Welcome to today's English lesson.

Today, we'll be learning about {lesson_topic}.

By the end of this lesson, you will be able to:
{' '.join(f'{i+1}. {obj}' for i, obj in enumerate(lesson_objectives))}

Let's begin our exciting journey to master English together!
Remember, practice makes perfect, and I'm here to help you every step of the way.

Are you ready? Let's get started!"""

        return await self.create_lesson_video(
            script=script,
            lesson_metadata={
                "type": "lesson_intro",
                "student": student_name,
                "topic": lesson_topic
            }
        )

    async def create_lesson_recap(
        self,
        student_name: str,
        key_points: List[str],
        homework: Optional[str] = None,
        next_lesson_preview: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a lesson recap video."""
        script = f"""Excellent work today, {student_name}!

Let's quickly review what we learned:
{' '.join(f'{i+1}. {point}' for i, point in enumerate(key_points))}

{"Your homework for next time is: " + homework if homework else ""}

{"In our next lesson, we'll explore: " + next_lesson_preview if next_lesson_preview else ""}

Keep practicing, and I'll see you in our next lesson.
Great job today! Goodbye!"""

        return await self.create_lesson_video(
            script=script,
            lesson_metadata={
                "type": "lesson_recap",
                "student": student_name
            }
        )

    async def get_available_avatars(self) -> List[Dict[str, Any]]:
        """Get list of available avatars."""
        # Mock data - in production, this would call the HeyGen API
        return [
            {
                "id": "Angela",
                "name": "Angela",
                "gender": "female",
                "ethnicity": "caucasian",
                "age_appearance": "30s",
                "style": "professional",
                "preview_url": "https://example.com/angela_preview.jpg"
            },
            {
                "id": "James",
                "name": "James",
                "gender": "male",
                "ethnicity": "african",
                "age_appearance": "40s",
                "style": "casual",
                "preview_url": "https://example.com/james_preview.jpg"
            },
            {
                "id": "Sophia",
                "name": "Sophia",
                "gender": "female",
                "ethnicity": "asian",
                "age_appearance": "20s",
                "style": "friendly",
                "preview_url": "https://example.com/sophia_preview.jpg"
            },
            {
                "id": "Carlos",
                "name": "Carlos",
                "gender": "male",
                "ethnicity": "hispanic",
                "age_appearance": "30s",
                "style": "energetic",
                "preview_url": "https://example.com/carlos_preview.jpg"
            }
        ]

    async def generate_pronunciation_video(
        self,
        word: str,
        phonetic: str,
        example_sentence: str
    ) -> Dict[str, Any]:
        """Generate a video teaching pronunciation of a specific word."""
        script = f"""Let's learn how to pronounce the word: {word}

The phonetic pronunciation is: {phonetic}

Listen carefully and repeat after me: {word}
{word}
{word}

Now let's use it in a sentence:
{example_sentence}

Practice saying this word throughout the day.
Remember, the key to good pronunciation is practice!"""

        return await self.create_lesson_video(
            script=script,
            lesson_metadata={
                "type": "pronunciation",
                "word": word
            }
        )

    async def create_grammar_explanation_video(
        self,
        grammar_point: str,
        explanation: str,
        examples: List[str]
    ) -> Dict[str, Any]:
        """Create a video explaining a grammar concept."""
        script = f"""Today's grammar focus: {grammar_point}

{explanation}

Let me show you some examples:
{' '.join(f'Example {i+1}: {ex}' for i, ex in enumerate(examples))}

Remember this rule and practice using it in your conversations.
Grammar is the foundation of clear communication!"""

        return await self.create_lesson_video(
            script=script,
            lesson_metadata={
                "type": "grammar_explanation",
                "topic": grammar_point
            }
        )