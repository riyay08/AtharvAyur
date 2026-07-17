"""Pure extraction of structured Vata/Pitta/Kapha scores from a prakriti quiz payload.

The onboarding quiz produces raw per-answer counts, not percentages — see
`src/models/quizScoring.js` (`buildAssessment` increments one dosha's score per
matching answer). `health_profiles.{vata,pitta,kapha}_score` cache that value so
it can be queried without parsing the `conditions` JSON blob; the JSON remains
the source of truth.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class DoshaScores:
    vata: int | None
    pitta: int | None
    kapha: int | None


def extract_dosha_scores(prakriti_payload: dict[str, Any] | None) -> DoshaScores:
    """Read `dosha_distribution.{vata,pitta,kapha}` off a prakriti quiz payload.

    Returns all-None if the payload is missing or malformed — callers should treat
    that as "no score available", not an error.
    """
    if not isinstance(prakriti_payload, dict):
        return DoshaScores(vata=None, pitta=None, kapha=None)
    distribution = prakriti_payload.get("dosha_distribution")
    if not isinstance(distribution, dict):
        return DoshaScores(vata=None, pitta=None, kapha=None)

    def _as_int(value: Any) -> int | None:
        return value if isinstance(value, int) and not isinstance(value, bool) else None

    return DoshaScores(
        vata=_as_int(distribution.get("vata")),
        pitta=_as_int(distribution.get("pitta")),
        kapha=_as_int(distribution.get("kapha")),
    )
