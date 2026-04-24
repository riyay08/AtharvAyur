from __future__ import annotations

from datetime import date

import pytest

from app.domain.errors import ValidationError
from app.domain.services.plan_normalization import (
    extract_json_object,
    normalize_weekly_plan_payload,
    strip_code_fence,
)


def test_strip_code_fence_handles_plain_json() -> None:
    assert strip_code_fence('{"a": 1}') == '{"a": 1}'


def test_strip_code_fence_handles_json_fence() -> None:
    assert strip_code_fence('```json\n{"a": 1}\n```') == '{"a": 1}'


def test_strip_code_fence_handles_bare_fence() -> None:
    assert strip_code_fence('```\n{"a": 1}\n```') == '{"a": 1}'


def test_extract_json_object_from_chatter() -> None:
    text = 'Sure, here is your plan:\n{"daily_focus_message": "Hi", "days": []}\nThanks!'
    out = extract_json_object(text)
    assert out["daily_focus_message"] == "Hi"


def test_extract_json_object_raises_when_missing() -> None:
    with pytest.raises(ValidationError):
        extract_json_object("no json here at all")


def test_normalize_produces_seven_days() -> None:
    out = normalize_weekly_plan_payload({}, date(2026, 4, 20))
    assert len(out["days"]) == 7
    assert out["days"][0]["date"] == "2026-04-20"
    assert out["days"][6]["date"] == "2026-04-26"


def test_normalize_pads_missing_pillars_with_defaults() -> None:
    out = normalize_weekly_plan_payload({}, date(2026, 4, 20))
    for day in out["days"]:
        assert set(day["pillars"].keys()) == {"Mind", "Fuel", "Body"}
        for pillar_tasks in day["pillars"].values():
            assert len(pillar_tasks) == 1


def test_normalize_assigns_sequential_ids() -> None:
    out = normalize_weekly_plan_payload({}, date(2026, 4, 20))
    ids = [
        t["id"]
        for day in out["days"]
        for pillar_name in ("Mind", "Fuel", "Body")
        for t in day["pillars"][pillar_name]
    ]
    assert ids == list(range(1, len(ids) + 1))


def test_normalize_preserves_given_tasks() -> None:
    raw = {
        "daily_focus_message": "Focus week",
        "days": [
            {
                "date": "2026-04-20",
                "pillars": {
                    "Mind": [{"task": "Journal", "context_reason": "Clarity"}],
                    "Fuel": [{"task": "Soup", "context_reason": "Warm"}],
                    "Body": [{"task": "Walk", "context_reason": "Movement"}],
                },
            }
        ],
    }
    out = normalize_weekly_plan_payload(raw, date(2026, 4, 20))
    assert out["daily_focus_message"] == "Focus week"
    assert out["days"][0]["pillars"]["Mind"][0]["task"] == "Journal"


def test_normalize_caps_tasks_per_pillar() -> None:
    huge = [{"task": f"t{i}", "context_reason": "x"} for i in range(20)]
    raw = {
        "days": [{"date": "2026-04-20", "pillars": {"Mind": huge, "Fuel": [], "Body": []}}]
    }
    out = normalize_weekly_plan_payload(raw, date(2026, 4, 20))
    assert len(out["days"][0]["pillars"]["Mind"]) == 8


def test_normalize_accepts_pillar_case_variants() -> None:
    raw = {
        "days": [
            {
                "date": "2026-04-20",
                "pillars": {"mind": [{"task": "Breathe", "context_reason": "Calm"}]},
            }
        ]
    }
    out = normalize_weekly_plan_payload(raw, date(2026, 4, 20))
    assert out["days"][0]["pillars"]["Mind"][0]["task"] == "Breathe"
