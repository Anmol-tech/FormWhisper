"""
TTS (Text-to-Speech) service — STUB.
Replace with ElevenLabs API calls when ready.
"""


async def synthesize(text: str, voice_id: str = "default") -> bytes | None:
    """
    STUB: Would call ElevenLabs API to synthesize speech.

    TODO: Replace with real TTS:
      1. Call ElevenLabs /v1/text-to-speech/{voice_id}
      2. Return audio bytes (mp3)
      3. Cache common confirmations to save API credits
    """
    # Return None to signal stub mode
    return None
