from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any

from app.domain.value_objects import Dosha


@dataclass(slots=True)
class HealthProfile:
    """User's health context. JSON-shaped fields for flexibility."""

    id: uuid.UUID
    user_id: uuid.UUID
    conditions: dict[str, Any] | list[Any] | None = None
    allergies: dict[str, Any] | list[Any] | None = None
    medications: dict[str, Any] | list[Any] | None = None

    @property
    def prakriti(self) -> dict[str, Any] | None:
        """Extract the onboarding dosha quiz payload from `conditions.prakriti_quiz`."""
        if isinstance(self.conditions, dict):
            value = self.conditions.get("prakriti_quiz")
            if isinstance(value, dict):
                return value
        return None

    @property
    def dominant_dosha(self) -> Dosha | None:
        prakriti = self.prakriti
        if prakriti is None:
            return None
        raw = prakriti.get("primary_dosha") or prakriti.get("dominant_dosha")
        if not isinstance(raw, str):
            return None
        try:
            return Dosha(raw.strip().lower())
        except ValueError:
            return None

    def merge_prakriti(
        self,
        prakriti: dict[str, Any],
    ) -> dict[str, Any] | list[Any]:
        """Return the new `conditions` value after merging a prakriti payload.

        Preserves prior structure: dict conditions get prakriti_quiz merged;
        non-dict conditions are moved under `prior_conditions` so we keep history.
        """
        if isinstance(self.conditions, dict):
            return {**self.conditions, "prakriti_quiz": prakriti}
        if self.conditions is None:
            return {"prakriti_quiz": prakriti}
        return {"prior_conditions": self.conditions, "prakriti_quiz": prakriti}
