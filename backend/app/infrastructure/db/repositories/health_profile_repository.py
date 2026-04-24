from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.entities import HealthProfile as HealthProfileEntity
from app.models.health_profile import HealthProfile as HealthProfileORM


def _to_entity(row: HealthProfileORM) -> HealthProfileEntity:
    return HealthProfileEntity(
        id=row.id,
        user_id=row.user_id,
        conditions=row.conditions,
        allergies=row.allergies,
        medications=row.medications,
    )


class SqlAlchemyHealthProfileRepository:
    def __init__(self, session: Session) -> None:
        self._s = session

    def get_by_user_id(self, user_id: uuid.UUID) -> HealthProfileEntity | None:
        row = self._s.execute(
            select(HealthProfileORM).where(HealthProfileORM.user_id == user_id)
        ).scalar_one_or_none()
        return _to_entity(row) if row else None

    def upsert(self, profile: HealthProfileEntity) -> HealthProfileEntity:
        existing = self._s.execute(
            select(HealthProfileORM).where(HealthProfileORM.user_id == profile.user_id)
        ).scalar_one_or_none()
        if existing:
            existing.conditions = profile.conditions
            existing.allergies = profile.allergies
            existing.medications = profile.medications
            self._s.flush()
            return _to_entity(existing)
        row = HealthProfileORM(
            id=profile.id,
            user_id=profile.user_id,
            conditions=profile.conditions,
            allergies=profile.allergies,
            medications=profile.medications,
        )
        self._s.add(row)
        self._s.flush()
        return _to_entity(row)
