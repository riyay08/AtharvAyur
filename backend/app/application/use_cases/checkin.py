from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import timedelta

from app.application.dtos import (
    CheckInView,
    CheckInWeekSlotView,
    GetCheckInWeekInput,
    GetCheckInWeekOutput,
    UpsertCheckInInput,
)
from app.application.ports.clock import Clock
from app.application.ports.repositories import AuditLogRepository, CheckInRepository
from app.application.ports.unit_of_work import UnitOfWork
from app.domain.entities import (
    DailyCheckIn,
    Digestion,
    EnergyState,
    MovementLevel,
    SleepQuality,
)
from app.domain.errors import ValidationError


def _to_view(ci: DailyCheckIn) -> CheckInView:
    return CheckInView(
        id=ci.id,
        check_in_date=ci.check_in_date,
        sleep_quality=ci.sleep_quality.value,
        digestion=ci.digestion.value,
        energy_state=ci.energy_state.value,
        movement=ci.movement.value,
        water_glasses=ci.water_glasses,
        timestamp=ci.timestamp,
    )


@dataclass(frozen=True, slots=True)
class UpsertCheckIn:
    check_ins: CheckInRepository
    audit: AuditLogRepository
    uow: UnitOfWork

    def execute(self, cmd: UpsertCheckInInput) -> CheckInView:
        try:
            sleep = SleepQuality(cmd.sleep_quality)
            dig = Digestion(cmd.digestion)
            energy = EnergyState(cmd.energy_state)
            move = MovementLevel(cmd.movement)
        except ValueError as exc:
            raise ValidationError(f"Invalid check-in enum value: {exc}") from exc

        existing = self.check_ins.get_for_date(cmd.user_id, cmd.check_in_date)
        check_in = DailyCheckIn(
            id=existing.id if existing else uuid.uuid4(),
            user_id=cmd.user_id,
            check_in_date=cmd.check_in_date,
            sleep_quality=sleep,
            digestion=dig,
            energy_state=energy,
            movement=move,
            water_glasses=cmd.water_glasses,
            timestamp=existing.timestamp if existing else None,
            # `mood_score`/`notes` aren't on this command yet (v1 endpoint) — preserve
            # whatever's already stored rather than silently nulling it on every edit.
            mood_score=existing.mood_score if existing else None,
            notes=existing.notes if existing else None,
        )
        saved = self.check_ins.upsert(check_in)
        self.audit.record(actor=str(cmd.user_id), action="checkin.upserted")
        self.uow.commit()
        return _to_view(saved)


@dataclass(frozen=True, slots=True)
class GetCheckInWeek:
    check_ins: CheckInRepository
    clock: Clock

    def execute(self, cmd: GetCheckInWeekInput) -> GetCheckInWeekOutput:
        end = cmd.end_date or self.clock.today()
        start = end - timedelta(days=6)
        rows = self.check_ins.list_week(cmd.user_id, start, end)
        by_date = {r.check_in_date: r for r in rows}

        slots: list[CheckInWeekSlotView] = []
        for i in range(7):
            d = start + timedelta(days=i)
            row = by_date.get(d)
            slots.append(
                CheckInWeekSlotView(
                    date=d,
                    check_in=_to_view(row) if row else None,
                )
            )
        return GetCheckInWeekOutput(start_date=start, end_date=end, slots=slots)
