from __future__ import annotations

import secrets


class SecureOtpCodeGenerator:
    def __init__(self, *, digits: int = 6) -> None:
        if digits < 4:
            raise ValueError("OTP length must be at least 4 digits.")
        self._digits = digits

    def generate(self) -> str:
        max_exclusive = 10**self._digits
        code = secrets.randbelow(max_exclusive)
        return str(code).zfill(self._digits)
