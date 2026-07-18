"""Orchestrator port — the Observe / Act / Replan (OAR) loop for a chat turn.

Concrete implementation lives in `app/application/orchestrator/` as a plain Python
state machine (no LangGraph/CrewAI, per the v2.0 architecture decision). It wraps
the existing `LLMGateway` port for Act and the outbound guard for Replan.

Only `observe` is async: it's the phase that touches the new async repositories
(`ConversationRepository`, `SessionSummaryRepository`) added in Phase 1, alongside
the legacy sync repositories (profile, chat history) that the hybrid async strategy
deliberately leaves untouched. `act` and `replan` wrap synchronous work today
(`LLMGateway.generate_health_reply` and the outbound guard are both sync) — they
stay sync rather than being async-for-the-sake-of-it.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Protocol

from app.application.ports.llm_gateway import GroundedReply
from app.domain.entities import SessionSummary


@dataclass(frozen=True, slots=True)
class ObservedContext:
    """Everything gathered by Observe; the only input Act/Replan need."""

    user_id: uuid.UUID
    conversation_id: uuid.UUID | None
    user_message: str
    profile_blob_json: str
    recent_history_block: str
    semantic_history_block: str
    conversation_history_block: str = ""
    session_summaries: tuple[SessionSummary, ...] = ()
    known_user_facts_block: str = ""
    daily_checkin_block: str = ""
    environment_block: str | None = None
    embedding: list[float] | None = None
    """The embedding computed for `user_message` during Observe. Exposed so a
    caller that persists the user's `ChatMessage` after the turn (see
    `GenerateHealthReplyViaOrchestrator`) doesn't need a second, redundant
    `LLMGateway.embed()` call just to attach it."""


class Orchestrator(Protocol):
    """Runs one Observe -> Act -> Replan cycle for a single chat turn."""

    async def observe(
        self,
        *,
        user_id: uuid.UUID,
        conversation_id: uuid.UUID | None,
        user_message: str,
    ) -> ObservedContext:
        """Gather context: health profile, recent/semantic chat history, this
        conversation's prior messages (if resuming), the user's last 3
        `SessionSummary` rows across conversations, and semantically relevant
        Long-Term Memory facts from `user_memories`."""
        ...

    def act(self, context: ObservedContext) -> GroundedReply:
        """Call the LLMGateway (today's only tool) to produce a draft reply."""
        ...

    def replan(self, context: ObservedContext, draft: GroundedReply) -> GroundedReply:
        """Run the outbound guard over the draft and return the final reply."""
        ...
