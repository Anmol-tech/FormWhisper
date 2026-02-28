"""
LLM service — Qwen2.5-VL-3B via AMD-hosted vLLM endpoint.

Provides a general-purpose chat completion interface.
"""

from __future__ import annotations

import os
from typing import Any

import httpx
from fastapi import HTTPException, status

LLM_BASE_URL = os.getenv("LLM_BASE_URL", "http://165.245.130.21:30000")
LLM_MODEL = os.getenv("LLM_MODEL", "Qwen/Qwen2.5-VL-3B-Instruct")
LLM_TIMEOUT = int(os.getenv("LLM_TIMEOUT", "30"))


async def chat(
    messages: list[dict[str, Any]],
    *,
    max_tokens: int = 256,
    temperature: float = 0.3,
    model: str | None = None,
) -> dict[str, Any]:
    """
    Send a chat-completion request to the Qwen VL endpoint and return the
    full response payload (OpenAI-compatible format).

    Messages can contain plain text or multimodal content parts (images).
    """
    payload = {
        "model": model or LLM_MODEL,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "stream": False,
    }

    async with httpx.AsyncClient(timeout=LLM_TIMEOUT) as client:
        resp = await client.post(
            f"{LLM_BASE_URL}/v1/chat/completions",
            headers={"Content-Type": "application/json"},
            json=payload,
        )

    if resp.status_code >= 400:
        try:
            err = resp.json()
        except Exception:
            err = resp.text
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={"message": "LLM request failed", "upstream": err},
        )

    return resp.json()


def extract_content(response: dict[str, Any]) -> str:
    """Pull the assistant message text out of a chat-completion response."""
    try:
        return response["choices"][0]["message"]["content"]
    except (KeyError, IndexError):
        return ""


def build_image_message(image_base64: str, media_type: str, text: str) -> dict[str, Any]:
    """Build an OpenAI-compatible multimodal user message with an image.

    Args:
        image_base64: raw base64 string of the image.
        media_type:   e.g. "image/png" or "image/jpeg".
        text:         the text prompt to accompany the image.
    """
    data_url = f"data:{media_type};base64,{image_base64}"
    return {
        "role": "user",
        "content": [
            {"type": "text", "text": text},
            {"type": "image_url", "image_url": {"url": data_url}},
        ],
    }
