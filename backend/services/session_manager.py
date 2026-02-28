"""
In-memory session manager.
Handles create / get / answer / confirm / finalize lifecycle.
"""

from fastapi import HTTPException

from models.session_state import SessionState, SessionStatus
from data.fema_template import get_template, get_field, get_total_fields

# ── In-memory store (swap for Redis in production) ──
_sessions: dict[str, SessionState] = {}


def create_session(template_id: str) -> SessionState:
    """Create a new form-filling session."""
    template = get_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail=f"Template '{template_id}' not found")

    session = SessionState(template_id=template_id)
    _sessions[session.session_id] = session
    return session


def get_session(session_id: str) -> SessionState:
    """Retrieve an existing session or 404."""
    session = _sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found")
    return session


def submit_answer(session_id: str, transcript: str, parsed_value: str) -> SessionState:
    """
    Store a pending answer for confirmation.
    Moves session status from ACTIVE → CONFIRMING.
    """
    session = get_session(session_id)

    if session.status == SessionStatus.COMPLETE:
        raise HTTPException(status_code=400, detail="Session is already complete")
    if session.status == SessionStatus.CONFIRMING:
        raise HTTPException(status_code=400, detail="Previous answer awaiting confirmation")

    session.pending_transcript = transcript
    session.pending_value = parsed_value
    session.status = SessionStatus.CONFIRMING
    return session


def confirm_answer(session_id: str, confirmed: bool) -> SessionState:
    """
    Confirm or reject the pending answer.
    If confirmed → store answer, advance to next field (or complete).
    If rejected  → go back to ACTIVE for the same field.
    """
    session = get_session(session_id)

    if session.status != SessionStatus.CONFIRMING:
        raise HTTPException(status_code=400, detail="No answer pending confirmation")

    if confirmed:
        # Store confirmed answer
        field = get_field(session.template_id, session.current_index)
        if field:
            session.answers[field["field_name"]] = session.pending_value or ""

        total = get_total_fields(session.template_id)
        if session.current_index + 1 >= total:
            session.status = SessionStatus.COMPLETE
        else:
            session.current_index += 1
            session.status = SessionStatus.ACTIVE
    else:
        # Retry same field
        session.status = SessionStatus.ACTIVE

    session.pending_value = None
    session.pending_transcript = None
    return session


def finalize_session(session_id: str) -> SessionState:
    """Mark session as complete and trigger PDF generation placeholder."""
    session = get_session(session_id)

    if session.status != SessionStatus.COMPLETE:
        raise HTTPException(
            status_code=400,
            detail="Cannot finalize — not all fields are confirmed",
        )

    # PDF generation will be handled by pdf_filler service
    return session
