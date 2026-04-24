"""Pure rules for merging onboarding quiz data into a HealthProfile."""

from __future__ import annotations

from typing import Any


def merge_prakriti_into_conditions(
    existing_conditions: Any,
    prakriti_payload: dict[str, Any],
) -> dict[str, Any] | list[Any]:
    """Merge the prakriti quiz into `conditions` without destroying existing data.

    - If existing is a dict, add/overwrite only the `prakriti_quiz` key.
    - If existing is a list or scalar, preserve it under `prior_conditions`.
    - If existing is None, start fresh with `{ "prakriti_quiz": ... }`.
    """
    if isinstance(existing_conditions, dict):
        return {**existing_conditions, "prakriti_quiz": prakriti_payload}
    if existing_conditions is None:
        return {"prakriti_quiz": prakriti_payload}
    return {"prior_conditions": existing_conditions, "prakriti_quiz": prakriti_payload}
