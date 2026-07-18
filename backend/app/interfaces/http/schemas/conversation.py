from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel


class EndConversationResponse(BaseModel):
    conversation_id: UUID
    status: str
    summary_pending: bool
    """True if a Janitor summarization run was just scheduled for this call."""
