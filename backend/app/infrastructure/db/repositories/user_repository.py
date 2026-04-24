from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.entities import User as UserEntity
from app.domain.value_objects import AuthProvider, Email, PhoneE164
from app.models.health_profile import HealthProfile as HealthProfileORM
from app.models.user import User as UserORM


def _to_entity(row: UserORM) -> UserEntity:
    try:
        provider = AuthProvider(row.primary_provider)
    except ValueError:
        provider = AuthProvider.ANONYMOUS
    return UserEntity(
        id=row.id,
        region=row.region,
        consent_flags=row.consent_flags,
        email=Email(row.email) if row.email else None,
        email_verified=bool(row.email_verified),
        phone=PhoneE164(row.phone) if row.phone else None,
        phone_verified=bool(row.phone_verified),
        password_hash=row.password_hash,
        google_sub=row.google_sub,
        display_name=row.display_name,
        primary_provider=provider,
        last_login_at=row.last_login_at,
    )


def _apply_entity(row: UserORM, user: UserEntity) -> None:
    row.region = user.region
    row.consent_flags = user.consent_flags
    row.email = user.email.value if user.email else None
    row.email_verified = bool(user.email_verified)
    row.phone = user.phone.value if user.phone else None
    row.phone_verified = bool(user.phone_verified)
    row.password_hash = user.password_hash
    row.google_sub = user.google_sub
    row.display_name = user.display_name
    row.primary_provider = user.primary_provider.value
    row.last_login_at = user.last_login_at


class SqlAlchemyUserRepository:
    def __init__(self, session: Session) -> None:
        self._s = session

    def get_by_id(self, user_id: uuid.UUID) -> UserEntity | None:
        row = self._s.get(UserORM, user_id)
        return _to_entity(row) if row else None

    def get_by_email(self, email: Email) -> UserEntity | None:
        row = self._s.execute(
            select(UserORM).where(UserORM.email == email.value)
        ).scalar_one_or_none()
        return _to_entity(row) if row else None

    def get_by_phone(self, phone: PhoneE164) -> UserEntity | None:
        row = self._s.execute(
            select(UserORM).where(UserORM.phone == phone.value)
        ).scalar_one_or_none()
        return _to_entity(row) if row else None

    def get_by_google_sub(self, google_sub: str) -> UserEntity | None:
        row = self._s.execute(
            select(UserORM).where(UserORM.google_sub == google_sub)
        ).scalar_one_or_none()
        return _to_entity(row) if row else None

    def add(self, user: UserEntity) -> UserEntity:
        row = UserORM(id=user.id)
        _apply_entity(row, user)
        self._s.add(row)
        self._s.flush()
        return _to_entity(row)

    def update(self, user: UserEntity) -> UserEntity:
        row = self._s.get(UserORM, user.id)
        if row is None:
            return self.add(user)
        _apply_entity(row, user)
        self._s.flush()
        return _to_entity(row)

    def list_ids_with_profile(self) -> list[uuid.UUID]:
        stmt = select(UserORM.id).join(HealthProfileORM, HealthProfileORM.user_id == UserORM.id)
        return list(self._s.execute(stmt).scalars().all())
