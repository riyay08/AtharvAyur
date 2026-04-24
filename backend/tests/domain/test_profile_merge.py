from __future__ import annotations

from app.domain.services.profile_merge import merge_prakriti_into_conditions


PAYLOAD = {"primary_dosha": "vata", "score": {"vata": 5}}


def test_merge_into_none_starts_fresh() -> None:
    out = merge_prakriti_into_conditions(None, PAYLOAD)
    assert out == {"prakriti_quiz": PAYLOAD}


def test_merge_into_existing_dict_adds_key() -> None:
    existing = {"diabetes": True}
    out = merge_prakriti_into_conditions(existing, PAYLOAD)
    assert out == {"diabetes": True, "prakriti_quiz": PAYLOAD}


def test_merge_overwrites_existing_prakriti_quiz() -> None:
    existing = {"prakriti_quiz": {"primary_dosha": "kapha"}}
    out = merge_prakriti_into_conditions(existing, PAYLOAD)
    assert out == {"prakriti_quiz": PAYLOAD}


def test_merge_preserves_list_under_prior_conditions() -> None:
    existing = ["hypertension"]
    out = merge_prakriti_into_conditions(existing, PAYLOAD)
    assert out == {"prior_conditions": ["hypertension"], "prakriti_quiz": PAYLOAD}


def test_merge_preserves_scalar_under_prior_conditions() -> None:
    out = merge_prakriti_into_conditions("diabetic", PAYLOAD)
    assert out == {"prior_conditions": "diabetic", "prakriti_quiz": PAYLOAD}
