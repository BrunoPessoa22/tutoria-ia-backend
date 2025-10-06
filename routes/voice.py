"""
Voice generation endpoints using ElevenLabs
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import aiohttp
import os
from fastapi.responses import StreamingResponse
import io

router = APIRouter()


class VoiceGenerationRequest(BaseModel):
    text: str
    voice_id: Optional[str] = "EXAVITQu4vr4xnSDxMaL"  # Default: Sarah voice


@router.post("/generate")
async def generate_voice(request: VoiceGenerationRequest):
    """Generate voice audio from text using ElevenLabs API"""

    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="ElevenLabs API key not configured")

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{request.voice_id}"

    headers = {
        "xi-api-key": api_key,
        "Content-Type": "application/json"
    }

    data = {
        "text": request.text,
        "model_id": "eleven_monolingual_v1",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.5
        }
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=data) as response:
                if response.status == 200:
                    audio_data = await response.read()
                    return StreamingResponse(
                        io.BytesIO(audio_data),
                        media_type="audio/mpeg",
                        headers={
                            "Content-Disposition": "inline; filename=speech.mp3"
                        }
                    )
                else:
                    error_text = await response.text()
                    raise HTTPException(
                        status_code=response.status,
                        detail=f"ElevenLabs API error: {error_text}"
                    )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/voices")
async def get_available_voices():
    """Get list of available voices from ElevenLabs"""

    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="ElevenLabs API key not configured")

    url = "https://api.elevenlabs.io/v1/voices"
    headers = {"xi-api-key": api_key}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        "voices": [
                            {
                                "voice_id": voice.get("voice_id"),
                                "name": voice.get("name"),
                                "preview_url": voice.get("preview_url"),
                                "category": voice.get("category", "unknown")
                            }
                            for voice in data.get("voices", [])
                        ]
                    }
                else:
                    raise HTTPException(
                        status_code=response.status,
                        detail="Failed to fetch voices"
                    )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))