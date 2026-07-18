from __future__ import annotations

import json
import uuid

from app.domain.entities import HealthProfile
from app.domain.entities import DailyCheckIn, Digestion, EnergyState, MovementLevel, SleepQuality
from app.domain.services.context_blocks import build_daily_checkin_block, build_profile_blob_json


def _profile(**overrides) -> HealthProfile:
    defaults: dict = dict(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        conditions=None,
        allergies=None,
        medications=None,
        vata_score=None,
        pitta_score=None,
        kapha_score=None,
    )
    defaults.update(overrides)
    return HealthProfile(**defaults)


def test_none_profile_returns_empty_json_object() -> None:
    assert build_profile_blob_json(None) == "{}"


def test_prakriti_quiz_qa_pairs_are_excluded_from_conditions() -> None:
    profile = _profile(
        conditions={
            "chronic": ["IBS"],
            "prakriti_quiz": {
                "primary_dosha": "vata",
                "dosha_distribution": {"vata": 40, "pitta": 35, "kapha": 25},
                "answers": [{"question": "How is your skin?", "answer": "dry"}] * 20,
            },
        },
        vata_score=40,
        pitta_score=35,
        kapha_score=25,
    )

    blob = build_profile_blob_json(profile)
    parsed = json.loads(blob)

    assert "prakriti_quiz" not in parsed["conditions"]
    assert parsed["conditions"] == {"chronic": ["IBS"]}
    assert "answers" not in blob
    assert "How is your skin?" not in blob


def test_dosha_summary_contains_scores_and_dominant_dosha() -> None:
    profile = _profile(
        conditions={"prakriti_quiz": {"primary_dosha": "pitta"}},
        vata_score=20,
        pitta_score=50,
        kapha_score=30,
    )

    blob = build_profile_blob_json(profile)
    parsed = json.loads(blob)

    assert parsed["dosha_summary"] == {
        "vata_score": 20,
        "pitta_score": 50,
        "kapha_score": 30,
        "dominant_dosha": "pitta",
    }


def test_dosha_summary_handles_missing_prakriti_quiz_gracefully() -> None:
    profile = _profile(conditions={"chronic": ["migraines"]}, vata_score=10, pitta_score=None, kapha_score=None)

    blob = build_profile_blob_json(profile)
    parsed = json.loads(blob)

    assert parsed["dosha_summary"] == {
        "vata_score": 10,
        "pitta_score": None,
        "kapha_score": None,
        "dominant_dosha": None,
    }
    # `conditions` without a quiz key is passed through untouched.
    assert parsed["conditions"] == {"chronic": ["migraines"]}


def test_dosha_summary_handles_null_conditions_gracefully() -> None:
    profile = _profile(conditions=None, vata_score=None, pitta_score=None, kapha_score=None)

    blob = build_profile_blob_json(profile)
    parsed = json.loads(blob)

    assert parsed["conditions"] is None
    assert parsed["dosha_summary"] == {
        "vata_score": None,
        "pitta_score": None,
        "kapha_score": None,
        "dominant_dosha": None,
    }


def test_allergies_and_medications_are_preserved_in_full() -> None:
    profile = _profile(
        allergies=["peanuts", "shellfish"],
        medications=[{"name": "metformin", "dose": "500mg"}],
    )

    blob = build_profile_blob_json(profile)
    parsed = json.loads(blob)

    assert parsed["allergies"] == ["peanuts", "shellfish"]
    assert parsed["medications"] == [{"name": "metformin", "dose": "500mg"}]


def test_output_is_indented_valid_json() -> None:
    profile = _profile(conditions={"prakriti_quiz": {"primary_dosha": "kapha"}}, kapha_score=60)

    blob = build_profile_blob_json(profile)

    assert "\n" in blob  # indent=2 produces multi-line output
    parsed = json.loads(blob)  # must not raise
    assert set(parsed.keys()) == {"conditions", "allergies", "medications", "dosha_summary"}


def test_non_serializable_conditions_falls_back_to_string_but_keeps_dosha_summary() -> None:
    # `json.dumps(..., default=str)` already stringifies most non-primitive
    # *values*; a non-string dict *key* is one of the few things it can't
    # coerce, which is what actually exercises the `except TypeError` fallback.
    profile = _profile(conditions={("weird", "key"): "value"}, vata_score=33)

    blob = build_profile_blob_json(profile)
    parsed = json.loads(blob)

    assert "weird" in parsed["conditions"]
    assert parsed["dosha_summary"]["vata_score"] == 33


def test_build_daily_checkin_block_returns_empty_string_for_none() -> None:
    assert build_daily_checkin_block(None) == ""


def test_build_daily_checkin_block_formats_all_biomarkers() -> None:
    from datetime import date

    check_in = DailyCheckIn(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        check_in_date=date(2026, 7, 17),
        sleep_quality=SleepQuality.REFRESHED,
        digestion=Digestion.CALM,
        energy_state=EnergyState.GROUNDED,
        movement=MovementLevel.LIGHT,
        water_glasses=5,
    )

    block = build_daily_checkin_block(check_in)

    assert block.startswith("Today's Daily Check-in:")
    assert "2026-07-17" in block
    assert "refreshed" in block
    assert "grounded" in block
    assert "calm" in block
    assert "light" in block
    assert "5 glasses of water" in block
