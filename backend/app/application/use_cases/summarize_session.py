"""The Janitor's business logic: summarize an ended conversation.

Kept here (application layer) rather than in `infrastructure/background/` so it
stays unit-testable with fakes — no DB, no LLM SDK, no APScheduler/BackgroundTasks
involved. `app/infrastructure/background/summary_worker.py` is the thin plumbing
that wires this use case to real repositories/gateway and is callable from
FastAPI `BackgroundTasks`.

Two passes over the same transcript, run in sequence:
  1. `generate_session_summary` — the 3-sentence `SessionSummary` recap (unchanged).
  2. `extract_long_term_facts` — 0+ durable facts (diet, allergies, firm
     preferences) written to `UserMemory` for cross-session recall. This is a
     strictly additive second pass; a failure here never blocks the summary.
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass

from app.application.ports.llm_gateway import LLMGateway
from app.application.ports.repositories import (
    ChatRepository,
    ConversationRepository,
    SessionSummaryRepository,
    UserMemoryRepository,
)
from app.domain.entities import ConversationStatus, SessionSummary
from app.domain.errors import NotFoundError
from app.domain.services.context_blocks import build_conversation_transcript

logger = logging.getLogger(__name__)

_MAX_TITLE_LENGTH = 255


def _title_from_summary(summary_text: str) -> str:
    """First sentence of the summary, trimmed to fit the `title` column."""
    first_sentence = summary_text.strip().split(". ")[0].strip().rstrip(".")
    if not first_sentence:
        return "Conversation"
    return first_sentence[:_MAX_TITLE_LENGTH]


@dataclass(frozen=True, slots=True)
class SummarizeSession:
    """Fetch a conversation's messages, summarize them, persist the recap,
    retitle the conversation, and extract any Long-Term Memory facts. This is
    the Janitor's Observe->Summarize->Extract->Store loop.

    Hybrid-async: `chat_repo` and `llm` are the legacy sync ports (called directly,
    no `await`); `conversations`/`summaries`/`user_memories` are the async Phase 1+ ports.
    """

    chat_repo: ChatRepository
    conversations: ConversationRepository
    summaries: SessionSummaryRepository
    user_memories: UserMemoryRepository
    llm: LLMGateway

    async def execute(self, conversation_id: uuid.UUID) -> SessionSummary | None:
        conversation = await self.conversations.get_by_id(conversation_id)
        if conversation is None:
            raise NotFoundError(f"Conversation {conversation_id} not found.")

        messages = self.chat_repo.list_for_conversation(conversation_id)
        if not messages:
            return None

        transcript = build_conversation_transcript(messages)
        summary_text = self.llm.generate_session_summary(transcript=transcript).strip()
        if not summary_text:
            return None

        summary = await self.summaries.add(
            SessionSummary(
                id=uuid.uuid4(),
                conversation_id=conversation_id,
                summary_text=summary_text,
            )
        )

        conversation.title = _title_from_summary(summary_text)
        conversation.status = ConversationStatus.ENDED
        await self.conversations.update(conversation)

        await self._extract_and_store_facts(
            user_id=conversation.user_id,
            conversation_id=conversation_id,
            transcript=transcript,
        )

        return summary

    async def _extract_and_store_facts(
        self, *, user_id: uuid.UUID, conversation_id: uuid.UUID, transcript: str
    ) -> None:
        """Best-effort second pass. Logs and swallows failures — a broken fact
        extraction must never take down the (already-persisted) session summary."""
        try:
            facts = self.llm.extract_long_term_facts(transcript=transcript)
        except Exception:
            logger.exception(
                "Janitor: long-term fact extraction failed for conversation %s", conversation_id
            )
            return

        if not facts:
            return

        source = f"session:{conversation_id}"
        for fact_text in facts:
            try:
                embedding = self.llm.embed(fact_text) or None
                await self.user_memories.add_fact(
                    user_id=user_id,
                    fact_text=fact_text,
                    embedding=embedding,
                    source=source,
                )
            except Exception:
                logger.exception(
                    "Janitor: failed to store long-term fact for conversation %s", conversation_id
                )
