from __future__ import annotations

import enum
from datetime import date, datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, BeforeValidator, Field


def _enum_to_str(v):  # type: ignore[no-untyped-def]
    if isinstance(v, enum.Enum):
        return v.value
    return v


StrFromEnum = Annotated[str, BeforeValidator(_enum_to_str)]


SleepQualityLiteral = Literal["heavy", "restless", "refreshed"]
DigestionLiteral = Literal["bloated", "acidic", "calm"]
EnergyStateLiteral = Literal["wired", "grounded", "sluggish"]
MovementLiteral = Literal["rest", "light", "sweat"]


class DailyCheckInCreate(BaseModel):
    user_id: UUID
    check_in_date: date | None = Field(
        default=None,
        description="Calendar date for this check-in; defaults to today (server date).",
    )
    sleep_quality: SleepQualityLiteral
    digestion: DigestionLiteral
    energy_state: EnergyStateLiteral
    movement: MovementLiteral
    water_glasses: int = Field(ge=0, le=24)


class DailyCheckInOut(BaseModel):
    id: UUID
    user_id: UUID
    check_in_date: date
    sleep_quality: StrFromEnum
    digestion: StrFromEnum
    energy_state: StrFromEnum
    movement: StrFromEnum
    water_glasses: int
    timestamp: datetime

    model_config = {"from_attributes": True}


class DailyCheckInWeekSlot(BaseModel):
    """One calendar day in the rolling 7-day window (oldest → newest)."""

    check_in_date: date
    record: DailyCheckInOut | None = None


class DailyCheckInWeekResponse(BaseModel):
    days: list[DailyCheckInWeekSlot]
