from __future__ import annotations

import uuid
from datetime import date

import pytest

from app.application.dtos import GetCheckInWeekInput, UpsertCheckInInput
from app.application.use_cases.checkin import GetCheckInWeek, UpsertCheckIn
from app.domain.errors import ValidationError
from tests.fakes import (
    FakeAuditLogRepository,
    FakeCheckInRepository,
    FakeClock,
    FakeUnitOfWork,
)


def _valid_input(user_id: uuid.UUID, d: date) -> UpsertCheckInInput:
    return UpsertCheckInInput(
        user_id=user_id,
        check_in_date=d,
        sleep_quality="refreshed",
        digestion="calm",
        energy_state="grounded",
        movement="light",
        water_glasses=8,
    )


def test_upsert_check_in_creates_new_row() -> None:
    user_id = uuid.uuid4()
    check_ins = FakeCheckInRepository()
    uc = UpsertCheckIn(check_ins=check_ins, audit=FakeAuditLogRepository(), uow=FakeUnitOfWork())
    out = uc.execute(_valid_input(user_id, date(2026, 4, 22)))
    assert out.water_glasses == 8
    assert check_ins.get_for_date(user_id, date(2026, 4, 22)) is not None


def test_upsert_check_in_overwrites_same_date() -> None:
    user_id = uuid.uuid4()
    d = date(2026, 4, 22)
    check_ins = FakeCheckInRepository()
    uc = UpsertCheckIn(check_ins=check_ins, audit=FakeAuditLogRepository(), uow=FakeUnitOfWork())
    uc.execute(_valid_input(user_id, d))
    out2 = uc.execute(
        UpsertCheckInInput(
            user_id=user_id,
            check_in_date=d,
            sleep_quality="restless",
            digestion="bloated",
            energy_state="sluggish",
            movement="rest",
            water_glasses=2,
        )
    )
    assert out2.water_glasses == 2
    assert out2.sleep_quality == "restless"


def test_upsert_check_in_raises_on_invalid_enum() -> None:
    uc = UpsertCheckIn(
        check_ins=FakeCheckInRepository(),
        audit=FakeAuditLogRepository(),
        uow=FakeUnitOfWork(),
    )
    with pytest.raises(ValidationError):
        uc.execute(
            UpsertCheckInInput(
                user_id=uuid.uuid4(),
                check_in_date=date(2026, 4, 22),
                sleep_quality="perfect",
                digestion="smooth",
                energy_state="balanced",
                movement="active",
                water_glasses=8,
            )
        )


def test_get_week_produces_seven_slots_with_sparse_data() -> None:
    user_id = uuid.uuid4()
    check_ins = FakeCheckInRepository()
    audit = FakeAuditLogRepository()
    uow = FakeUnitOfWork()
    UpsertCheckIn(check_ins=check_ins, audit=audit, uow=uow).execute(
        _valid_input(user_id, date(2026, 4, 22))
    )

    uc = GetCheckInWeek(check_ins=check_ins, clock=FakeClock(today=date(2026, 4, 26)))
    out = uc.execute(GetCheckInWeekInput(user_id=user_id))
    assert len(out.slots) == 7
    assert out.end_date == date(2026, 4, 26)
    assert out.start_date == date(2026, 4, 20)
    filled = [s for s in out.slots if s.check_in is not None]
    assert len(filled) == 1
    assert filled[0].date == date(2026, 4, 22)
