"""Gemini-backed implementation of `app.application.ports.llm_gateway.LLMGateway`.

Owns: google.genai client, grounded-chat prompts, citation trust filter, JSON extraction.
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

from google import genai
from google.genai import types
from google.genai.errors import APIError

from app.application.ports.llm_gateway import GroundedReply
from app.config import settings
from app.domain.errors import ConfigurationError, ExternalServiceError
from app.domain.value_objects import Citation

logger = logging.getLogger(__name__)

_EMBEDDING_DIM = 768

_TRUSTED_HOST_MARKERS: tuple[str, ...] = (
    ".gov", ".edu", ".ac.uk", ".mil",
    "nih.gov", "cdc.gov", "who.int", "nhs.uk", "mayoclinic.org", "clevelandclinic.org",
    "hopkinsmedicine.org", "webmd.com", "merckmanuals.com", "ncbi.nlm.nih.gov",
    "pubmed.ncbi.nlm.nih.gov", "thelancet.com", "lancet.com", "nejm.org",
    "bmj.com", "statnews.com",
)
_FORBIDDEN_URL_KEYWORDS: tuple[str, ...] = ("shop", "buy", "store", "product", "cart", "sales")

_VERIFICATION_FALLBACK = (
    "I cannot find clinical or governmental verification for this specific practice at this time."
)


_STRICT_SEARCH_PROTOCOL = """[STRICT SEARCH PROTOCOL]
1. SEARCH OPERATOR ENFORCEMENT: When you generate search queries to ground your response, you MUST append advanced search operators to restrict results to trusted tiers.
2. SOURCE HIERARCHY: Tier 1 peer-reviewed / government, Tier 2 academic medical centers, Tier 3 reliable medical press. TIER 4 (FORBIDDEN) commercial blogs, Reddit, Quora, SEO wellness sites.
3. VERIFICATION HABIT: If no Tier 1-3 source verifies, state: "I cannot find clinical or governmental verification for this specific practice at this time."
[END SEARCH PROTOCOL]"""


def _hostname(url: str) -> str:
    try:
        host = urlparse(url).hostname
        return (host or "").lower()
    except Exception:
        return ""


def _url_trusted(url: str) -> bool:
    if not isinstance(url, str):
        return False
    u = url.strip()
    if not (u.startswith("http://") or u.startswith("https://")):
        return False
    host = _hostname(u)
    if not host:
        return False
    for bad in _FORBIDDEN_URL_KEYWORDS:
        if bad in host:
            return False
    for marker in _TRUSTED_HOST_MARKERS:
        if marker.startswith(".") and host.endswith(marker):
            return True
        if marker in host:
            return True
    return False


def _strip_untrusted_urls(text: str) -> str:
    if not text:
        return text
    out = text
    for m in list(re.finditer(r"https?://[^\s)\]\"'<>]+", out)):
        u = m.group(0).rstrip(".,);")
        if _url_trusted(u):
            continue
        esc = re.escape(u)
        out = re.sub(rf"\[[^\]]*\]\(\s*{esc}\s*\)", "", out, flags=re.IGNORECASE)
        out = out.replace(u, "")
    return re.sub(r"\n{3,}", "\n\n", out).strip()


def _safe_json(text: str) -> dict[str, Any]:
    s = text.strip()
    try:
        obj = json.loads(s)
        if isinstance(obj, dict):
            return obj
    except Exception:
        pass
    marker = '"response_text"'
    idx = s.find(marker)
    if idx != -1:
        start = s.rfind("{", 0, idx)
        if start != -1:
            depth = 0
            for i in range(start, len(s)):
                ch = s[i]
                if ch == "{":
                    depth += 1
                elif ch == "}":
                    depth -= 1
                    if depth == 0:
                        try:
                            return json.loads(s[start : i + 1])
                        except Exception:
                            break
    return {"response_text": s, "citations": []}


_CHAT_SYSTEM_TEMPLATE = """You are HolisticAI, a non-diagnostic health & wellness guide that integrates modern lifestyle education with Ayurvedic principles.

CORE DIRECTIVES:
1. THE PIVOT: Never aggressively refuse. Acknowledge, state you cannot diagnose, pivot to safe lifestyle / Ayurvedic tips.
2. MEMORY RELEVANCE: Use Relevant Past History only if it naturally helps answer the current question.
3. CITATION INTEGRITY: Never invent URLs. If search does not verify, say: "I do not have verified information on this specific topic."
4. UNIFIED SAFETY: Check the HealthProfile for medications before discussing any herb/supplement.

{search_protocol}

{env_block}You must return JSON with this exact schema:
{{"response_text": "...", "citations": [{{"source_name": "Name", "url": "URL"}}]}}

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


