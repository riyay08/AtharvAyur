from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.entities import DailyEnvironmentTip as TipEntity
from app.models.daily_environment_tip import DailyEnvironmentTip as TipORM


def _to_entity(row: TipORM) -> TipEntity:
    return TipEntity(
        id=row.id,
        user_id=row.user_id,
        tip_date=row.tip_date,
        tip_title=row.tip_title,
        tip_description=row.tip_description,
        icon_name=row.icon_name,
        created_at=row.created_at,
    )


class SqlAlchemyEnvironmentTipRepository:
    def __init__(self, session: Session) -> None:
        self._s = session

    def get_for_date(
        self, user_id: uuid.UUID, tip_date: date
    ) -> TipEntity | None:
        row = self._s.execute(
            select(TipORM).where(
                TipORM.user_id == user_id,
                TipORM.tip_date == tip_date,
            )
        ).scalar_one_or_none()
        return _to_entity(row) if row else None

    def add(self, tip: TipEntity) -> TipEntity:
        row = TipORM(
            id=tip.id,
            user_id=tip.user_id,
            tip_date=tip.tip_date,
            tip_title=tip.tip_title,
            tip_description=tip.tip_description,
            icon_name=tip.icon_name,
        )
        self._s.add(row)
        self._s.flush()
        return _to_entity(row)
