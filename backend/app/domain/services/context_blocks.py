"""Pure formatters that turn domain entities into LLM prompt context blocks.

Shared by `GenerateHealthReply` (legacy chat use case) and `ChatOrchestrator`
(v2.0) so both build identical profile/history blocks — no duplicated
prompt-formatting logic.
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.domain.entities import DailyCheckIn


def _conditions_without_quiz(conditions: Any) -> Any:
    """Strip the verbose `prakriti_quiz` object (all onboarding Q&A pairs) out
    of `conditions` before it reaches the LLM prompt.

    The quiz itself is NOT deleted anywhere — `HealthProfile.conditions` in the
    database/entity is untouched. This only affects what gets serialized into
    the prompt: the durable insight the quiz produced now lives in
    `dosha_summary` (structured scores) and, for anything beyond dosha, in the
    Long-Term Memory `user_memories` table — not in a raw JSON dump resent
    every single turn."""
    if isinstance(conditions, dict) and "prakriti_quiz" in conditions:
        return {k: v for k, v in conditions.items() if k != "prakriti_quiz"}
    return conditions


def _dosha_summary(profile: Any) -> dict[str, int | str | None]:
    """Compact replacement for the full `prakriti_quiz` blob: just the 3
    structured scores plus the single derived `dominant_dosha` label.

    `profile.dominant_dosha` still reads `conditions.prakriti_quiz` internally
    (see `HealthProfile.dominant_dosha`) to extract one string — it does not
    reintroduce the quiz's Q&A pairs into the prompt, and resolves to `None`
    gracefully if the quiz is missing/malformed."""
    dominant = getattr(profile, "dominant_dosha", None)
    return {
        "vata_score": getattr(profile, "vata_score", None),
        "pitta_score": getattr(profile, "pitta_score", None),
        "kapha_score": getattr(profile, "kapha_score", None),
        "dominant_dosha": dominant.value if dominant is not None else None,
    }


def build_profile_blob_json(profile: Any | None) -> str:
    """Serialize a `HealthProfile`'s clinical fields for the LLM prompt.

    `conditions` (minus the quiz), `allergies`, and `medications` are sent in
    full every turn — these are clinical safety requirements. The onboarding
    `prakriti_quiz` (every Q&A pair) is deliberately excluded in favor of the
    compact `dosha_summary`; see `_conditions_without_quiz`/`_dosha_summary`.
    """
    if profile is None:
        return "{}"
    payload = {
        "conditions": _conditions_without_quiz(profile.conditions),
        "allergies": profile.allergies,
        "medications": profile.medications,
        "dosha_summary": _dosha_summary(profile),
    }
    try:
        return json.dumps(payload, indent=2, default=str)
    except TypeError:
        return json.dumps(
            {
                "conditions": str(payload["conditions"]),
                "allergies": str(profile.allergies),
                "medications": str(profile.medications),
                "dosha_summary": payload["dosha_summary"],
            },
            indent=2,
        )


def build_history_block(messages: Any) -> str:
    """Chronological bullet list of message text, no role labels.

    Matches how `GenerateHealthReply` has always built recent/semantic blocks —
    callers pre-filter to the role they want (typically user-only)."""
    if not messages:
        return "No user messages in the last 7 days."
    chrono = sorted(messages, key=lambda m: m.timestamp or 0)
    return "\n".join(f"- {m.message}" for m in chrono)


def build_conversation_transcript(messages: Any) -> str:
    """Chronological, role-labeled transcript for resuming a specific conversation."""
    if not messages:
        return ""
    chrono = sorted(messages, key=lambda m: m.timestamp or 0)
    return "\n".join(f"{m.role.value}: {m.message}" for m in chrono)


def build_daily_checkin_block(check_in: DailyCheckIn | None) -> str:
    """Format the user's Daily Ritual (DailyCheckIn) for the LLM prompt.

    Returns an empty string when there is no check-in for the requested day —
    callers should omit the section entirely rather than sending a placeholder."""
    if check_in is None:
        return ""
    return (
        "Today's Daily Check-in:\n"
        f"- Date: {check_in.check_in_date}\n"
        f"- Sleep quality: {check_in.sleep_quality.value}\n"
        f"- Energy state: {check_in.energy_state.value}\n"
        f"- Digestion: {check_in.digestion.value}\n"
        f"- Movement: {check_in.movement.value}\n"
        f"- Hydration: {check_in.water_glasses} glasses of water"
    )


def build_known_user_facts_block(facts: Sequence[Any]) -> str:
    """Format semantically retrieved Long-Term Memory facts for the LLM prompt.

    Returns an empty string when there are no facts — callers should omit the
    section entirely rather than sending a placeholder."""
    if not facts:
        return ""
    lines: list[str] = []
    for fact in facts:
        text = fact.fact_text if hasattr(fact, "fact_text") else str(fact)
        text = text.strip()
        if text:
            lines.append(f"- {text}")
    if not lines:
        return ""
    return "Known User Facts:\n" + "\n".join(lines)
