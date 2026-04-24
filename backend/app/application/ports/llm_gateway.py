"""LLM gateway port.

Abstracts text generation, embeddings, and the grounded-chat case. Infrastructure
layer implements this against Google Gemini; tests can fake it deterministically.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from app.domain.value_objects import Citation


@dataclass(frozen=True, slots=True)
class GroundedReply:
    reply_text: str
    citations: tuple[Citation, ...] = ()
    search_queries: tuple[str, ...] = ()


class LLMGateway(Protocol):
    def embed(self, text: str) -> list[float]:
        """Return the embedding vector (empty list if embedding is unavailable)."""
        ...

    def generate_health_reply(
        self,
        *,
        user_message: str,
        profile_blob_json: str,
        recent_history_block: str,
        semantic_history_block: str,
        environment_block: str | None = None,
    ) -> GroundedReply: ...

    def generate_weekly_plan_json(
        self,
        *,
        profile_blob_json: str,
        recent_history_block: str,
        semantic_history_block: str,
        week_start_iso: str,
        week_end_iso: str,
    ) -> str:
        """Return raw text that normalize_weekly_plan_payload can parse."""
        ...

    def generate_followup_task_json(
        self,
        *,
        pillar: str,
        completed_task: str,
        completed_context: str,
        plan_day_date: str,
        profile_blob_json: str,
        recent_history_block: str,
    ) -> str:
        """Return raw text containing a JSON object: {task, context_reason}."""
        ...

    def generate_environment_tip_json(
        self,
        *,
        profile_blob_json: str,
        dominant_dosha: str | None,
        environment_blob_json: str,
    ) -> str:
        """Return raw text containing {tip_title, tip_description, icon_name}."""
        ...
