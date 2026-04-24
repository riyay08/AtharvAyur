from __future__ import annotations

import uuid
from datetime import date

import pytest

from app.application.dtos import UpsertProfileInput
from app.application.use_cases.profile import GetProfileMe, UpsertProfile
from app.domain.entities import HealthProfile, User
from app.domain.errors import NotFoundError
from tests.fakes import (
    FakeAuditLogRepository,
    FakeCheckInRepository,
    FakeClock,
    FakeHealthProfileRepository,
    FakeUnitOfWork,
    FakeUserRepository,
    FakeWeeklyPlanRepository,
)


def test_upsert_profile_creates_new_profile_with_prakriti() -> None:
    user = User.new()
    users = FakeUserRepository([user])
    profiles = FakeHealthProfileRepository()
    audit = FakeAuditLogRepository()
    uow = FakeUnitOfWork()
    uc = UpsertProfile(users=users, profiles=profiles, audit=audit, uow=uow)

    out = uc.execute(
        UpsertProfileInput(
            user_id=user.id,
            prakriti_payload={"primary_dosha": "vata"},
            allergies=["peanut"],
        )
    )

    stored = profiles.get_by_user_id(user.id)
    assert stored is not None
    assert stored.conditions == {"prakriti_quiz": {"primary_dosha": "vata"}}
    assert stored.allergies == ["peanut"]
    assert out.health_profile_id == stored.id
    assert uow.commits == 1


def test_upsert_profile_preserves_existing_fields_when_unset() -> None:
    user = User.new()
    existing = HealthProfile(
        id=uuid.uuid4(),
        user_id=user.id,
        conditions={"diabetes": True},
        allergies=["shellfish"],
        medications=["metformin"],
    )
    users = FakeUserRepository([user])
    profiles = FakeHealthProfileRepository()
    profiles.upsert(existing)
    audit = FakeAuditLogRepository()
    uow = FakeUnitOfWork()
    uc = UpsertProfile(users=users, profiles=profiles, audit=audit, uow=uow)

    uc.execute(
        UpsertProfileInput(
            user_id=user.id,
            prakriti_payload={"primary_dosha": "kapha"},
        )
    )

    stored = profiles.get_by_user_id(user.id)
    assert stored.allergies == ["shellfish"]
    assert stored.medications == ["metformin"]
    assert stored.conditions == {
        "diabetes": True,
        "prakriti_quiz": {"primary_dosha": "kapha"},
    }


def test_upsert_profile_raises_when_user_missing() -> None:
    users = FakeUserRepository()
    uc = UpsertProfile(
        users=users,
        profiles=FakeHealthProfileRepository(),
        audit=FakeAuditLogRepository(),
        uow=FakeUnitOfWork(),
    )
    with pytest.raises(NotFoundError):
        uc.execute(UpsertProfileInput(user_id=uuid.uuid4()))


def test_upsert_profile_explicit_none_clears_allergies() -> None:
    user = User.new()
    existing = HealthProfile(
        id=uuid.uuid4(),
        user_id=user.id,
        allergies=["peanut"],
    )
    profiles = FakeHealthProfileRepository()
    profiles.upsert(existing)
    uc = UpsertProfile(
        users=FakeUserRepository([user]),
        profiles=profiles,
        audit=FakeAuditLogRepository(),
        uow=FakeUnitOfWork(),
    )
    uc.execute(UpsertProfileInput(user_id=user.id, allergies=None))
    assert profiles.get_by_user_id(user.id).allergies is None


def test_get_profile_me_returns_empty_when_no_profile_or_plan() -> None:
    user = User.new()
    uc = GetProfileMe(
        users=FakeUserRepository([user]),
        profiles=FakeHealthProfileRepository(),
        check_ins=FakeCheckInRepository(),
        plans=FakeWeeklyPlanRepository(),
        clock=FakeClock(today=date(2026, 4, 22)),
    )
    out = uc.execute(user_id=user.id)
    assert out.health_profile is None
    assert out.current_plan is None
    assert out.latest_check_in is None


def test_get_profile_me_raises_when_user_missing() -> None:
    uc = GetProfileMe(
        users=FakeUserRepository(),
        profiles=FakeHealthProfileRepository(),
        check_ins=FakeCheckInRepository(),
        plans=FakeWeeklyPlanRepository(),
        clock=FakeClock(today=date(2026, 4, 22)),
    )
    with pytest.raises(NotFoundError):
        uc.execute(user_id=uuid.uuid4())
