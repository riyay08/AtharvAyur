from __future__ import annotations

from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


SleepQualityLiteral = Literal["heavy", "restless", "refreshed"]
DigestionLiteral = Literal["bloated", "acidic", "calm"]
EnergyStateLiteral = Literal["wired", "grounded", "sluggish"]
MovementLiteral = Literal["rest", "light", "sweat"]


class DailyCheckInCreate(BaseModel):
    check_in_date: date | None = Field(
        default=None,
        description="Calendar date; defaults to today (server date).",
    )
    sleep_quality: SleepQualityLiteral
    digestion: DigestionLiteral
    energy_state: EnergyStateLiteral
    movement: MovementLiteral
    water_glasses: int = Field(ge=0, le=24)


class DailyCheckInOut(BaseModel):
    id: UUID
    check_in_date: date
    sleep_quality: str
    digestion: str
    energy_state: str
    movement: str
    water_glasses: int
    timestamp: datetime | None = None


class DailyCheckInWeekSlot(BaseModel):
    check_in_date: date
    record: DailyCheckInOut | None = None


class DailyCheckInWeekResponse(BaseModel):
    days: list[DailyCheckInWeekSlot]
