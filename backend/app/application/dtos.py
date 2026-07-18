"""Use-case Input/Output DTOs (framework-free).

These are what use cases accept and return. Interface-layer Pydantic schemas map
into/out of these. Using plain dataclasses keeps the application layer independent
of Pydantic/FastAPI.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any

from app.domain.value_objects import Citation


# ---------- Auth ----------


@dataclass(frozen=True, slots=True)
class IssueTokenInput:
    user_id: uuid.UUID | None = None


@dataclass(frozen=True, slots=True)
class AuthSessionView:
    """What a successful auth call returns to the interface layer."""

    user_id: uuid.UUID
    access_token: str
    token_type: str
    email: str | None
    phone: str | None
    display_name: str | None
    primary_provider: str
    email_verified: bool
    phone_verified: bool
    has_password: bool
    has_passkey: bool
    is_new_user: bool = False


@dataclass(frozen=True, slots=True)
class IssueTokenOutput:
    access_token: str
    token_type: str
    user_id: uuid.UUID


@dataclass(frozen=True, slots=True)
class SignUpWithEmailInput:
    email: str
    password: str
    display_name: str | None = None
    anonymous_user_id: uuid.UUID | None = None


@dataclass(frozen=True, slots=True)
class LogInWithEmailInput:
    email: str
    password: str


@dataclass(frozen=True, slots=True)
class RequestPhoneOtpInput:
    phone: str


@dataclass(frozen=True, slots=True)
class RequestPhoneOtpOutput:
    phone: str
    expires_at: datetime
    dev_code: str | None = None


@dataclass(frozen=True, slots=True)
class VerifyPhoneOtpInput:
    phone: str
    code: str
    display_name: str | None = None
    anonymous_user_id: uuid.UUID | None = None


@dataclass(frozen=True, slots=True)
class SignInWithGoogleInput:
    id_token: str
    anonymous_user_id: uuid.UUID | None = None


@dataclass(frozen=True, slots=True)
class PasskeyRegisterStartInput:
    user_id: uuid.UUID


@dataclass(frozen=True, slots=True)
class PasskeyChallengeView:
    options: Any
    challenge_b64: str


@dataclass(frozen=True, slots=True)
class PasskeyRegisterFinishInput:
    user_id: uuid.UUID
    challenge_b64: str
    response: Any
    label: str | None = None


@dataclass(frozen=True, slots=True)
class PasskeyLoginStartInput:
    email: str | None = None


@dataclass(frozen=True, slots=True)
class PasskeyLoginFinishInput:
    challenge_b64: str
    response: Any


@dataclass(frozen=True, slots=True)
class AuthenticatedUserView:
    user_id: uuid.UUID
    email: str | None
    phone: str | None
    display_name: str | None
    primary_provider: str
    email_verified: bool
    phone_verified: bool
    has_password: bool
    passkey_count: int


# ---------- Profile ----------


# Sentinel for "field not provided" — distinct from explicit None.
# Exposed as `UpsertProfileInput.UNSET` for use-case callers.
class _Unset:
    _instance = None

    def __new__(cls) -> "_Unset":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __repr__(self) -> str:
        return "UNSET"


_UNSET = _Unset()


@dataclass(frozen=True, slots=True)
class UpsertProfileInput:
    user_id: uuid.UUID
    region: Any = _UNSET
    consent_flags: Any = _UNSET
    conditions: Any = _UNSET
    allergies: Any = _UNSET
    medications: Any = _UNSET
    prakriti_payload: dict[str, Any] | None = None

    UNSET = _UNSET

    @staticmethod
    def is_unset(v: Any) -> bool:
        return v is _UNSET


@dataclass(frozen=True, slots=True)
class HealthProfileView:
    id: uuid.UUID
    conditions: Any
    allergies: Any
    medications: Any


@dataclass(frozen=True, slots=True)
class UpsertProfileOutput:
    user_id: uuid.UUID
    health_profile: HealthProfileView
    health_profile_id: uuid.UUID


@dataclass(frozen=True, slots=True)
class CheckInLiteView:
    check_in_date: date
    sleep_quality: str
    digestion: str
    energy_state: str
    movement: str
    water_glasses: int


@dataclass(frozen=True, slots=True)
class WeeklyPlanView:
    id: uuid.UUID
    start_date: date
    tasks: Any


@dataclass(frozen=True, slots=True)
class GetProfileMeOutput:
    user_id: uuid.UUID
    health_profile: HealthProfileView | None
    latest_check_in: CheckInLiteView | None
    current_plan: WeeklyPlanView | None


# ---------- Check-in ----------


@dataclass(frozen=True, slots=True)
class UpsertCheckInInput:
    user_id: uuid.UUID
    check_in_date: date
    sleep_quality: str
    digestion: str
    energy_state: str
    movement: str
    water_glasses: int


@dataclass(frozen=True, slots=True)
class CheckInView:
    id: uuid.UUID
    check_in_date: date
    sleep_quality: str
    digestion: str
    energy_state: str
    movement: str
    water_glasses: int
    timestamp: datetime | None


@dataclass(frozen=True, slots=True)
class GetCheckInWeekInput:
    user_id: uuid.UUID
    end_date: date | None = None


@dataclass(frozen=True, slots=True)
class CheckInWeekSlotView:
    date: date
    check_in: CheckInView | None


@dataclass(frozen=True, slots=True)
class GetCheckInWeekOutput:
    start_date: date
    end_date: date
    slots: list[CheckInWeekSlotView]


# ---------- Chat ----------


@dataclass(frozen=True, slots=True)
class GenerateHealthReplyInput:
    user_id: uuid.UUID
    message: str
    lat: float | None = None
    lon: float | None = None
    conversation_id: uuid.UUID | None = None
    """If set, resume this conversation (must belong to `user_id`). If omitted,
    a new `Conversation` is created and its id is returned on the output."""


@dataclass(frozen=True, slots=True)
class GenerateHealthReplyOutput:
    reply_text: str
    blocked: bool
    block_reason: str
    citations: tuple[Citation, ...] = ()
    search_queries: tuple[str, ...] = ()
    conversation_id: uuid.UUID | None = None


# ---------- Environment ----------


@dataclass(frozen=True, slots=True)
class GetOrCreateDailyTipInput:
    user_id: uuid.UUID
    lat: float
    lon: float


@dataclass(frozen=True, slots=True)
class DailyTipView:
    id: uuid.UUID
    tip_date: date
    tip_title: str
    tip_description: str
    icon_name: str
    created_at: datetime | None


# ---------- Plan ----------


@dataclass(frozen=True, slots=True)
class GenerateWeeklyPlanInput:
    user_id: uuid.UUID


@dataclass(frozen=True, slots=True)
class GetCurrentPlanInput:
    user_id: uuid.UUID


@dataclass(frozen=True, slots=True)
class UpdatePlanTaskInput:
    user_id: uuid.UUID
    day_index: int
    pillar: str
    task_id: int
    completed: bool
