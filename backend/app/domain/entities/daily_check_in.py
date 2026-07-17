from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum


class SleepQuality(str, Enum):
    HEAVY = "heavy"
    RESTLESS = "restless"
    REFRESHED = "refreshed"


class Digestion(str, Enum):
    BLOATED = "bloated"
    ACIDIC = "acidic"
    CALM = "calm"


class EnergyState(str, Enum):
    WIRED = "wired"
    GROUNDED = "grounded"
    SLUGGISH = "sluggish"


class MovementLevel(str, Enum):
    REST = "rest"
    LIGHT = "light"
    SWEAT = "sweat"


@dataclass(slots=True)
class DailyCheckIn:
    """A one-day wellness snapshot. Unique per (user, date)."""

    id: uuid.UUID
    user_id: uuid.UUID
    check_in_date: date
    sleep_quality: SleepQuality
    digestion: Digestion
    energy_state: EnergyState
    movement: MovementLevel
    water_glasses: int
    timestamp: datetime | None = None
    mood_score: int | None = None
    notes: str | None = None

    def __post_init__(self) -> None:
        if self.water_glasses < 0:
            raise ValueError("water_glasses cannot be negative")
        if self.mood_score is not None and not (1 <= self.mood_score <= 5):
            raise ValueError("mood_score must be between 1 and 5")
