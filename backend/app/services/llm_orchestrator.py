"""
Gemini orchestration with Google Search grounding (official `google-genai` SDK).

Call only after deterministic safety checks pass. This module does not perform
safety screening itself.
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any

from google import genai
from google.genai import types

from app.config import settings
from app.models.chat_history import ChatHistory, ChatRole
from app.models.health_profile import HealthProfile


class OrchestratorConfigError(RuntimeError):
    """Missing configuration (e.g. API key)."""


@dataclass(frozen=True, slots=True)
class SourceCitation:
    """A web source returned via Gemini grounding metadata."""

    title: str | None
    uri: str


@dataclass(frozen=True, slots=True)
class OrchestratorResult:
    """Model reply plus structured grounding fields for the API layer."""

    text: str
    citations: tuple[SourceCitation, ...] = ()
    web_search_queries: tuple[str, ...] = ()
    finish_reason: str | None = None
    blocked_by_model_safety: bool = False


def _flatten_profile_json(value: Any) -> str:
    parts: list[str] = []

    def walk(node: Any) -> None:
        if node is None:
            return
        if isinstance(node, str):
            parts.append(node)
        elif isinstance(node, bool):
            parts.append("true" if node else "false")
        elif isinstance(node, (int, float)):
            parts.append(str(node))
        elif isinstance(node, list):
            for item in node:
                walk(item)
        elif isinstance(node, dict):
            for key, val in node.items():
                parts.append(str(key))
                walk(val)
        else:
            parts.append(str(node))

    walk(value)
    return " ".join(parts)


def _health_profile_context_block(profile: HealthProfile | None) -> str:
    if profile is None:
        return "No structured health profile has been provided for this user."
    payload = {
        "conditions": profile.conditions,
        "allergies": profile.allergies,
        "medications": profile.medications,
    }
    try:
        return json.dumps(payload, indent=2, default=str)
    except TypeError:
        return json.dumps(
            {
                "conditions": _flatten_profile_json(profile.conditions),
                "allergies": _flatten_profile_json(profile.allergies),
                "medications": _flatten_profile_json(profile.medications),
            },
            indent=2,
        )


def _build_system_instruction(profile: HealthProfile | None) -> str:
    profile_blob = _health_profile_context_block(profile)
    return f"""You are a non-diagnostic health assistant for HolisticAI Health.

Hard rules:
- You must never diagnose conditions or imply a definitive medical diagnosis.
- You must never recommend starting, stopping, or changing prescription or OTC medications, doses, or supplements.
- You must encourage users to consult licensed clinicians for personal medical decisions.
- Use the provided Google Search tool when answering factual or guideline-style questions so answers can be grounded in current public sources.
- When you rely on search results, cite sources clearly (e.g. name the organization and link to the URL from grounding metadata).
- If information is uncertain or user-specific, say so and suggest professional evaluation.

User health profile (JSON; may be incomplete — do not infer beyond what is listed):
{profile_blob}
"""


def _chat_role_to_gemini_role(role: ChatRole) -> str:
    return "user" if role == ChatRole.USER else "model"


def _history_to_contents(history: Sequence[ChatHistory]) -> list[types.Content]:
    ordered = sorted(history, key=lambda m: m.timestamp)
    contents: list[types.Content] = []
    for row in ordered:
        contents.append(
            types.Content(
                role=_chat_role_to_gemini_role(row.role),
                parts=[types.Part.from_text(text=row.message)],
            )
        )
    return contents


def _extract_grounding(response: types.GenerateContentResponse) -> tuple[list[SourceCitation], list[str]]:
    citations: list[SourceCitation] = []
    queries: list[str] = []
    if not response.candidates:
        return citations, queries
    candidate = response.candidates[0]
    meta = candidate.grounding_metadata
    if not meta:
        return citations, queries
    queries.extend(meta.web_search_queries or [])
    seen: set[str] = set()
    for chunk in meta.grounding_chunks or []:
        web = chunk.web
        if web and web.uri and web.uri not in seen:
            seen.add(web.uri)
            citations.append(SourceCitation(title=web.title, uri=web.uri))
    return citations, queries


def _response_finish_reason(response: types.GenerateContentResponse) -> str | None:
    if not response.candidates:
        return None
    fr = response.candidates[0].finish_reason
    if fr is None:
        return None
    return str(fr)


def _finish_reason_name(response: types.GenerateContentResponse) -> str | None:
    if not response.candidates:
        return None
    fr = response.candidates[0].finish_reason
    if fr is None:
        return None
    if hasattr(fr, "name"):
        return str(fr.name)
    s = str(fr)
    return s.rsplit(".", maxsplit=1)[-1]


def _model_safety_blocked(response: types.GenerateContentResponse) -> bool:
    name = _finish_reason_name(response)
    if name is None:
        return False
    return name in {"SAFETY", "BLOCKLIST", "PROHIBITED_CONTENT", "SPII", "RECITATION"}


def generate_health_reply(
    user_message: str,
    *,
    health_profile: HealthProfile | None,
    chat_history: Sequence[ChatHistory],
    api_key: str | None = None,
    model: str | None = None,
) -> OrchestratorResult:
    """
    Call Gemini with Google Search grounding.

    Parameters
    ----------
    user_message:
        Latest user turn (not yet persisted).
    health_profile:
        ORM profile injected into the system instruction.
    chat_history:
        Prior turns; only the last five (by timestamp) are sent as conversational memory.
    api_key:
        Optional override; defaults to ``settings.gemini_api_key``.
    model:
        Optional override; defaults to ``settings.gemini_model``.
    """
    key = api_key or settings.gemini_api_key
    if not key or not key.strip():
        raise OrchestratorConfigError(
            "GEMINI_API_KEY is not set. Add it to backend/.env or pass api_key=."
        )

    model_id = model or settings.gemini_model
    client = genai.Client(api_key=key)

    prior = sorted(chat_history, key=lambda m: m.timestamp)[-5:]
    contents = _history_to_contents(prior) + [
        types.Content(
            role="user",
            parts=[types.Part.from_text(text=user_message)],
        )
    ]

    grounding_tool = types.Tool(google_search=types.GoogleSearch())
    config = types.GenerateContentConfig(
        system_instruction=_build_system_instruction(health_profile),
        tools=[grounding_tool],
    )

    response = client.models.generate_content(
        model=model_id,
        contents=contents,
        config=config,
    )

    safety_stopped = _model_safety_blocked(response)
    finish = _response_finish_reason(response)
    text = (response.text or "").strip()
    if safety_stopped and not text:
        text = (
            "The model could not produce a reply for this request (safety or policy filters). "
            "Please rephrase your question in general wellness terms, or speak with a qualified "
            "health professional for personal guidance."
        )
    if not response.candidates and not text:
        text = "The model did not return a response. Please try again later."

    cites, queries = _extract_grounding(response)
    return OrchestratorResult(
        text=text,
        citations=tuple(cites),
        web_search_queries=tuple(queries),
        finish_reason=finish,
        blocked_by_model_safety=safety_stopped,
    )
