"""TTS router — STUB for ElevenLabs dynamic confirmations."""

from fastapi import APIRouter
from models.schemas import TTSRequest, TTSResponse

router = APIRouter(tags=["tts"])


@router.post("/tts", response_model=TTSResponse, status_code=501)
async def text_to_speech(body: TTSRequest):
    """
    STUB: Generate speech audio from text.

    TODO: Integrate ElevenLabs API
      - POST https://api.elevenlabs.io/v1/text-to-speech/{voice_id}
      - Use pre-generated audio for static prompts
      - Live TTS only for dynamic confirmations ("I heard X, correct?")
    """
    return TTSResponse(
        audio_url=None,
        message=f"TTS not implemented yet. Would synthesize: '{body.text}'",
    )
