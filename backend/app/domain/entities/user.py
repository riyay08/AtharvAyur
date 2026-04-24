from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from app.domain.value_objects import AuthProvider, Email, PhoneE164


@dataclass(slots=True)
class User:
    """A person using the system. Identity + credentials.

    Health data lives on `HealthProfile`. A user may have one or more of
    ``email`` / ``phone`` / ``google_sub`` set (the identifiers they can
    log in with). ``password_hash`` is only meaningful when ``email`` is
    set. ``display_name`` is purely cosmetic.

    A "pure anonymous" user has all identity fields left as ``None`` and
    ``primary_provider == ANONYMOUS``.
    """

    id: uuid.UUID
    region: str | None = None
    consent_flags: dict[str, Any] | list[Any] | None = None

    email: Email | None = None
    email_verified: bool = False
    phone: PhoneE164 | None = None
    phone_verified: bool = False
    password_hash: str | None = None
    google_sub: str | None = None
    display_name: str | None = None
    primary_provider: AuthProvider = AuthProvider.ANONYMOUS
    last_login_at: datetime | None = None

    @staticmethod
    def new(region: str | None = None) -> "User":
        return User(id=uuid.uuid4(), region=region)

    @property
    def is_anonymous(self) -> bool:
        return (
            self.email is None
            and self.phone is None
            and self.google_sub is None
            and self.password_hash is None
        )

    def touch_login(self, now: datetime | None = None) -> None:
        self.last_login_at = now or datetime.now(timezone.utc)
