"""
ElevenLabs Text-to-Speech helper.
Transforms text into speech and returns a data URL for easy playback in the UI.
"""

from __future__ import annotations

import base64
import os
from typing import Any

import httpx
from fastapi import HTTPException, status

# Prefer standard name; fall back to legacy key in .env for convenience.
ELEVEN_API_KEY = os.getenv("ELEVENLABS_API_KEY") or os.getenv("apiKey")

# A sensible default voice; users can override via request.voice_id.
DEFAULT_VOICE_ID = "21m00Tcm4TlvDq8ikWAM"  # Rachel (English)


async def synthesize(text: str, voice_id: str | None = None) -> str:
    """
    Call ElevenLabs TTS and return an audio data URL (MP3).
    Raises HTTPException on failure so the router can surface an API error.
    """
    if not text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="text is required",
        )

    if not ELEVEN_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Missing ELEVENLABS_API_KEY",
        )

    vid = DEFAULT_VOICE_ID if voice_id in (None, "", "default") else voice_id
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{vid}/stream"

    headers = {
        "xi-api-key": ELEVEN_API_KEY,
        "accept": "audio/mpeg",
        "content-type": "application/json",
    }
    payload: dict[str, Any] = {
        "text": text,
        "model_id": "eleven_monolingual_v1",
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
    }

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(url, headers=headers, json=payload)

    if resp.status_code >= 400:
        try:
            err = resp.json()
        except Exception:
            err = resp.text
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={"message": "ElevenLabs TTS failed", "upstream": err},
        )

    audio_b64 = base64.b64encode(resp.content).decode("ascii")
    return f"data:audio/mpeg;base64,{audio_b64}"
