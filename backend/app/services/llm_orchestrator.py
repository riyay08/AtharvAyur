"""
Gemini orchestration with semantic memory + grounded citations.

Call only after deterministic safety checks pass. This module does not perform
the hardcoded safety screening.
"""

from __future__ import annotations

import json
import logging
import re
import uuid
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

from google import genai
from google.genai import types
from google.genai.errors import APIError
from sqlalchemy import desc, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.config import settings
from app.models.chat_history import ChatHistory, ChatRole
from app.models.health_profile import HealthProfile

logger = logging.getLogger(__name__)

# Must match `ChatHistory.embedding` column (pgvector).
_EMBEDDING_DIM = 768

# Authoritative grounding: host/path must look high-trust; commerce patterns rejected.
_TRUSTED_HOST_MARKERS: tuple[str, ...] = (
    ".gov",
    ".edu",
    ".ac.uk",
    ".mil",
    "nih.gov",
    "cdc.gov",
    "who.int",
    "nhs.uk",
    "mayoclinic.org",
    "clevelandclinic.org",
    "hopkinsmedicine.org",
    "webmd.com",
    "merckmanuals.com",
    "ncbi.nlm.nih.gov",
    "pubmed.ncbi.nlm.nih.gov",
    "thelancet.com",
    "lancet.com",
    "nejm.org",
    "bmj.com",
    "statnews.com",
)
_FORBIDDEN_URL_KEYWORDS: tuple[str, ...] = (
    "shop",
    "buy",
    "store",
    "product",
    "cart",
    "sales",
)

_VERIFICATION_FALLBACK = (
    "I cannot find clinical or governmental verification for this specific practice at this time."
)

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


_STRICT_SEARCH_PROTOCOL = """[STRICT SEARCH PROTOCOL]
1. SEARCH OPERATOR ENFORCEMENT: When you generate search queries to ground your response, you MUST append advanced search operators to restrict results to trusted tiers. Your internal queries should prioritize strings like:
   - "[Topic] site:.gov OR site:.edu OR site:who.int"
   - "[Topic] site:mayoclinic.org OR site:clevelandclinic.org OR site:nih.gov"

2. SOURCE HIERARCHY: You must prioritize information in this order:
   - Tier 1 (Gold Standard): Peer-reviewed journals (PubMed, Lancet), Government agencies (NIH, CDC, NHS), and International bodies (WHO).
   - Tier 2 (Clinical Excellence): Academic medical centers (Mayo Clinic, Cleveland Clinic, Johns Hopkins).
   - Tier 3 (Reliable Medical Press): WebMD, Merck Manuals, or STAT News (use only if Tier 1 and 2 are unavailable).
   - TIER 4 (FORBIDDEN): Strictly ignore supplement stores, commercial blogs (.coms without clinical backing), Reddit, Quora, and SEO-farmed wellness sites.

3. VERIFICATION HABIT: If a search returns a result from a Tier 4 source, you must discard that data. If no Tier 1-3 sources can verify a claim, you must state: "I cannot find clinical or governmental verification for this specific practice at this time."
[END SEARCH PROTOCOL]"""


def _hostname(url: str) -> str:
    try:
        host = urlparse(url).hostname
        return (host or "").lower()
    except Exception:
        return ""


def _url_passes_authoritative_grounding(url: str) -> bool:
    if not isinstance(url, str):
        return False
    u = url.strip()
    if not (u.startswith("http://") or u.startswith("https://")):
        return False
    host = _hostname(u)
    if not host:
        return False
    # Commerce / spam signals: check host only so path words like "restore" do not false-positive "store".
    for bad in _FORBIDDEN_URL_KEYWORDS:
        if bad in host:
            return False
    for marker in _TRUSTED_HOST_MARKERS:
        if marker.startswith(".") and host.endswith(marker):
            return True
        if marker in host:
            return True
    return False


def _filter_trusted_grounding_citations(
    citations: list[SourceCitation],
) -> tuple[list[SourceCitation], set[str], int]:
    """Returns (trusted_citations, trusted_url_set, raw_count_before_filter)."""
    raw_count = len(citations)
    trusted: list[SourceCitation] = []
    seen: set[str] = set()
    for c in citations:
        if not _url_passes_authoritative_grounding(c.url):
            logger.info("Grounding citation rejected by trust filter: %s", c.url[:120])
            continue
        if c.url in seen:
            continue
        seen.add(c.url)
        trusted.append(c)
    return trusted, seen, raw_count


