from __future__ import annotations

import uuid
from typing import Any

from pydantic import BaseModel, Field

from app.schemas.checkin import DailyCheckInOut
from app.schemas.plan import WeeklyPlanOut


class ProfileUpsertRequest(BaseModel):
    region: str | None = Field(default=None, max_length=255)
    consent_flags: dict[str, Any] | list[Any] | None = None
    conditions: dict[str, Any] | list[Any] | None = None
    allergies: dict[str, Any] | list[Any] | None = None
    medications: dict[str, Any] | list[Any] | None = None
    prakriti_quiz: dict[str, Any] | None = Field(
        default=None,
        description="Dosha onboarding payload from the React quiz (scores, primary_dosha, answers, etc.).",
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

    model_config = {"from_attributes": True}


class ProfileMeResponse(BaseModel):
    user_id: uuid.UUID
    region: str | None = None
    consent_flags: dict[str, Any] | list[Any] | None = None
    health_profile: HealthProfileOut | None = None
    latest_checkin: DailyCheckInOut | None = None
    active_weekly_plan: WeeklyPlanOut | None = None
