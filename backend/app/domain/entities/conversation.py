from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class ConversationStatus(str, Enum):
    ACTIVE = "active"
    ENDED = "ended"


@dataclass(slots=True)
class Conversation:
    """A bounded chat session ('folder'). Messages link to it via `conversation_id`."""

    id: uuid.UUID
    user_id: uuid.UUID
    status: ConversationStatus = ConversationStatus.ACTIVE
    title: str | None = None
    created_at: datetime | None = None
