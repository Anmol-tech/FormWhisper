"""LLM router — exposes the Qwen VL chat-completion endpoint to the frontend."""

from fastapi import APIRouter
from models.schemas import (
    LLMChatRequest,
    LLMChatResponse,
    AnalyzeFormRequest,
    AnalyzeFormResponse,
)
from services.llm import chat, extract_content, build_image_message

router = APIRouter(prefix="/llm", tags=["llm"])


@router.post("/chat", response_model=LLMChatResponse)
async def llm_chat(body: LLMChatRequest):
    """
    General-purpose chat completion.

    Supports both plain-text and multimodal (vision) messages.
    For vision, send content as a list of {type, text/image_url} parts.
    """
    messages = [m.model_dump() for m in body.messages]

    response = await chat(
        messages=messages,
        max_tokens=body.max_tokens,
        temperature=body.temperature,
        model=body.model,
    )

    content = extract_content(response)
    usage = response.get("usage", {})

    return LLMChatResponse(
        content=content,
        model=response.get("model", body.model or ""),
        prompt_tokens=usage.get("prompt_tokens", 0),
        completion_tokens=usage.get("completion_tokens", 0),
        total_tokens=usage.get("total_tokens", 0),
    )


@router.post("/analyze-form", response_model=AnalyzeFormResponse)
async def analyze_form(body: AnalyzeFormRequest):
    """
    Send a base64-encoded image of a form to the Qwen VL model.

    The model visually reads the form and returns a JSON array of fields
    with suggested prompts — ready to feed into ElevenLabs TTS.

    Pipeline (future):
      1. Upload PDF  →  convert to PNG/JPG  →  base64 encode
      2. POST here   →  VL model reads form  →  returns field questions
      3. Frontend feeds questions to TTS and voice-interaction flow
    """
    user_msg = build_image_message(
        image_base64=body.image_base64,
        media_type=body.image_media_type,
        text=body.prompt,
    )

    response = await chat(
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a form-analysis assistant. You will receive an image "
                    "of a paper or digital form. Identify every fillable field and "
                    "return structured JSON only."
                ),
            },
            user_msg,
        ],
        max_tokens=body.max_tokens,
        temperature=0.2,
    )

    content = extract_content(response)
    usage = response.get("usage", {})

    return AnalyzeFormResponse(
        raw_content=content,
        model=response.get("model", ""),
        prompt_tokens=usage.get("prompt_tokens", 0),
        completion_tokens=usage.get("completion_tokens", 0),
        total_tokens=usage.get("total_tokens", 0),
    )
