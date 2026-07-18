"""`ChatOrchestrator` — the default `Orchestrator` port implementation.

Plain Python OAR state machine (no LangGraph/CrewAI, per the v2.0 architecture
decision). It is "the recipe" — it only sequences calls to ports it's handed;
all real work (querying Postgres, calling the LLM, regex-rewriting text) lives
in the repositories / gateways / domain services it wraps.

Hybrid-async split (matches `ports/orchestrator.py`):
  - `observe` is async — it's the only phase touching the new async
    `ConversationRepository`/`SessionSummaryRepository`/`UserMemoryRepository`
    from Phase 1+. It also calls the legacy *sync* `HealthProfileRepository`/
    `ChatRepository` directly (no `await`) — those stay on the sync engine,
    untouched, per the hybrid async strategy.
  - `act`/`replan` are sync — they wrap `LLMGateway.generate_health_reply` and
    the outbound guard, both of which are sync today.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date

from app.application.ports.llm_gateway import GroundedReply, LLMGateway
from app.application.ports.orchestrator import ObservedContext
from app.application.ports.repositories import (
    ChatRepository,
    CheckInRepository,
    ConversationRepository,
    HealthProfileRepository,
    SessionSummaryRepository,
    UserMemoryRepository,
)
from app.domain.errors import NotFoundError
from app.domain.services.context_blocks import (
    build_conversation_transcript,
    build_daily_checkin_block,
    build_history_block,
    build_known_user_facts_block,
    build_profile_blob_json,
)
from app.domain.services.outbound_guard import guard_reply


def _combine_context_blocks(context: ObservedContext) -> str:
    """Fold Observe's extra context into the 'recent history' block that
    `LLMGateway.generate_health_reply` already accepts.

    The port's signature is intentionally left unchanged, so this is how the
    Summary Cache, Long-Term Memory facts, and conversation resume reach the
    user payload without touching `LLMGateway` at all.

    Injection order (LLM reads top-to-bottom):
      1. Today's daily check-in (logged wellness state)
      2. Session summaries (compressed cross-session recaps)
      3. Known user facts (semantically retrieved LTM)
      4. This conversation's transcript (if resuming)
      5. Recent 7-day user messages (chronological)
    """
    sections: list[str] = []
    if context.daily_checkin_block:
        sections.append(context.daily_checkin_block)
    if context.session_summaries:
        summary_lines = "\n".join(f"- {s.summary_text}" for s in context.session_summaries)
        sections.append(f"Summaries of recent past sessions:\n{summary_lines}")
    if context.known_user_facts_block:
        sections.append(context.known_user_facts_block)
    if context.conversation_history_block:
        sections.append(f"This conversation so far:\n{context.conversation_history_block}")
    sections.append(context.recent_history_block)
    return "\n\n".join(sections)


@dataclass(frozen=True, slots=True)
class ChatOrchestrator:
    """Default `Orchestrator` implementation for a single chat turn."""

    profiles: HealthProfileRepository
    chat_repo: ChatRepository
    check_ins: CheckInRepository
    conversations: ConversationRepository
    summaries: SessionSummaryRepository
    user_memories: UserMemoryRepository
    llm: LLMGateway

    async def observe(
        self,
        *,
        user_id: uuid.UUID,
        conversation_id: uuid.UUID | None,
        user_message: str,
    ) -> ObservedContext:
        # Legacy sync repositories — untouched by the async migration, called
        # directly (no `await`) from inside this async method.
        profile = self.profiles.get_by_user_id(user_id)
        today = date.today()
        todays_checkins = self.check_ins.list_week(user_id, today, today)
        latest_checkin = todays_checkins[-1] if todays_checkins else None
        daily_checkin_block = build_daily_checkin_block(latest_checkin)
        embedding = self.llm.embed(user_message)
        recent = self.chat_repo.list_recent_user_messages(user_id, days=7, limit=80)
        semantic = (
            self.chat_repo.list_semantic_user_messages(user_id, embedding, days=7, limit=5)
            if embedding
            else []
        )

        conversation_history_block = ""
        if conversation_id is not None:
            conversation = await self.conversations.get_by_id(conversation_id)
            if conversation is None or conversation.user_id != user_id:
                raise NotFoundError(f"Conversation {conversation_id} not found for this user.")
            transcript = self.chat_repo.list_for_conversation(conversation_id)
            conversation_history_block = build_conversation_transcript(transcript)

        session_summaries = tuple(await self.summaries.list_recent_for_user(user_id, limit=3))

        relevant_facts = (
            await self.user_memories.search_relevant_facts(user_id, embedding, limit=3)
            if embedding
            else []
        )
        known_user_facts_block = build_known_user_facts_block(relevant_facts)

        return ObservedContext(
            user_id=user_id,
            conversation_id=conversation_id,
            user_message=user_message,
            profile_blob_json=build_profile_blob_json(profile),
            recent_history_block=build_history_block(recent),
            semantic_history_block=build_history_block(semantic),
            conversation_history_block=conversation_history_block,
            session_summaries=session_summaries,
            known_user_facts_block=known_user_facts_block,
            daily_checkin_block=daily_checkin_block,
            embedding=embedding or None,
        )

    def act(self, context: ObservedContext) -> GroundedReply:
        return self.llm.generate_health_reply(
            user_message=context.user_message,
            profile_blob_json=context.profile_blob_json,
            recent_history_block=_combine_context_blocks(context),
            semantic_history_block=context.semantic_history_block,
            environment_block=context.environment_block,
        )

    def replan(self, context: ObservedContext, draft: GroundedReply) -> GroundedReply:
        guarded = guard_reply(draft.reply_text)
        if not guarded.rewritten:
            return draft
        return GroundedReply(
            reply_text=guarded.text,
            citations=draft.citations,
            search_queries=draft.search_queries,
        )
