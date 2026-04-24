"""Development-mode SMS sender that logs the OTP instead of delivering it.

Swap this for a Twilio / AWS SNS adapter in production without touching
the use case. The port is ``app.application.ports.sms_sender.SmsSender``.
"""

from __future__ import annotations

import logging

from app.domain.value_objects import PhoneE164

logger = logging.getLogger(__name__)


class StubSmsSender:
    def send_otp(self, *, phone: PhoneE164, code: str) -> None:
        logger.warning(
            "[DEV SMS] OTP for %s is %s (not actually sent — using StubSmsSender)",
            phone.value,
            code,
        )
