from __future__ import annotations

from app.domain.services.outbound_guard import DISCLAIMER, guard_reply


def test_empty_reply_is_unchanged() -> None:
    result = guard_reply("")
    assert result.rewritten is False
    assert result.text == ""


def test_non_diagnostic_reply_is_unchanged() -> None:
    text = "Warm water and gentle movement can help with sluggish mornings."
    result = guard_reply(text)
    assert result.rewritten is False
    assert result.text == text
    assert result.matched_patterns == ()


def test_diagnostic_claim_is_softened_and_disclaimer_appended() -> None:
    result = guard_reply("You have irritable bowel syndrome.")
    assert result.rewritten is True
    assert "you have" not in result.text.lower()
    assert "you may be experiencing" in result.text.lower()
    assert DISCLAIMER in result.text


def test_diagnosed_with_phrase_is_softened() -> None:
    result = guard_reply("You are diagnosed with anxiety.")
    assert result.rewritten is True
    assert "diagnosed with" not in result.text.lower().split("some")[0]
    assert "some people with similar patterns are diagnosed with" in result.text.lower()


def test_disclaimer_not_duplicated_if_already_present() -> None:
    text = f"You have low energy today. {DISCLAIMER}"
    result = guard_reply(text)
    assert result.text.count(DISCLAIMER) == 1
