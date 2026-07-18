"""Conversation lifecycle use cases (v2.0 — 'Session Persistence').

Scheduling the Janitor background task is an HTTP-framework concern (FastAPI
`BackgroundTasks`), not business logic, so it deliberately does NOT live here —
see `interfaces/http/routers/v1/conversations.py`. This use case only owns the
ownership check + status transition.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from app.application.ports.async_unit_of_work import AsyncUnitOfWork
from app.application.ports.repositories import ConversationRepository
from app.domain.entities import Conversation, ConversationStatus
from app.domain.errors import NotFoundError


@dataclass(frozen=True, slots=True)
class EndConversationResult:
    conversation: Conversation
    already_ended: bool
    """True if the conversation was already `ENDED` before this call — the
    caller should treat this as an idempotent no-op and NOT re-trigger the
    Janitor (avoids duplicate `SessionSummary` rows on retried/duplicate calls)."""


@dataclass(frozen=True, slots=True)
class EndConversation:
    conversations: ConversationRepository
    uow: AsyncUnitOfWork

    async def execute(self, *, conversation_id: uuid.UUID, user_id: uuid.UUID) -> EndConversationResult:
        conversation = await self.conversations.get_by_id(conversation_id)
        if conversation is None or conversation.user_id != user_id:
            raise NotFoundError(f"Conversation {conversation_id} not found for this user.")

        if conversation.status is ConversationStatus.ENDED:
            return EndConversationResult(conversation=conversation, already_ended=True)

        conversation.status = ConversationStatus.ENDED
        updated = await self.conversations.update(conversation)
        await self.uow.commit()
        return EndConversationResult(conversation=updated, already_ended=False)
