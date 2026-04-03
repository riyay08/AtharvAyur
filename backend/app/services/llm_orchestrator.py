"""
Gemini orchestration with semantic memory + grounded citations.

Call only after deterministic safety checks pass. This module does not perform
the hardcoded safety screening.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from typing import Any

from google import genai
from google.genai import types
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.config import settings
from app.models.chat_history import ChatHistory, ChatRole
from app.models.health_profile import HealthProfile


class OrchestratorConfigError(RuntimeError):
    """Missing configuration (e.g. API key)."""


@dataclass(frozen=True, slots=True)
class SourceCitation:
    source_name: str
    url: str


@dataclass(frozen=True, slots=True)
class OrchestratorResult:
    response_text: str
    citations: tuple[SourceCitation, ...] = ()
    web_search_queries: tuple[str, ...] = ()
    finish_reason: str | None = None
    blocked_by_model_safety: bool = False
    prompt_embedding: tuple[float, ...] | None = None


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
    return f"""You are HolisticAI, a highly intelligent, non-diagnostic health and wellness guide. You integrate modern lifestyle education with Ayurvedic principles based on the user's provided profile.

CORE DIRECTIVES:
1. THE PIVOT (Never aggressively refuse): If a user mentions a symptom (e.g., "I have bloating"), DO NOT say "I cannot help you" or "I am an AI." Instead, acknowledge the symptom, state clearly that you cannot diagnose the underlying cause, and immediately PIVOT to providing general, safe, educational lifestyle and Ayurvedic tips relevant to their profile.
2. MEMORY RELEVANCE: You will be provided with "Relevant Past History". Only reference this history IF it naturally helps answer the user's current question. If the user just says "Hello", do NOT bring up their past medical issues.
3. CITATION INTEGRITY (No fake links): You will use the Google Search tool to find evidence. You MUST NOT invent, guess, or hallucinate URLs. If the search tool does not provide a reputable link for a claim, you must state: "I do not have verified information on this specific topic."
4. UNIFIED SAFETY: Treat all paradigms equally. Do not prescribe Ayurvedic herbs as if they are harmless. If a user asks about taking a supplement/herb, you MUST check their HealthProfile for medications and explicitly state if there are potential interactions, or advise them to check with their doctor.

You must return JSON with this exact schema:
{{
  "response_text": "The conversational reply to the user",
  "citations": [{{"source_name": "Name", "url": "Actual URL from Search tool"}}]
}}

