"""Session state machine for FormWhisper."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class SessionStatus(str, Enum):
    ACTIVE = "active"          # Waiting for an answer
    CONFIRMING = "confirming"  # Answer received, waiting for yes/no
    COMPLETE = "complete"      # All fields confirmed


@dataclass
class SessionState:
    """Represents the live state of one form-filling session."""

    session_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    template_id: str = "fema_009_0_3"
    current_index: int = 0
    answers: dict[str, str] = field(default_factory=dict)
    status: SessionStatus = SessionStatus.ACTIVE
    pending_value: str | None = None        # Value waiting for confirmation
    pending_transcript: str | None = None   # Raw transcript before confirmation
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    pdf_bytes: bytes | None = None          # Filled PDF once finalized
