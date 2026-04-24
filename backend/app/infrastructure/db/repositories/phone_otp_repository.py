from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.entities import PhoneOtp as PhoneOtpEntity
from app.domain.value_objects import PhoneE164
from app.models.phone_otp import PhoneOtp as PhoneOtpORM


def _to_entity(row: PhoneOtpORM) -> PhoneOtpEntity:
    return PhoneOtpEntity(
        id=row.id,
        phone=PhoneE164(row.phone),
        code_hash=row.code_hash,
        expires_at=row.expires_at,
        attempts=row.attempts,
        consumed=row.consumed,
        created_at=row.created_at,
    )


class SqlAlchemyPhoneOtpRepository:
    def __init__(self, session: Session) -> None:
        self._s = session

    def add(self, otp: PhoneOtpEntity) -> PhoneOtpEntity:
        row = PhoneOtpORM(
            id=otp.id,
            phone=otp.phone.value,
            code_hash=otp.code_hash,
            expires_at=otp.expires_at,
            attempts=otp.attempts,
            consumed=otp.consumed,
        )
        self._s.add(row)
        self._s.flush()
        return _to_entity(row)

    def get_latest_active_for_phone(self, phone: PhoneE164) -> PhoneOtpEntity | None:
        row = self._s.execute(
            select(PhoneOtpORM)
            .where(PhoneOtpORM.phone == phone.value, PhoneOtpORM.consumed == False)  # noqa: E712
            .order_by(PhoneOtpORM.created_at.desc())
            .limit(1)
        ).scalar_one_or_none()
        return _to_entity(row) if row else None

    def update(self, otp: PhoneOtpEntity) -> PhoneOtpEntity:
        row = self._s.get(PhoneOtpORM, otp.id)
        if row is None:
            return self.add(otp)
        row.attempts = otp.attempts
        row.consumed = otp.consumed
        row.expires_at = otp.expires_at
        self._s.flush()
        return _to_entity(row)
