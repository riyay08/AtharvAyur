from __future__ import annotations

from typing import Protocol


class OtpCodeGenerator(Protocol):
    """Produce a fresh OTP code string.

    Split from the hasher so tests can inject a deterministic generator.
    """

    def generate(self) -> str: ...
