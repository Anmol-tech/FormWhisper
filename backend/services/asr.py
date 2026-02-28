"""
ASR (Automatic Speech Recognition) service — STUB.
Replace with real ASR (Whisper, Deepgram, etc.) when ready.
"""

from data.fema_template import get_field

# Mock answers keyed by field_name for demo purposes
_MOCK_TRANSCRIPTS: dict[str, str] = {
    "applicant_name": "Sid Johnson",
    "date_of_birth": "March 15, 1990",
    "ssn": "123-45-6789",
    "mailing_address": "1234 Oak Street, Austin, TX 78701",
    "phone_number": "(512) 555-0147",
    "disaster_type": "Hurricane",
    "damaged_property_address": "1234 Oak Street, Austin, TX 78701",
    "has_insurance": "No",
}


async def transcribe(audio_bytes: bytes, template_id: str, field_index: int) -> dict:
    """
    STUB: Pretend to transcribe audio.
    Returns a mock transcript based on the field being answered.

    TODO: Replace with real ASR pipeline:
      1. audio_bytes → Whisper / Deepgram
      2. post-processing (normalize dates, phones, etc.)
    """
    field = get_field(template_id, field_index)
    field_name = field["field_name"] if field else "unknown"
    transcript = _MOCK_TRANSCRIPTS.get(field_name, "sample answer")

    return {
        "transcript": transcript,
        "parsed_value": transcript,   # In real version, apply normalizer
        "confidence": 0.95,
        "field_name": field_name,
    }
