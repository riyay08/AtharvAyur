"""Groq-backed implementation of `app.application.ports.llm_gateway.LLMGateway`.

Groq exposes an OpenAI-compatible chat-completions endpoint backed by Llama 3.x
(and other) models running on their LPU hardware. Two important differences vs.
Gemini that this adapter has to absorb:

* Groq does not provide an embedding endpoint. `embed()` returns an empty list,
  which the chat / plan use cases already treat as "skip semantic recall".
* Groq has no built-in `google_search` grounding tool. `generate_health_reply`
  therefore always returns empty citations; the trust-filter pipeline that the
  Gemini gateway applies is unnecessary here.

JSON-shape contracts for the planner / follow-up / tip helpers stay identical
to the Gemini gateway, so downstream parsers do not need any branching.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from groq import APIError, Groq

from app.application.ports.llm_gateway import GroundedReply
from app.config import settings
from app.domain.errors import ConfigurationError, ExternalServiceError

logger = logging.getLogger(__name__)


_CHAT_SYSTEM_TEMPLATE = """You are HolisticAI, a non-diagnostic health & wellness guide that integrates modern lifestyle education with Ayurvedic principles.

CORE DIRECTIVES:
1. THE PIVOT: Never aggressively refuse. Acknowledge, state you cannot diagnose, pivot to safe lifestyle / Ayurvedic tips.
2. MEMORY RELEVANCE: Use Relevant Past History only if it naturally helps answer the current question.
3. CITATION INTEGRITY: Live web search is unavailable. Do not invent URLs. Always return an empty citations array.
4. UNIFIED SAFETY: Check the HealthProfile for medications before discussing any herb/supplement.

{env_block}You must return JSON with this exact schema:
{{"response_text": "...", "citations": []}}

