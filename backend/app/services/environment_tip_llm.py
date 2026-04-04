"""Single-shot Gemini call for cached daily environment tips (no search tool)."""

from __future__ import annotations

import json
import logging
import re

from google import genai
from google.genai import types
from google.genai.errors import APIError

from app.config import settings

logger = logging.getLogger(__name__)

TIP_SYSTEM = """You output only valid JSON for a wellness app. No markdown fences.
The tip must be non-diagnostic, safe, and grounded in general Ayurvedic lifestyle education.
icon_name must be one of: leaf, building, droplets, sun, cloud, wind, sparkles (lowercase)."""


def build_fallback_environment_tip(
    dominant_dosha: str,
    environment_context: dict[str, str],
) -> dict[str, str]:
    """Deterministic tip when Gemini is unavailable (quota, outage, parse errors)."""
    weather = environment_context.get("weather", "today's conditions")
    hum = environment_context.get("humidity_type", "balanced")
    hab = environment_context.get("habitat", "Rural")
    dosha = dominant_dosha if dominant_dosha and dominant_dosha != "unknown" else "your dosha balance"

    if hab == "Urban":
        return {
            "tip_title": "City pace & steady nerves",
            "tip_description": (
                f"Dense urban rhythm can aggravate Vata-like restlessness. For {dosha}, take two minutes of "
                "slow breathing by a window or tree, soften visual noise, and choose one warm, cooked meal today."
            ),
            "icon_name": "building",
        }
    if hum == "dry":
        return {
            "tip_title": "Dry air, warm grounding",
            "tip_description": (
                f"{weather} suggests dry qualities in the environment. Favor warm fluids, nose-friendly steam "
                f"(not too hot), and light self-massage with oil you tolerate—supporting {dosha} without harsh heat."
            ),
            "icon_name": "droplets",
        }
    if hum == "damp":
        return {
            "tip_title": "Damp day, light & warm",
            "tip_description": (
                f"Heavy or damp air pairs best with warm, well-spiced, easy-to-digest foods and brisk walking. "
                f"Keep {dosha} comfortable by avoiding cold, soggy snacks and sitting too long."
            ),
            "icon_name": "cloud",
        }
    return {
        "tip_title": f"Sync with {weather.split(',')[0] if weather else 'today'}",
        "tip_description": (
            f"Match your day to {weather}. Steady meal times, hydration, and gentle movement usually support "
            f"{dosha}; adjust intensity if you feel overheated or chilled."
        ),
        "icon_name": "leaf",
    }


def _strip_json_fence(text: str) -> str:
    t = text.strip()
    m = re.match(r"^```(?:json)?\s*([\s\S]*?)\s*```$", t, re.IGNORECASE)
    if m:
        return m.group(1).strip()
    return t


def synthesize_daily_environment_tip(
    *,
    dominant_dosha: str,
    environment_context: dict[str, str],
    api_key: str | None = None,
    model: str | None = None,
) -> dict[str, str]:
    key = (api_key or settings.gemini_api_key or "").strip()
    if not key:
        logger.warning("GEMINI_API_KEY missing; using fallback environment tip.")
        return build_fallback_environment_tip(dominant_dosha, environment_context)

    model_id = model or settings.gemini_model
    client = genai.Client(api_key=key)

    user_prompt = (
        f"Based on the user's Dosha ({dominant_dosha}) and current environment "
        f"(weather summary: {environment_context.get('weather', '')}; "
        f"humidity tendency: {environment_context.get('humidity_type', '')}; "
        f"habitat: {environment_context.get('habitat', '')}), "
        "generate ONE short, highly actionable Ayurvedic lifestyle tip for today.\n"
        'Output JSON with exactly these keys: "tip_title", "tip_description", "icon_name".\n'
        "tip_title: max 8 words, catchy.\n"
        "tip_description: 1-3 sentences, specific and practical.\n"
        "icon_name: one of the allowed icon names from the system message."
    )

    config = types.GenerateContentConfig(
        system_instruction=TIP_SYSTEM,
        temperature=0.6,
        response_mime_type="application/json",
    )

    try:
        response = client.models.generate_content(
            model=model_id,
            contents=[
                types.Content(
                    role="user",
                    parts=[types.Part.from_text(text=user_prompt)],
                )
            ],
            config=config,
        )
    except APIError as exc:
        logger.warning("Gemini daily tip API error (%s); using fallback.", exc)
        return build_fallback_environment_tip(dominant_dosha, environment_context)

    raw = (response.text or "").strip()
    if not raw:
        logger.warning("Gemini returned empty tip; using fallback.")
        return build_fallback_environment_tip(dominant_dosha, environment_context)

    try:
        parsed = json.loads(_strip_json_fence(raw))
    except json.JSONDecodeError:
        logger.warning("Tip JSON parse failed: %s", raw[:200])
        return build_fallback_environment_tip(dominant_dosha, environment_context)

    if not isinstance(parsed, dict):
        return build_fallback_environment_tip(dominant_dosha, environment_context)

    title = parsed.get("tip_title")
    desc = parsed.get("tip_description")
    icon = parsed.get("icon_name")
    if not isinstance(title, str) or not title.strip():
        return build_fallback_environment_tip(dominant_dosha, environment_context)
    if not isinstance(desc, str) or not desc.strip():
        return build_fallback_environment_tip(dominant_dosha, environment_context)
    if not isinstance(icon, str) or not icon.strip():
        icon = "sparkles"

    allowed = {"leaf", "building", "droplets", "sun", "cloud", "wind", "sparkles"}
    icon_norm = icon.strip().lower()
    if icon_norm not in allowed:
        icon_norm = "sparkles"

    return {
        "tip_title": title.strip()[:512],
        "tip_description": desc.strip()[:2000],
        "icon_name": icon_norm,
    }
