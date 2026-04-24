from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.entities import (
    DailyCheckIn as CheckInEntity,
)
from app.domain.entities import Digestion, EnergyState, MovementLevel, SleepQuality
from app.models.daily_check_in import (
    DailyCheckIn as CheckInORM,
)
from app.models.daily_check_in import (
    Digestion as OrmDigestion,
)
from app.models.daily_check_in import (
    EnergyState as OrmEnergyState,
)
from app.models.daily_check_in import (
    MovementLevel as OrmMovementLevel,
)
from app.models.daily_check_in import (
    SleepQuality as OrmSleepQuality,
)


def _to_entity(row: CheckInORM) -> CheckInEntity:
    return CheckInEntity(
        id=row.id,
        user_id=row.user_id,
        check_in_date=row.check_in_date,
        sleep_quality=SleepQuality(row.sleep_quality.value),
        digestion=Digestion(row.digestion.value),
        energy_state=EnergyState(row.energy_state.value),
        movement=MovementLevel(row.movement.value),
        water_glasses=row.water_glasses,
        timestamp=row.timestamp,
    )


class SqlAlchemyCheckInRepository:
    def __init__(self, session: Session) -> None:
        self._s = session

    def get_for_date(self, user_id: uuid.UUID, d: date) -> CheckInEntity | None:
        row = self._s.execute(
            select(CheckInORM).where(
                CheckInORM.user_id == user_id,
                CheckInORM.check_in_date == d,
            )
        ).scalar_one_or_none()
        return _to_entity(row) if row else None

    def list_week(
        self, user_id: uuid.UUID, start: date, end: date
    ) -> list[CheckInEntity]:
        rows = (
            self._s.execute(
                select(CheckInORM)
                .where(
                    CheckInORM.user_id == user_id,
                    CheckInORM.check_in_date >= start,
                    CheckInORM.check_in_date <= end,
                )
                .order_by(CheckInORM.check_in_date.asc())
            )
            .scalars()
            .all()
        )
        return [_to_entity(r) for r in rows]

    def upsert(self, check_in: CheckInEntity) -> CheckInEntity:
        existing = self._s.execute(
            select(CheckInORM).where(
                CheckInORM.user_id == check_in.user_id,
                CheckInORM.check_in_date == check_in.check_in_date,
            )
        ).scalar_one_or_none()
        if existing:
            existing.sleep_quality = OrmSleepQuality(check_in.sleep_quality.value)
            existing.digestion = OrmDigestion(check_in.digestion.value)
            existing.energy_state = OrmEnergyState(check_in.energy_state.value)
            existing.movement = OrmMovementLevel(check_in.movement.value)
            existing.water_glasses = check_in.water_glasses
            self._s.flush()
            return _to_entity(existing)
        row = CheckInORM(
            id=check_in.id,
            user_id=check_in.user_id,
            check_in_date=check_in.check_in_date,
            sleep_quality=OrmSleepQuality(check_in.sleep_quality.value),
            digestion=OrmDigestion(check_in.digestion.value),
            energy_state=OrmEnergyState(check_in.energy_state.value),
            movement=OrmMovementLevel(check_in.movement.value),
            water_glasses=check_in.water_glasses,
        )
        self._s.add(row)
        self._s.flush()
        return _to_entity(row)
