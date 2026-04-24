from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog


class SqlAlchemyAuditLogRepository:
    def __init__(self, session: Session) -> None:
        self._s = session

    def record(self, actor: str, action: str) -> None:
        self._s.add(AuditLog(actor=actor, action=action))
        self._s.flush()
