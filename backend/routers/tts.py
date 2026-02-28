"""TTS router — ElevenLabs integration."""

from fastapi import APIRouter

from models.schemas import TTSRequest, TTSResponse
from services import tts as tts_service

router = APIRouter(tags=["tts"])


@router.post("/tts", response_model=TTSResponse)
async def text_to_speech(body: TTSRequest):
    """
    Generate speech audio from text via ElevenLabs.
    Returns a data URL (audio/mpeg) so the frontend can play it without storage.
    """
    audio_url = await tts_service.synthesize(body.text, voice_id=body.voice_id)
    return TTSResponse(audio_url=audio_url, message="ok")
