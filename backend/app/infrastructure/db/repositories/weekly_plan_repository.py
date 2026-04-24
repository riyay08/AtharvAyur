from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from app.domain.entities import WeeklyPlan as WeeklyPlanEntity
from app.models.weekly_plan import WeeklyPlan as WeeklyPlanORM


def _to_entity(row: WeeklyPlanORM) -> WeeklyPlanEntity:
    return WeeklyPlanEntity(
        id=row.id,
        user_id=row.user_id,
        start_date=row.start_date,
        tasks=row.tasks,
        created_at=row.created_at,
    )


class SqlAlchemyWeeklyPlanRepository:
    def __init__(self, session: Session) -> None:
        self._s = session

    def get_for_week(
        self, user_id: uuid.UUID, week_start: date
    ) -> WeeklyPlanEntity | None:
        row = self._s.execute(
            select(WeeklyPlanORM).where(
                WeeklyPlanORM.user_id == user_id,
                WeeklyPlanORM.start_date == week_start,
            )
        ).scalar_one_or_none()
        return _to_entity(row) if row else None

    def upsert(self, plan: WeeklyPlanEntity) -> WeeklyPlanEntity:
        existing = self._s.execute(
            select(WeeklyPlanORM).where(
                WeeklyPlanORM.user_id == plan.user_id,
                WeeklyPlanORM.start_date == plan.start_date,
            )
        ).scalar_one_or_none()
        if existing:
            existing.tasks = plan.tasks
            flag_modified(existing, "tasks")
            self._s.flush()
            return _to_entity(existing)
        row = WeeklyPlanORM(
            id=plan.id,
            user_id=plan.user_id,
            start_date=plan.start_date,
            tasks=plan.tasks,
        )
        self._s.add(row)
        self._s.flush()
        return _to_entity(row)

    def save_envelope(self, plan: WeeklyPlanEntity) -> WeeklyPlanEntity:
        """Persist mutations to an in-memory envelope back to the JSONB column."""
        row = self._s.execute(
            select(WeeklyPlanORM).where(WeeklyPlanORM.id == plan.id)
        ).scalar_one_or_none()
        if row is None:
            return self.upsert(plan)
        row.tasks = plan.tasks
        flag_modified(row, "tasks")
        self._s.flush()
        return _to_entity(row)