User HealthProfile (JSON; may be incomplete):
{profile_blob}
"""


_WEEKLY_PLAN_SYSTEM = (
    "You are a safe health planner. Using the user's Dosha and recent chat themes, design a 7-day "
    "lifestyle plan. Every task must be in exactly one of: Mind, Fuel, or Body. Every task must have "
    "a context_reason that links it to either the user's Dosha or a specific recent theme. Output a "
    "single raw JSON object with keys daily_focus_message (string) and days (7 items, each with date "
    "YYYY-MM-DD and pillars: {Mind, Fuel, Body}). Each task: {id: number, task: string, "
    "context_reason: string, completed: false}."
)

_FOLLOWUP_SYSTEM = (
    "The user just completed a task. Propose exactly ONE new actionable task in the SAME pillar only. "
    "Do not prescribe medicine. Respond with a single raw JSON object with keys 'task' (under 200 "
    "chars) and 'context_reason' (under 280 chars) that explicitly links to Dosha or a recent chat "
    "theme."
)

_TIP_SYSTEM = (
    "You generate a short, safe daily wellness tip tailored to Ayurvedic dosha + live weather + "
    "location habitat. Output a single raw JSON object with keys tip_title (<= 80 chars), "
    "tip_description (<= 500 chars), icon_name (one of: Sun, CloudRain, Wind, Snowflake, Leaf, "
    "Droplet, Moon). Non-diagnostic; no supplements or dosages."
)

_SESSION_SUMMARY_SYSTEM = (
    "Summarize the following health/wellness conversation in EXACTLY 3 sentences of plain text "
    "(no JSON, no markdown, no bullet points, no preamble). Sentence 1: symptoms or health concerns "
    "the user raised. Sentence 2: actionable lifestyle/wellness insight or suggestion that was "
    "discussed. Sentence 3: how the user's state evolved over the conversation, or what to follow up "
    "on next time. Never state a diagnosis. Never invent details not present in the transcript."
)

_LONG_TERM_FACTS_SYSTEM = (
    "You extract Long-Term Memory facts from a health/wellness conversation transcript. A fact is a "
    "durable, declarative statement about the user that would remain true and useful in future, "
    "unrelated conversations — e.g. a dietary restriction, allergy, chronic condition, firm "
    "preference, or habit ('User is lactose intolerant', 'User prefers mornings for exercise'). "
    "Do NOT extract: symptoms specific to this conversation, moods, one-off events, or anything "
    "already obviously a diagnosis. Most conversations contain ZERO such facts — only extract what "
    "is explicitly stated or directly implied by the user, never invented. Each fact must be a short, "
    "self-contained sentence (under 150 characters) written in third person about 'User'. "
    'Return ONE JSON object with exactly this schema: {"facts": ["...", ...]}. If there are no '
    'durable facts, return {"facts": []}.'
)


def _safe_json(text: str) -> dict[str, Any]:
    """Best-effort decode of a model response into a dict.

    Mirrors the Gemini gateway: when JSON-mode is on Groq returns valid JSON,
    but if the model returns a stray prose response we still want a usable
    `{response_text, citations}` shape downstream.
    """
    s = (text or "").strip()
    try:
        obj = json.loads(s)
        if isinstance(obj, dict):
            return obj
    except Exception:
        pass
    return {"response_text": s, "citations": []}


def _parse_facts_json(text: str) -> tuple[str, ...]:
    """Best-effort decode of `{"facts": [...]}` from a JSON-object-mode response."""
    try:
        obj = json.loads((text or "").strip())
    except Exception:
        return ()
    if not isinstance(obj, dict):
        return ()
    facts = obj.get("facts")
    if not isinstance(facts, list):
        return ()
    return tuple(f.strip() for f in facts if isinstance(f, str) and f.strip())


class GroqLLMGateway:
    """Concrete `LLMGateway` backed by Groq's Llama 3.x chat completions."""

    def __init__(
        self,
        *,
        api_key: str | None = None,
        model: str | None = None,
    ) -> None:
        key = (api_key or settings.groq_api_key or "").strip()
        if not key:
            raise ConfigurationError("GROQ_API_KEY is not set.")
        self._client = Groq(api_key=key)
        self._model = model or settings.groq_model

    # ------------------------------------------------------------------ embeddings

    def embed(self, text: str) -> list[float]:
        # Groq has no embedding endpoint. Returning [] makes the chat / plan
        # use cases skip semantic-history recall instead of failing.
        return []

    # ------------------------------------------------------------------ chat

    def generate_health_reply(
        self,
        *,
        user_message: str,
        profile_blob_json: str,
        recent_history_block: str,
        semantic_history_block: str,
        environment_block: str | None = None,
    ) -> GroundedReply:
        if environment_block:
            env_block = (
                f"Current environment (approximate):\n{environment_block}\n\n"
                "ENVIRONMENT & DOSHA: Tailor suggestions to the environment. Stay non-diagnostic.\n\n"
            )
        else:
            env_block = (
                "ENVIRONMENT & DOSHA: If the user describes their environment, tailor suggestions "
                "accordingly. No environment data was provided for this turn.\n\n"
            )

        system = _CHAT_SYSTEM_TEMPLATE.format(
            env_block=env_block,
            profile_blob=profile_blob_json,
        )
        user_payload = (
            f"User latest message:\n{user_message}\n\n"
            f"Immediate Context (chronological):\n{recent_history_block}\n\n"
            f"Relevant Past History (semantic, only if useful):\n{semantic_history_block}"
        )

        raw = self._chat_json(system=system, user_text=user_payload)
        parsed = _safe_json(raw)
        response_text = (
            parsed.get("response_text")
            if isinstance(parsed.get("response_text"), str)
            else raw
        )
        return GroundedReply(
            reply_text=(response_text or "").strip(),
            citations=(),
            search_queries=(),
        )

    # ------------------------------------------------------------------ JSON tasks

    def generate_weekly_plan_json(
        self,
        *,
        profile_blob_json: str,
        recent_history_block: str,
        semantic_history_block: str,
        week_start_iso: str,
        week_end_iso: str,
    ) -> str:
        user_content = (
            f"Plan week: Monday {week_start_iso} through Sunday {week_end_iso}.\n"
            f"User HealthProfile (JSON; includes Dosha when available):\n{profile_blob_json}\n\n"
            "Semantically relevant user messages from the last 7 days (themes only; do not diagnose):\n"
            f"{semantic_history_block}\n\n"
            "All user messages from the last 7 days (chronological excerpts):\n"
            f"{recent_history_block}\n\n"
            "Return ONE JSON object only (no markdown), matching the schema in the system instruction. "
            f'The 7 "days[].date" values must be consecutive calendar dates from {week_start_iso} onward.'
        )
        return self._chat_json(system=_WEEKLY_PLAN_SYSTEM, user_text=user_content)

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
        user_content = (
            f'Pillar for the new task (must stay in this pillar only): "{pillar}".\n'
            f"Plan calendar day: {plan_day_date}.\n\n"
            "The user just completed this task:\n"
            f"- Task: {completed_task}\n"
            f"- Prior context note: {completed_context}\n\n"
            f"User HealthProfile (JSON):\n{profile_blob_json}\n\n"
            f"Recent user messages (excerpt):\n{recent_history_block}\n\n"
            'Output one JSON object: {"task": "...", "context_reason": "..."}.'
        )
        return self._chat_json(system=_FOLLOWUP_SYSTEM, user_text=user_content)

    def generate_environment_tip_json(
        self,
        *,
        profile_blob_json: str,
        dominant_dosha: str | None,
        environment_blob_json: str,
    ) -> str:
        user_content = (
            f"Dominant Dosha (lowercase or null): {dominant_dosha}\n"
            f"User HealthProfile (JSON):\n{profile_blob_json}\n\n"
            f"Environment context (JSON):\n{environment_blob_json}\n\n"
            'Output one JSON object: {"tip_title": "...", "tip_description": "...", "icon_name": "..."}.'
        )
        return self._chat_json(system=_TIP_SYSTEM, user_text=user_content)

    def generate_session_summary(self, *, transcript: str) -> str:
        user_content = f"Conversation transcript:\n{transcript}"
        return self._chat_text(system=_SESSION_SUMMARY_SYSTEM, user_text=user_content)

    def extract_long_term_facts(self, *, transcript: str) -> tuple[str, ...]:
        user_content = f"Conversation transcript:\n{transcript}"
        raw = self._chat_json(system=_LONG_TERM_FACTS_SYSTEM, user_text=user_content)
        return _parse_facts_json(raw)

    # ------------------------------------------------------------------ helpers

    def _chat_text(self, *, system: str, user_text: str) -> str:
        """Like `_chat_json` but without forcing JSON-object response mode — for
        plain-prose outputs (e.g. the session summary), not JSON payloads."""
        try:
            completion = self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user_text},
                ],
                temperature=0.3,
            )
        except APIError as exc:
            logger.warning("Groq call failed: %s", exc)
            raise ExternalServiceError(f"LLM call failed: {exc}") from exc

        try:
            choice = completion.choices[0]
            return (choice.message.content or "").strip()
        except (AttributeError, IndexError):
            return ""

    def _chat_json(self, *, system: str, user_text: str) -> str:
        """Call Groq's chat-completions in JSON-object mode and return the raw string."""
        try:
            completion = self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user_text},
                ],
                response_format={"type": "json_object"},
                temperature=0.3,
            )
        except APIError as exc:
            logger.warning("Groq call failed: %s", exc)
            raise ExternalServiceError(f"LLM call failed: {exc}") from exc

        try:
            choice = completion.choices[0]
            return (choice.message.content or "").strip()
        except (AttributeError, IndexError):
            return ""
