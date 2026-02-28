"""Pydantic request / response schemas for the FormWhisper API."""

from pydantic import BaseModel


# ── Session ──────────────────────────────────────────────

class FieldMeta(BaseModel):
    """Metadata for a single form field sent to the client."""
    id: int
    field_name: str
    prompt: str
    type: str
    sensitive: bool
    audio_url: str | None = None


class StartSessionRequest(BaseModel):
    template_id: str = "fema_009_0_3"


class StartSessionResponse(BaseModel):
    session_id: str
    template_title: str
    total_fields: int
    current_field: FieldMeta


class SessionStatusResponse(BaseModel):
    session_id: str
    status: str  # active | confirming | complete
    current_index: int
    total_fields: int
    current_field: FieldMeta | None = None
    pending_value: str | None = None
    answers: dict[str, str]
    progress_pct: float


# ── Answer / Confirm ─────────────────────────────────────

class AnswerAudioResponse(BaseModel):
    transcript: str
    parsed_value: str
    confidence: float
    field_name: str


class ConfirmRequest(BaseModel):
    confirmed: bool


class ConfirmResponse(BaseModel):
    status: str  # active | confirming | complete
    current_field: FieldMeta | None = None
    current_index: int
    message: str


# ── Finalize / PDF ───────────────────────────────────────

class FinalizeResponse(BaseModel):
    status: str
    pdf_url: str
    message: str


# ── TTS (optional) ───────────────────────────────────────

class TTSRequest(BaseModel):
    text: str
    voice_id: str = "default"


class TTSResponse(BaseModel):
    audio_url: str | None = None
    message: str


# ── Security (optional) ─────────────────────────────────

class SecurityCheckRequest(BaseModel):
    device_signal: str = ""
    session_id: str = ""


class SecurityCheckResponse(BaseModel):
    safe: bool
    message: str
