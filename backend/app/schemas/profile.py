from __future__ import annotations

import uuid
from typing import Any

from pydantic import BaseModel, Field


class ProfileUpsertRequest(BaseModel):
    """
    Create or update a user and their health profile.
    Omit ``user_id`` to create a new user (UUID returned in the response).
    """

    user_id: uuid.UUID | None = Field(
        default=None,
        description="Existing user UUID. If omitted, a new user is created.",
    )
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
    created_user: bool = False
