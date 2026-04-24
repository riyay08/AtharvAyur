"""Deterministic safety screening. Runs before any LLM call.

Takes a plain `HealthProfile` entity (not an ORM row) and a user message. No DB,
no HTTP, no SDKs — only regex + constants.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from app.domain.entities.health_profile import HealthProfile
from app.domain.value_objects import SafetyBlockReason


_RED_FLAG_PHRASES: tuple[str, ...] = (
    "chest pain",
    "crushing chest",
    "pain in my chest",
    "shortness of breath",
    "can't breathe",
    "cannot breathe",
    "trouble breathing",
    "difficulty breathing",
    "suicide",
    "suicidal",
    "kill myself",
    "end my life",
    "want to die",
    "self-harm",
    "self harm",
    "hurt myself",
    "severe bleeding",
    "coughing up blood",
    "stroke",
    "face drooping",
    "slurred speech",
    "worst headache of my life",
)

_RED_FLAG_WORDS: tuple[str, ...] = (
    "overdose",
    "seizure",
    "anaphylaxis",
    "unconscious",
)

_BLOOD_THINNER_MARKERS: tuple[str, ...] = (
    "warfarin",
    "coumadin",
    "apixaban",
    "eliquis",
    "rivaroxaban",
    "xarelto",
    "dabigatran",
    "pradaxa",
    "clopidogrel",
    "plavix",
    "prasugrel",
    "effient",
    "ticagrelor",
    "brilinta",
    "aspirin",
    "blood thinner",
    "anticoagulant",
    "antiplatelet",
)

_CONTRAINDICATION_SUBSTANCES: tuple[str, ...] = (
    "ginger",
    "ginkgo",
    "ginkgo biloba",
    "garlic supplement",
    "vitamin e",
    "fish oil",
    "omega-3",
    "omega 3",
    "turmeric supplement",
    "curcumin",
)

EMERGENCY_MESSAGE = (
    "Your message may describe a medical emergency or crisis. "
    "HolisticAI Health is not for emergencies and cannot diagnose or triage. "
    "If you or someone else may be in danger, call your local emergency number "
    "(for example, 911 in the U.S.) or go to the nearest emergency department now. "
    "If you are thinking about harming yourself, contact a crisis line or emergency services immediately."
)

CONTRAINDICATION_MESSAGE = (
    "Your health profile lists medications that can affect bleeding or clotting, and your message "
    "mentions supplements or substances that may interact with those medications. "
    "This app cannot provide personalized advice on herbs, supplements, or dosing. "
    "Please speak with your prescribing clinician or a pharmacist before starting, stopping, or "
    "combining supplements with prescription or over-the-counter drugs."
)


@dataclass(frozen=True, slots=True)
class SafetyResult:
    allowed: bool
    reason: SafetyBlockReason
    escalation_message: str | None
    matched_terms: tuple[str, ...]


def _normalize(text: str) -> str:
    return " ".join(text.lower().split())


def _json_to_search_text(value: Any) -> str:
    """Flatten nested JSON into a single searchable string."""
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


def _profile_to_search_text(profile: HealthProfile | None) -> str:
    if profile is None:
        return ""
    chunks = (
        _json_to_search_text(profile.conditions),
        _json_to_search_text(profile.allergies),
        _json_to_search_text(profile.medications),
    )
    return _normalize(" ".join(chunks))


def _find_red_flags(text: str) -> list[str]:
    normalized = _normalize(text)
    matched: list[str] = []
    for phrase in _RED_FLAG_PHRASES:
        if phrase in normalized:
            matched.append(phrase)
    for word in _RED_FLAG_WORDS:
        if re.search(rf"\b{re.escape(word)}\b", normalized) is not None:
            matched.append(word)
    return matched


def _profile_suggests_bleeding_related_meds(profile_text: str) -> bool:
    if not profile_text:
        return False
    return any(marker in profile_text for marker in _BLOOD_THINNER_MARKERS)


def _find_contraindication_substances(message_text: str) -> list[str]:
    normalized = _normalize(message_text)
    return [s for s in _CONTRAINDICATION_SUBSTANCES if s in normalized]


def evaluate_message(
    user_message: str,
    *,
    health_profile: HealthProfile | None = None,
) -> SafetyResult:
    """Deterministic safety check. When `allowed` is False the caller MUST NOT call the LLM.

    Evaluation order:
      1. Red-flag / crisis language in the user message.
      2. Anticoagulant profile × supplement contraindication in the message.
    """
    if not user_message or not user_message.strip():
        return SafetyResult(
            allowed=True,
            reason=SafetyBlockReason.NONE,
            escalation_message=None,
            matched_terms=(),
        )

    red = _find_red_flags(user_message)
    if red:
        return SafetyResult(
            allowed=False,
            reason=SafetyBlockReason.EMERGENCY_OR_RED_FLAG,
            escalation_message=EMERGENCY_MESSAGE,
            matched_terms=tuple(sorted(set(red))),
        )

    profile_text = _profile_to_search_text(health_profile)
    if _profile_suggests_bleeding_related_meds(profile_text):
        contra = _find_contraindication_substances(user_message)
        if contra:
            return SafetyResult(
                allowed=False,
                reason=SafetyBlockReason.CONTRAINDICATION,
                escalation_message=CONTRAINDICATION_MESSAGE,
                matched_terms=tuple(sorted(set(contra))),
            )

    return SafetyResult(
        allowed=True,
        reason=SafetyBlockReason.NONE,
        escalation_message=None,
        matched_terms=(),
    )
