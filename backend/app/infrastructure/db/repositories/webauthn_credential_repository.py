from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.entities import WebAuthnCredential as CredentialEntity
from app.models.webauthn_credential import WebAuthnCredential as CredentialORM


def _transports_to_str(transports: tuple[str, ...]) -> str | None:
    if not transports:
        return None
    return ",".join(t.strip() for t in transports if t)


def _transports_from_str(raw: str | None) -> tuple[str, ...]:
    if not raw:
        return ()
    return tuple(t.strip() for t in raw.split(",") if t.strip())


def _to_entity(row: CredentialORM) -> CredentialEntity:
    return CredentialEntity(
        id=row.id,
        user_id=row.user_id,
        credential_id=bytes(row.credential_id),
        public_key=bytes(row.public_key),
        sign_count=row.sign_count,
        transports=_transports_from_str(row.transports),
        label=row.label,
        created_at=row.created_at,
        last_used_at=row.last_used_at,
    )


class SqlAlchemyWebAuthnCredentialRepository:
    def __init__(self, session: Session) -> None:
        self._s = session

    def add(self, credential: CredentialEntity) -> CredentialEntity:
        row = CredentialORM(
            id=credential.id,
            user_id=credential.user_id,
            credential_id=credential.credential_id,
            public_key=credential.public_key,
            sign_count=credential.sign_count,
            transports=_transports_to_str(credential.transports),
            label=credential.label,
        )
        self._s.add(row)
        self._s.flush()
        return _to_entity(row)

    def list_for_user(self, user_id: uuid.UUID) -> list[CredentialEntity]:
        rows = (
            self._s.execute(
                select(CredentialORM)
                .where(CredentialORM.user_id == user_id)
                .order_by(CredentialORM.created_at.asc())
            )
            .scalars()
            .all()
        )
        return [_to_entity(r) for r in rows]

    def get_by_credential_id(self, credential_id: bytes) -> CredentialEntity | None:
        row = self._s.execute(
            select(CredentialORM).where(CredentialORM.credential_id == credential_id)
        ).scalar_one_or_none()
        return _to_entity(row) if row else None

    def update(self, credential: CredentialEntity) -> CredentialEntity:
        row = self._s.get(CredentialORM, credential.id)
        if row is None:
            return self.add(credential)
        row.sign_count = credential.sign_count
        row.last_used_at = credential.last_used_at
        row.label = credential.label
        self._s.flush()
        return _to_entity(row)

    def delete(self, credential_id: uuid.UUID) -> None:
        row = self._s.get(CredentialORM, credential_id)
        if row is not None:
            self._s.delete(row)
            self._s.flush()