class GeminiLLMGateway:
    """Concrete LLM gateway. Implements `LLMGateway` protocol."""

    def __init__(
        self,
        *,
        api_key: str | None = None,
        model: str | None = None,
        embedding_model: str | None = None,
    ) -> None:
        key = (api_key or settings.gemini_api_key or "").strip()
        if not key:
            raise ConfigurationError(
                "GEMINI_API_KEY is not set. Add GEMINI_API_KEY to backend/.env, or use Groq: "
                "set LLM_PROVIDER=groq and GROQ_API_KEY there, then restart the API."
            )
        self._client = genai.Client(api_key=key)
        self._model = model or settings.gemini_model
        self._embed_model = embedding_model or settings.gemini_embedding_model

    def embed(self, text: str) -> list[float]:
        try:
            emb = self._client.models.embed_content(
                model=self._embed_model,
                contents=[text],
                config=types.EmbedContentConfig(output_dimensionality=_EMBEDDING_DIM),
            )
            if not emb.embeddings or not emb.embeddings[0].values:
                return []
            vec = list(emb.embeddings[0].values)
            return vec if len(vec) == _EMBEDDING_DIM else []
        except APIError as exc:
            logger.warning("Gemini embedding failed: %s", exc)
            return []

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
                "ENVIRONMENT & DESHA: Tailor suggestions to the environment. Stay non-diagnostic.\n\n"
            )
        else:
            env_block = (
                "ENVIRONMENT & DESHA: If the user describes their environment, tailor suggestions "
                "accordingly. No environment data was provided for this turn.\n\n"
            )

        system = _CHAT_SYSTEM_TEMPLATE.format(
            search_protocol=_STRICT_SEARCH_PROTOCOL,
            env_block=env_block,
            profile_blob=profile_blob_json,
        )

        payload = (
            f"User latest message:\n{user_message}\n\n"
            f"Immediate Context (chronological):\n{recent_history_block}\n\n"
            f"Relevant Past History (semantic, only if useful):\n{semantic_history_block}"
        )

        content = types.Content(role="user", parts=[types.Part.from_text(text=payload)])
        search_tool = types.Tool(google_search=types.GoogleSearch())
        config = types.GenerateContentConfig(
            system_instruction=system,
            tools=[search_tool],
        )

        try:
            response = self._client.models.generate_content(
                model=self._model, contents=[content], config=config
            )
        except APIError as exc:
            logger.warning("Gemini with search failed; retrying without tools: %s", exc)
            fallback_system = system + (
                "\n\nNOTE: Live web search is unavailable for this turn. Return citations as empty "
                "unless you are citing retrieved tool output; never invent URLs."
            )
            try:
                response = self._client.models.generate_content(
                    model=self._model,
                    contents=[content],
                    config=types.GenerateContentConfig(system_instruction=fallback_system),
                )
            except APIError as exc2:
                raise ExternalServiceError(
                    "The assistant could not reach the AI service. Please try again shortly."
                ) from exc2

        try:
            raw = (response.text or "").strip()
        except Exception:
            raw = ""

        parsed = _safe_json(raw)

        grounding_urls: list[str] = []
        queries: list[str] = []
        grounding_names: dict[str, str] = {}
        if response.candidates:
            cand = response.candidates[0]
            meta = cand.grounding_metadata
            if meta:
                queries = list(meta.web_search_queries or [])
                for chunk in meta.grounding_chunks or []:
                    web = chunk.web
                    if web and web.uri and web.uri not in grounding_names:
                        grounding_names[web.uri] = web.title or web.uri
                        grounding_urls.append(web.uri)

        trusted: list[Citation] = []
        for url in grounding_urls:
            if _url_trusted(url):
                trusted.append(Citation(url=url, title=grounding_names.get(url, url)))

        response_text = parsed.get("response_text") if isinstance(parsed.get("response_text"), str) else raw
        response_text = (response_text or "").strip()
        if grounding_urls and not trusted:
            response_text = _VERIFICATION_FALLBACK
        else:
            response_text = _strip_untrusted_urls(response_text)

        return GroundedReply(
            reply_text=response_text,
            citations=tuple(trusted),
            search_queries=tuple(queries),
        )

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
        return self._generate_text(system=_WEEKLY_PLAN_SYSTEM, user_text=user_content)

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
        return self._generate_text(system=_FOLLOWUP_SYSTEM, user_text=user_content)

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
        return self._generate_text(system=_TIP_SYSTEM, user_text=user_content)

    def _generate_text(self, *, system: str, user_text: str) -> str:
        content = types.Content(role="user", parts=[types.Part.from_text(text=user_text)])
        config = types.GenerateContentConfig(system_instruction=system)
        try:
            response = self._client.models.generate_content(
                model=self._model, contents=[content], config=config
            )
        except APIError as exc:
            raise ExternalServiceError(f"LLM call failed: {exc}") from exc
        try:
            return (response.text or "").strip()
        except Exception:
            return ""