def _strip_untrusted_urls_from_response_text(text: str, removed_urls: set[str]) -> str:
    """Remove obvious markdown links and bare URLs that were stripped from citations."""
    if not text or not removed_urls:
        return text
    out = text
    for u in sorted(removed_urls, key=len, reverse=True):
        esc = re.escape(u)
        out = re.sub(rf"\[[^\]]*\]\(\s*{esc}\s*\)", "", out, flags=re.IGNORECASE)
        out = out.replace(u, "")
    out = re.sub(r"\n{3,}", "\n\n", out).strip()
    return out


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


def _build_system_instruction(
    profile: HealthProfile | None,
    *,
    environment_context: dict[str, str] | None = None,
) -> str:
    profile_blob = _health_profile_context_block(profile)
    if environment_context:
        env_blob = json.dumps(environment_context, indent=2, ensure_ascii=False)
        env_block = (
            f"Current environment (approximate from weather and location):\n{env_blob}\n\n"
            "ENVIRONMENT & DESHA: You must tailor your advice to the user's environment. "
            "If they are in a cold or dry place, suggest warming and nourishing practices "
            "(e.g., gentle steam, warm fluids, abhyanga-style self-massage with awareness of allergies, "
            "nasal care education such as traditional nasya only as general wellness context—not as a prescription). "
            "If humidity is high or the air feels damp, favor light, warm, well-digestible foods and movement that "
            "does not overheat. If they are in a dense urban setting, suggest practices to ground the nervous system "
            "and reconnect with nature (short outdoor breaks, breath awareness, routine). "
            "Always stay non-diagnostic and avoid specific dosing or medical instructions.\n\n"
        )
    else:
        env_block = (
            "ENVIRONMENT & DESHA: When the user describes their environment (climate, city, season), tailor your "
            "Ayurvedic lifestyle suggestions accordingly: cold/dry favors warming and unctuous qualities in "
            "moderation; damp favors lightness and warmth; urban stress favors grounding and nature contact. "
            "No environment data was provided for this turn—infer only if the user mentions it.\n\n"
        )

    return f"""You are HolisticAI, a highly intelligent, non-diagnostic health and wellness guide. You integrate modern lifestyle education with Ayurvedic principles based on the user's provided profile.

CORE DIRECTIVES:
1. THE PIVOT (Never aggressively refuse): If a user mentions a symptom (e.g., "I have bloating"), DO NOT say "I cannot help you" or "I am an AI." Instead, acknowledge the symptom, state clearly that you cannot diagnose the underlying cause, and immediately PIVOT to providing general, safe, educational lifestyle and Ayurvedic tips relevant to their profile.
2. MEMORY RELEVANCE: You will be provided with "Relevant Past History". Only reference this history IF it naturally helps answer the user's current question. If the user just says "Hello", do NOT bring up their past medical issues.
3. CITATION INTEGRITY (No fake links): You will use the Google Search tool to find evidence. You MUST NOT invent, guess, or hallucinate URLs. If the search tool does not provide a reputable link for a claim, you must state: "I do not have verified information on this specific topic." When search grounding is used, follow the strict search protocol below for query formulation and source acceptance.
4. UNIFIED SAFETY: Treat all paradigms equally. Do not prescribe Ayurvedic herbs as if they are harmless. If a user asks about taking a supplement/herb, you MUST check their HealthProfile for medications and explicitly state if there are potential interactions, or advise them to check with their doctor.

{_STRICT_SEARCH_PROTOCOL}

{env_block}You must return JSON with this exact schema:
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
    """Keep only citations whose URLs are in ``allowed_urls`` (trusted grounded URLs)."""
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
        if not allowed_urls or u not in allowed_urls:
            continue
        if u in seen:
            continue
        seen.add(u)
        normalized.append(SourceCitation(source_name=source_name.strip() or u, url=u))
    return normalized


def _urls_in_response_text(text: str) -> set[str]:
    found: set[str] = set()
    for m in re.finditer(r"https?://[^\s)\]\"'<>]+", text or ""):
        found.add(m.group(0).rstrip(".,);"))
    return found


def _strip_untrusted_urls_from_free_text(text: str) -> str:
    """Remove bare URLs and markdown links pointing at hosts that fail the trust filter."""
    if not text:
        return text
    out = text
    for m in list(re.finditer(r"https?://[^\s)\]\"'<>]+", out)):
        u = m.group(0).rstrip(".,);")
        if _url_passes_authoritative_grounding(u):
            continue
        esc = re.escape(u)
        out = re.sub(rf"\[[^\]]*\]\(\s*{esc}\s*\)", "", out, flags=re.IGNORECASE)
        out = out.replace(u, "")
    out = re.sub(r"\n{3,}", "\n\n", out).strip()
    return out


def _embed_text(client: genai.Client, text: str) -> list[float]:
    emb = client.models.embed_content(
        model=settings.gemini_embedding_model,
        contents=[text],
        config=types.EmbedContentConfig(output_dimensionality=_EMBEDDING_DIM),
    )
    if not emb.embeddings or not emb.embeddings[0].values:
        return []
    return list(emb.embeddings[0].values)


def _embed_text_safe(client: genai.Client, text: str) -> list[float]:
    try:
        vec = _embed_text(client, text)
    except APIError as exc:
        logger.warning("Gemini embedding failed (semantic memory disabled for this turn): %s", exc)
        return []
    if len(vec) != _EMBEDDING_DIM:
        logger.warning(
            "Embedding length %s != %s (schema mismatch); skipping semantic retrieval.",
            len(vec),
            _EMBEDDING_DIM,
        )
        return []
    return vec


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
    environment_context: dict[str, str] | None = None,
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

    query_embedding = _embed_text_safe(client, user_message)
    immediate_rows = _fetch_immediate_context(db, user_id)
    try:
        relevant_rows = _fetch_semantic_context(db, user_id, query_embedding)
    except SQLAlchemyError as exc:
        logger.warning("Semantic history query failed (pgvector / DB): %s", exc)
        relevant_rows = []

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

    system_instruction = _build_system_instruction(
        health_profile,
        environment_context=environment_context,
    )
    user_content = types.Content(
        role="user",
        parts=[types.Part.from_text(text=payload_text)],
    )

    grounding_tool = types.Tool(google_search=types.GoogleSearch())
    config_with_search = types.GenerateContentConfig(
        system_instruction=system_instruction,
        tools=[grounding_tool],
    )

    try:
        response = client.models.generate_content(
            model=model_id,
            contents=[user_content],
            config=config_with_search,
        )
    except APIError as exc:
        logger.warning(
            "Gemini generate with Google Search failed; retrying without search tool: %s",
            exc,
        )
        fallback_instruction = (
            system_instruction
            + "\n\nNOTE: Live web search is unavailable for this turn. "
            "Return citations as an empty array unless you are citing from retrieved tool output; "
            "never invent URLs."
        )
        config_no_tools = types.GenerateContentConfig(system_instruction=fallback_instruction)
        try:
            response = client.models.generate_content(
                model=model_id,
                contents=[user_content],
                config=config_no_tools,
            )
        except APIError as exc2:
            raise OrchestratorConfigError(
                "The assistant could not reach the AI service (quota, network, model access, or "
                "configuration). Please try again in a few minutes."
            ) from exc2

    safety_stopped = _model_safety_blocked(response)
    finish = _response_finish_reason(response)
    try:
        raw_text = (response.text or "").strip()
    except Exception:
        logger.warning("Could not read response.text from model response.")
        raw_text = ""
    if safety_stopped and not raw_text:
        raw_text = (
            '{"response_text":"The model could not produce a reply for this request due to safety '
            'or policy filters. Please rephrase your request in general wellness terms.",'
            '"citations":[]}'
        )
    if not response.candidates and not raw_text:
        raw_text = '{"response_text":"The model did not return a response. Please try again later.","citations":[]}'

    parsed = _safe_json_response(raw_text)
    fallback_cites_raw, queries, _ = _extract_grounding_urls(response)
    raw_grounding_count = len(fallback_cites_raw)
    trusted_grounding, trusted_urls, _ = _filter_trusted_grounding_citations(fallback_cites_raw)
    all_grounding_rejected = raw_grounding_count > 0 and len(trusted_grounding) == 0

    removed_urls: set[str] = {
        c.url for c in fallback_cites_raw if not _url_passes_authoritative_grounding(c.url)
    }

    parsed_aligned = _normalize_citations(parsed, trusted_urls)
    name_by_url = {c.url: c.source_name for c in parsed_aligned}

    cites_list: list[SourceCitation] = [
        SourceCitation(source_name=name_by_url.get(c.url, c.source_name), url=c.url) for c in trusted_grounding
    ]

    response_text = parsed.get("response_text")
    if not isinstance(response_text, str) or not response_text.strip():
        response_text = raw_text if isinstance(raw_text, str) else ""

    response_text_out = response_text.strip()

    if all_grounding_rejected:
        response_text_out = _VERIFICATION_FALLBACK
        cites_list = []
    else:
        if trusted_urls:
            for u in _urls_in_response_text(response_text_out):
                if u not in trusted_urls:
                    removed_urls.add(u)
            response_text_out = _strip_untrusted_urls_from_response_text(response_text_out, removed_urls)
        else:
            response_text_out = _strip_untrusted_urls_from_free_text(response_text_out)

    return OrchestratorResult(
        response_text=response_text_out,
        citations=tuple(cites_list),
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
