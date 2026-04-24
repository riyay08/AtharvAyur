from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date, datetime


@dataclass(slots=True)
class DailyEnvironmentTip:
    """Cached daily weather-driven tip (one per user per UTC day)."""

    id: uuid.UUID
    user_id: uuid.UUID
    tip_date: date
    tip_title: str
    tip_description: str
    icon_name: str
    created_at: datetime | None = None
