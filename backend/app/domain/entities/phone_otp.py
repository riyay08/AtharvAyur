from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from app.domain.value_objects import PhoneE164


@dataclass(slots=True)
class PhoneOtp:
    """A pending one-time code tied to a phone number.

    ``code_hash`` is stored rather than the plaintext so the DB row does
    not leak a working credential. ``attempts`` is incremented by the
    verify use case to bound brute-force guessing.
    """

    id: uuid.UUID
    phone: PhoneE164
    code_hash: str
    expires_at: datetime
    attempts: int = 0
    consumed: bool = False
    created_at: datetime | None = None

    def is_expired(self, now: datetime | None = None) -> bool:
        now = now or datetime.now(timezone.utc)
        return now >= self.expires_at
