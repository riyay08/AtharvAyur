from __future__ import annotations

from typing import Protocol

from app.domain.value_objects import PhoneE164


class SmsSender(Protocol):
    """Send a transactional SMS (one-time passcode delivery).

    Implementations should raise ``app.domain.errors.ExternalServiceError``
    on network / provider failures so the use case can surface a friendly
    message to the caller.
    """

    def send_otp(self, *, phone: PhoneE164, code: str) -> None: ...
