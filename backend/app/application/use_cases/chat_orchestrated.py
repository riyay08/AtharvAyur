"""`POST /api/v1/chat` business logic — chat traffic unified onto the `Orchestrator`.

This supersedes `GenerateHealthReply` (`app/application/use_cases/chat.py`) for
new traffic: instead of calling `LLMGateway.generate_health_reply` directly
with hand-built context blocks, it delegates the Observe/Act/Replan cycle to
an `Orchestrator`, which gives every chat turn the same Summary Cache +
Long-Term Memory context the rest of the v2.0 memory cycle already uses.

Everything the legacy use case did that Observe/Act/Replan does *not* own
still lives here, so this remains at parity with `GenerateHealthReply`:
  - the inbound safety check (must run before any LLM call is made),
  - persisting both turns of the exchange (now tagged with `conversation_id`),
  - the audit trail,
  - weather/environment context (Observe has no weather dependency; this
    layers it onto the `ObservedContext` right before Act),
  - the sync `UnitOfWork` commit for the legacy chat/audit tables.

On top of that, it owns conversation lifecycle (get-or-create) since the
Orchestrator's `observe()` only *reads* conversations — creating a new one on
a fresh chat (no `conversation_id` supplied) is this use case's job, backed by
the async `AsyncUnitOfWork` for the new v2.0 tables.
"""

from __future__ import annotations

import json
import logging
import uuid
from dataclasses import dataclass, replace

from app.application.dtos import GenerateHealthReplyInput, GenerateHealthReplyOutput
from app.application.ports.async_unit_of_work import AsyncUnitOfWork
from app.application.ports.llm_gateway import GroundedReply
from app.application.ports.orchestrator import ObservedContext, Orchestrator
from app.application.ports.repositories import (
    AuditLogRepository,
    ChatRepository,
    ConversationRepository,
    HealthProfileRepository,
)
from app.application.ports.unit_of_work import UnitOfWork
from app.application.ports.weather_gateway import WeatherGateway
from app.domain.entities import ChatMessage, Conversation, ConversationStatus
from app.domain.errors import ExternalServiceError, NotFoundError
from app.domain.services.safety_policy import SafetyResult, evaluate_message
from app.domain.value_objects import ChatRole, SafetyBlockReason

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class GenerateHealthReplyViaOrchestrator:
    chat_repo: ChatRepository
    profiles: HealthProfileRepository
    conversations: ConversationRepository
    audit: AuditLogRepository
    orchestrator: Orchestrator
    weather: WeatherGateway
    uow: UnitOfWork
    async_uow: AsyncUnitOfWork

    async def execute(self, cmd: GenerateHealthReplyInput) -> GenerateHealthReplyOutput:
        conversation_id = await self._resolve_conversation_id(cmd)
        profile = self.profiles.get_by_user_id(cmd.user_id)

        safety: SafetyResult = evaluate_message(cmd.message, health_profile=profile)
        if not safety.allowed:
            self._persist_turn(
                user_id=cmd.user_id,
                conversation_id=conversation_id,
                user_text=cmd.message,
                assistant_text=safety.escalation_message or "",
                user_embedding=None,
            )
            self.audit.record(
                actor=str(cmd.user_id),
                action=f"chat.blocked:{safety.reason.value}",
            )
            self.uow.commit()
            logger.info(
                "chat.orchestrated user_id=%s conversation_id=%s blocked=True reason=%s",
                cmd.user_id,
                conversation_id,
                safety.reason.value,
            )
            return GenerateHealthReplyOutput(
                reply_text=safety.escalation_message or "",
                blocked=True,
                block_reason=safety.reason.value,
                conversation_id=conversation_id,
            )

        context = await self.orchestrator.observe(
            user_id=cmd.user_id,
            conversation_id=conversation_id,
            user_message=cmd.message,
        )
        context = await self._with_environment_block(context, cmd)

        draft = self.orchestrator.act(context)
        final = self.orchestrator.replan(context, draft)

        self._persist_turn(
            user_id=cmd.user_id,
            conversation_id=conversation_id,
            user_text=cmd.message,
            assistant_text=final.reply_text,
            user_embedding=context.embedding,
        )
        self.audit.record(actor=str(cmd.user_id), action="chat.reply")
        self.uow.commit()

        self._log_turn(user_id=cmd.user_id, conversation_id=conversation_id, context=context, final=final)

        return GenerateHealthReplyOutput(
            reply_text=final.reply_text,
            blocked=False,
            block_reason=SafetyBlockReason.NONE.value,
            citations=final.citations,
            search_queries=final.search_queries,
            conversation_id=conversation_id,
        )

    async def _resolve_conversation_id(self, cmd: GenerateHealthReplyInput) -> uuid.UUID:
        if cmd.conversation_id is not None:
            conversation = await self.conversations.get_by_id(cmd.conversation_id)
            if conversation is None or conversation.user_id != cmd.user_id:
                raise NotFoundError(f"Conversation {cmd.conversation_id} not found for this user.")
            return cmd.conversation_id

        created = await self.conversations.add(
            Conversation(id=uuid.uuid4(), user_id=cmd.user_id, status=ConversationStatus.ACTIVE)
        )
        await self.async_uow.commit()
        return created.id

    async def _with_environment_block(
        self, context: ObservedContext, cmd: GenerateHealthReplyInput
    ) -> ObservedContext:
        if cmd.lat is None or cmd.lon is None:
            return context
        try:
            weather_ctx = await self.weather.get_context(lat=cmd.lat, lon=cmd.lon)
        except ExternalServiceError:
            return context
        return replace(context, environment_block=json.dumps(weather_ctx, indent=2))

    def _persist_turn(
        self,
        *,
        user_id: uuid.UUID,
        conversation_id: uuid.UUID,
        user_text: str,
        assistant_text: str,
        user_embedding: list[float] | None,
    ) -> None:
        self.chat_repo.add(
            ChatMessage(
                id=uuid.uuid4(),
                user_id=user_id,
                role=ChatRole.USER,
                message=user_text,
                embedding=user_embedding or None,
                conversation_id=conversation_id,
            )
        )
        self.chat_repo.add(
            ChatMessage(
                id=uuid.uuid4(),
                user_id=user_id,
                role=ChatRole.ASSISTANT,
                message=assistant_text,
                conversation_id=conversation_id,
            )
        )

    def _log_turn(
        self,
        *,
        user_id: uuid.UUID,
        conversation_id: uuid.UUID,
        context: ObservedContext,
        final: GroundedReply,
    ) -> None:
        injected_chars = (
            len(context.profile_blob_json)
            + len(context.recent_history_block)
            + len(context.semantic_history_block)
            + len(context.conversation_history_block)
            + len(context.known_user_facts_block)
            + sum(len(s.summary_text) for s in context.session_summaries)
        )
        # Heuristic (~4 chars/token) — no tokenizer is wired up; good enough
        # for trend-watching context-window budget in logs.
        approx_tokens = max(1, injected_chars // 4)
        logger.info(
            "chat.orchestrated user_id=%s conversation_id=%s blocked=False "
            "injected_chars=%d approx_tokens=%d summaries=%d has_known_facts=%s "
            "resumed=%s citations=%d",
            user_id,
            conversation_id,
            injected_chars,
            approx_tokens,
            len(context.session_summaries),
            bool(context.known_user_facts_block),
            bool(context.conversation_history_block),
            len(final.citations),
        )
