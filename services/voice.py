import aiohttp
import asyncio
import json
import logging
from typing import Optional, Dict, Any, AsyncGenerator
from config import settings
import base64

logger = logging.getLogger(__name__)


class ElevenLabsVoiceService:
    """Real-time voice service using ElevenLabs API."""

    def __init__(self):
        self.api_key = settings.ELEVENLABS_API_KEY
        self.base_url = "https://api.elevenlabs.io/v1"
        self.ws_url = "wss://api.elevenlabs.io/v1/text-to-speech/websocket"
        self.default_voice_id = "21m00Tcm4TlvDq8ikWAM"  # Rachel voice
        self.model_id = "eleven_monolingual_v1"

    async def text_to_speech(
        self,
        text: str,
        voice_id: Optional[str] = None,
        stability: float = 0.5,
        similarity_boost: float = 0.75
    ) -> bytes:
        """Convert text to speech and return audio bytes."""
        voice_id = voice_id or self.default_voice_id
        url = f"{self.base_url}/text-to-speech/{voice_id}"

        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": self.api_key
        }

        data = {
            "text": text,
            "model_id": self.model_id,
            "voice_settings": {
                "stability": stability,
                "similarity_boost": similarity_boost
            }
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=data) as response:
                if response.status == 200:
                    return await response.read()
                else:
                    error = await response.text()
                    logger.error(f"ElevenLabs TTS error: {error}")
                    raise Exception(f"TTS failed: {error}")

    async def text_to_speech_stream(
        self,
        text: str,
        voice_id: Optional[str] = None
    ) -> AsyncGenerator[bytes, None]:
        """Stream text to speech for real-time playback."""
        voice_id = voice_id or self.default_voice_id
        url = f"{self.base_url}/text-to-speech/{voice_id}/stream"

        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": self.api_key
        }

        data = {
            "text": text,
            "model_id": self.model_id,
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75
            }
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=data) as response:
                if response.status == 200:
                    async for chunk in response.content.iter_chunked(1024):
                        yield chunk
                else:
                    error = await response.text()
                    logger.error(f"ElevenLabs streaming error: {error}")
                    raise Exception(f"Streaming failed: {error}")

    async def websocket_stream(
        self,
        voice_id: Optional[str] = None
    ) -> Any:
        """Establish WebSocket connection for real-time conversation."""
        voice_id = voice_id or self.default_voice_id

        session = aiohttp.ClientSession()
        try:
            ws = await session.ws_connect(
                self.ws_url,
                headers={"xi-api-key": self.api_key}
            )

            # Send initial configuration
            await ws.send_json({
                "action": "start",
                "voice_id": voice_id,
                "model_id": self.model_id,
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.75
                }
            })

            return ws, session

        except Exception as e:
            await session.close()
            logger.error(f"WebSocket connection failed: {e}")
            raise

    async def send_text_to_websocket(
        self,
        ws: Any,
        text: str,
        flush: bool = False
    ):
        """Send text to WebSocket for streaming."""
        await ws.send_json({
            "action": "text",
            "text": text,
            "flush": flush
        })

    async def receive_audio_from_websocket(
        self,
        ws: Any
    ) -> AsyncGenerator[bytes, None]:
        """Receive audio chunks from WebSocket."""
        async for msg in ws:
            if msg.type == aiohttp.WSMsgType.TEXT:
                data = json.loads(msg.data)
                if data.get("audio"):
                    # Decode base64 audio
                    audio_bytes = base64.b64decode(data["audio"])
                    yield audio_bytes
            elif msg.type == aiohttp.WSMsgType.ERROR:
                logger.error(f"WebSocket error: {ws.exception()}")
                break

    async def close_websocket(self, ws: Any, session: aiohttp.ClientSession):
        """Close WebSocket connection."""
        await ws.close()
        await session.close()

    async def get_voices(self) -> Dict[str, Any]:
        """Get available voices."""
        url = f"{self.base_url}/voices"
        headers = {"xi-api-key": self.api_key}

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error = await response.text()
                    logger.error(f"Failed to get voices: {error}")
                    raise Exception(f"Failed to get voices: {error}")

    async def get_voice_settings(self, voice_id: str) -> Dict[str, Any]:
        """Get voice settings."""
        url = f"{self.base_url}/voices/{voice_id}/settings"
        headers = {"xi-api-key": self.api_key}

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error = await response.text()
                    logger.error(f"Failed to get voice settings: {error}")
                    raise Exception(f"Failed to get voice settings: {error}")

    async def create_pronunciation_assessment(
        self,
        reference_text: str,
        student_audio: bytes
    ) -> Dict[str, Any]:
        """Assess student pronunciation (mock implementation)."""
        # Note: ElevenLabs doesn't provide pronunciation assessment
        # This would integrate with another service like Azure Speech
        return {
            "overall_score": 85.5,
            "pronunciation_score": 82.0,
            "fluency_score": 88.0,
            "completeness_score": 86.5,
            "word_scores": [
                {"word": "example", "score": 90.0},
                {"word": "pronunciation", "score": 75.0}
            ],
            "feedback": "Good overall pronunciation with slight issues on complex words."
        }

    async def generate_voice_clone(
        self,
        name: str,
        files: list,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a voice clone (requires ElevenLabs Creator+ plan)."""
        url = f"{self.base_url}/voices/add"
        headers = {"xi-api-key": self.api_key}

        data = aiohttp.FormData()
        data.add_field("name", name)
        if description:
            data.add_field("description", description)

        for file_path in files:
            with open(file_path, "rb") as f:
                data.add_field("files", f, filename=file_path.split("/")[-1])

        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, data=data) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error = await response.text()
                    logger.error(f"Failed to create voice clone: {error}")
                    raise Exception(f"Failed to create voice clone: {error}")