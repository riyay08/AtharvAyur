from __future__ import annotations

import uuid

from app.domain.entities import HealthProfile
from app.domain.services.safety_policy import evaluate_message
from app.domain.value_objects import SafetyBlockReason


def _profile(meds: list[str] | None = None) -> HealthProfile:
    return HealthProfile(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        medications=meds,
    )


def test_empty_message_is_allowed() -> None:
    assert evaluate_message("").allowed is True
    assert evaluate_message("   ").allowed is True


def test_normal_message_is_allowed() -> None:
    result = evaluate_message("I'd like tips for better sleep tonight.")
    assert result.allowed is True
    assert result.reason is SafetyBlockReason.NONE
    assert result.escalation_message is None


def test_red_flag_phrase_blocks_with_emergency_reason() -> None:
    result = evaluate_message("I have severe chest pain right now")
    assert result.allowed is False
    assert result.reason is SafetyBlockReason.EMERGENCY_OR_RED_FLAG
    assert result.escalation_message is not None
    assert "emergency" in result.escalation_message.lower()
    assert "chest pain" in result.matched_terms


def test_red_flag_word_blocks() -> None:
    result = evaluate_message("I think I had a seizure yesterday")
    assert result.allowed is False
    assert result.reason is SafetyBlockReason.EMERGENCY_OR_RED_FLAG
    assert "seizure" in result.matched_terms


def test_red_flag_takes_precedence_over_contraindication() -> None:
    profile = _profile(meds=["warfarin"])
    result = evaluate_message("I'm on warfarin and took ginger but now chest pain", health_profile=profile)
    assert result.allowed is False
    assert result.reason is SafetyBlockReason.EMERGENCY_OR_RED_FLAG


def test_anticoagulant_plus_supplement_blocks_as_contraindication() -> None:
    profile = _profile(meds=["warfarin 5mg daily"])
    result = evaluate_message("Should I add ginger tea to my routine?", health_profile=profile)
    assert result.allowed is False
    assert result.reason is SafetyBlockReason.CONTRAINDICATION
    assert "ginger" in result.matched_terms


def test_anticoagulant_without_supplement_is_allowed() -> None:
    profile = _profile(meds=["warfarin"])
    result = evaluate_message("Can you recommend meditation practices?", health_profile=profile)
    assert result.allowed is True


def test_supplement_without_anticoagulant_is_allowed() -> None:
    profile = _profile(meds=["tylenol"])
    result = evaluate_message("I drink turmeric supplement daily", health_profile=profile)
    assert result.allowed is True


def test_safety_is_case_insensitive() -> None:
    result = evaluate_message("CHEST PAIN right now")
    assert result.allowed is False


def test_safety_handles_missing_profile() -> None:
    result = evaluate_message("I'm taking ginger daily")
    assert result.allowed is True
