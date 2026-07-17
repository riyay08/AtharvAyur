from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class SessionSummary:
    """A short LLM-generated recap of one conversation.

    The Janitor worker writes these when a conversation ends; the Orchestrator
    reads the most recent few to inject prior context into the system prompt.
    """

    id: uuid.UUID
    conversation_id: uuid.UUID
    summary_text: str
    created_at: datetime | None = None
