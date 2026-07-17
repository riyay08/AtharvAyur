from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

from app.domain.value_objects import ChatRole


@dataclass(slots=True)
class ChatMessage:
    """One row in the chat log. Embedding is optional and may be attached later."""

    id: uuid.UUID
    user_id: uuid.UUID
    role: ChatRole
    message: str
    timestamp: datetime | None = None
    embedding: list[float] | None = None
    conversation_id: uuid.UUID | None = None
