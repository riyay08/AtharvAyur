from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, Field


class ProfileUpsertRequest(BaseModel):
    region: str | None = Field(default=None, max_length=255)
    consent_flags: dict[str, Any] | list[Any] | None = None
    conditions: dict[str, Any] | list[Any] | None = None
    allergies: dict[str, Any] | list[Any] | None = None
    medications: dict[str, Any] | list[Any] | None = None
    prakriti_quiz: dict[str, Any] | None = Field(
        default=None,
        description="Dosha onboarding payload from the React quiz.",
    )


class ProfileUpsertResponse(BaseModel):
    user_id: uuid.UUID
    health_profile_id: uuid.UUID


class HealthProfileOut(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    conditions: dict[str, Any] | list[Any] | None = None
    allergies: dict[str, Any] | list[Any] | None = None
    medications: dict[str, Any] | list[Any] | None = None


class CheckInLiteOut(BaseModel):
    check_in_date: date
    sleep_quality: str
    digestion: str
    energy_state: str
    movement: str
    water_glasses: int


class WeeklyPlanLiteOut(BaseModel):
    id: uuid.UUID
    start_date: date
    tasks: dict[str, Any] | list[Any]


class ProfileMeResponse(BaseModel):
    user_id: uuid.UUID
    region: str | None = None
    consent_flags: dict[str, Any] | list[Any] | None = None
    health_profile: HealthProfileOut | None = None
    latest_checkin: CheckInLiteOut | None = None
    active_weekly_plan: WeeklyPlanLiteOut | None = None