User HealthProfile (JSON; may be incomplete):
{profile_blob}
"""


def _format_message(row: ChatHistory) -> str:
    role = "User" if row.role == ChatRole.USER else "Assistant"
    return f"[{role}] {row.message}"


def _format_history_block(rows: list[ChatHistory], *, empty_message: str) -> str:
    if not rows:
        return empty_message
    return "\n".join(f"- {_format_message(r)}" for r in rows)


def _extract_grounding_urls(
    response: types.GenerateContentResponse,
) -> tuple[list[SourceCitation], list[str], set[str]]:
    citations: list[SourceCitation] = []
    queries: list[str] = []
    urls: set[str] = set()
    if not response.candidates:
        return citations, queries, urls
    candidate = response.candidates[0]
    meta = candidate.grounding_metadata
    if not meta:
        return citations, queries, urls
    queries.extend(meta.web_search_queries or [])
    for chunk in meta.grounding_chunks or []:
        web = chunk.web
        if web and web.uri:
            if web.uri not in urls:
                urls.add(web.uri)
                citations.append(SourceCitation(source_name=web.title or web.uri, url=web.uri))
    return citations, queries, urls


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
    return str(fr).rsplit(".", maxsplit=1)[-1]


def _model_safety_blocked(response: types.GenerateContentResponse) -> bool:
    name = _finish_reason_name(response)
    if name is None:
        return False
    return name in {"SAFETY", "BLOCKLIST", "PROHIBITED_CONTENT", "SPII", "RECITATION"}


def _safe_json_response(raw_text: str) -> dict[str, Any]:
    stripped = raw_text.strip()
    try:
        parsed = json.loads(stripped)
        if isinstance(parsed, dict):
            return parsed
    except Exception:
        pass

    marker = '"response_text"'
    marker_idx = stripped.find(marker)
    if marker_idx != -1:
        start = stripped.rfind("{", 0, marker_idx)
        if start != -1:
            depth = 0
            for i in range(start, len(stripped)):
                ch = stripped[i]
                if ch == "{":
                    depth += 1
                elif ch == "}":
                    depth -= 1
                    if depth == 0:
                        candidate = stripped[start : i + 1]
                        try:
                            parsed = json.loads(candidate)
                            if isinstance(parsed, dict):
                                return parsed
                        except Exception:
                            break

    return {"response_text": stripped, "citations": []}


def _normalize_citations(parsed: dict[str, Any], allowed_urls: set[str]) -> list[SourceCitation]:
    normalized: list[SourceCitation] = []
    seen: set[str] = set()
    raw = parsed.get("citations")
    if not isinstance(raw, list):
        return normalized
    for item in raw:
        if not isinstance(item, dict):
            continue
        source_name = item.get("source_name")
        url = item.get("url")
        if not isinstance(source_name, str) or not isinstance(url, str):
            continue
        u = url.strip()
        if not (u.startswith("http://") or u.startswith("https://")):
            continue
        if allowed_urls and u not in allowed_urls:
            continue
        if u in seen:
            continue
        seen.add(u)
        normalized.append(SourceCitation(source_name=source_name.strip() or u, url=u))
    return normalized


def _embed_text(client: genai.Client, text: str) -> list[float]:
    emb = client.models.embed_content(
        model=settings.gemini_embedding_model,
        contents=[text],
        config=types.EmbedContentConfig(output_dimensionality=768),
    )
    if not emb.embeddings or not emb.embeddings[0].values:
        return []
    return list(emb.embeddings[0].values)


def _fetch_immediate_context(db: Session, user_id: uuid.UUID) -> list[ChatHistory]:
    stmt = (
        select(ChatHistory)
        .where(ChatHistory.user_id == user_id)
        .order_by(desc(ChatHistory.timestamp))
        .limit(settings.immediate_history_limit)
    )
    rows = list(db.execute(stmt).scalars().all())
    return list(reversed(rows))


def _fetch_semantic_context(
    db: Session,
    user_id: uuid.UUID,
    query_embedding: list[float],
) -> list[ChatHistory]:
    if not query_embedding:
        return []
    stmt = (
        select(ChatHistory)
        .where(
            ChatHistory.user_id == user_id,
            ChatHistory.role == ChatRole.USER,
            ChatHistory.embedding.is_not(None),
        )
        .order_by(ChatHistory.embedding.cosine_distance(query_embedding))
        .limit(settings.semantic_history_limit)
    )
    return list(db.execute(stmt).scalars().all())


def generate_health_reply(
    user_message: str,
    *,
    db: Session,
    user_id: uuid.UUID,
    health_profile: HealthProfile | None,
    api_key: str | None = None,
    model: str | None = None,
) -> OrchestratorResult:
    key = api_key or settings.gemini_api_key
    if not key or not key.strip():
        raise OrchestratorConfigError(
            "GEMINI_API_KEY is not set. Add it to backend/.env or pass api_key=."
        )

    model_id = model or settings.gemini_model
    client = genai.Client(api_key=key)

    query_embedding = _embed_text(client, user_message)
    immediate_rows = _fetch_immediate_context(db, user_id)
    relevant_rows = _fetch_semantic_context(db, user_id, query_embedding)

    immediate_context = _format_history_block(
        immediate_rows,
        empty_message="No immediate context is available.",
    )
    relevant_context = _format_history_block(
        relevant_rows,
        empty_message="No semantically relevant past history found.",
    )

    payload_text = (
        f"User latest message:\n{user_message}\n\n"
        f"Immediate Context (last {settings.immediate_history_limit} chronological messages):\n"
        f"{immediate_context}\n\n"
        f"Relevant Past History (semantic retrieval, only if useful):\n{relevant_context}"
    )

    grounding_tool = types.Tool(google_search=types.GoogleSearch())
    config = types.GenerateContentConfig(
        system_instruction=_build_system_instruction(health_profile),
        tools=[grounding_tool],
    )

    response = client.models.generate_content(
        model=model_id,
        contents=[
            types.Content(
                role="user",
                parts=[types.Part.from_text(text=payload_text)],
            )
        ],
        config=config,
    )

    safety_stopped = _model_safety_blocked(response)
    finish = _response_finish_reason(response)
    raw_text = (response.text or "").strip()
    if safety_stopped and not raw_text:
        raw_text = (
            '{"response_text":"The model could not produce a reply for this request due to safety '
            'or policy filters. Please rephrase your request in general wellness terms.",'
            '"citations":[]}'
        )
    if not response.candidates and not raw_text:
        raw_text = '{"response_text":"The model did not return a response. Please try again later.","citations":[]}'

    parsed = _safe_json_response(raw_text)
    fallback_cites, queries, grounded_urls = _extract_grounding_urls(response)
    cites = _normalize_citations(parsed, grounded_urls)
    if not cites:
        cites = fallback_cites

    response_text = parsed.get("response_text")
    if not isinstance(response_text, str) or not response_text.strip():
        response_text = raw_text

    return OrchestratorResult(
        response_text=response_text.strip(),
        citations=tuple(cites),
        web_search_queries=tuple(queries),
        finish_reason=finish,
        blocked_by_model_safety=safety_stopped,
        prompt_embedding=tuple(query_embedding) if query_embedding else None,
    )


# --- Weekly plan (Dynamic Category Stack) — consumed by `app.services.weekly_plan_service` ---

WEEKLY_PLAN_DYNAMIC_STACK_SYSTEM = (
    "You are a safe health planner. Using the user's Dosha (from profile) and recent chat themes "
    "(including pgvector-retrieved symptoms), design a 7-day lifestyle and Ayurvedic-inspired plan. "
    "Do not prescribe medicine. Emphasize hydration, movement, sleep, and Dosha-supporting foods. "
    "Every task MUST be placed in exactly one of three pillars: Mind, Fuel, or Body — no other "
    "categories. "
    "Every task MUST include a context_reason string that explicitly links the task to EITHER the "
    "user's Dosha OR a specific recent symptom/theme from their chat history (e.g. "
    "\"To soothe yesterday's bloating\" or \"Balances Pitta per your profile\"). Never use vague "
    "context_reason text. "
    "Output a single raw JSON object (no markdown fences) with exactly this structure: "
    '{"daily_focus_message": string, "days": array of 7 objects each with "date" (YYYY-MM-DD) and '
    '"pillars": {"Mind": array, "Fuel": array, "Body": array}}. '
    "Each task object MUST be: "
    '{"id": number, "task": string, "context_reason": string, "completed": false}. '
    "Use unique numeric ids across all tasks in the entire plan. "
    "Include at least one task per pillar per day; you may include several per pillar."
)
