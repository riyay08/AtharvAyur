"""Value objects shared across domain entities.

Value objects are immutable, equality-by-value, and have no identity.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, timedelta
from enum import Enum


class AuthProvider(str, Enum):
    """Identity provider that produced a user's login credential."""

    PASSWORD = "password"
    GOOGLE = "google"
    PHONE = "phone"
    PASSKEY = "passkey"
    ANONYMOUS = "anonymous"


# Intentionally permissive — we only want to reject obviously malformed
# strings so the UI surfaces friendly errors before a network round-trip.
# The backend does not attempt deliverability checks.
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


@dataclass(frozen=True, slots=True)
class Email:
    """RFC-shape email, normalized to lowercase."""

    value: str

    def __post_init__(self) -> None:
        v = self.value.strip().lower()
        if not _EMAIL_RE.match(v):
            raise ValueError("Invalid email address.")
        object.__setattr__(self, "value", v)

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.value


# E.164: optional leading '+', 8–15 digits. We accept anything that
# canonicalizes to that shape after stripping separators; the library
# `phonenumbers` would be stricter but we deliberately keep the domain
# free of third-party deps and do a coarse normalization here.
_PHONE_SANITIZE_RE = re.compile(r"[\s\-().]+")
_PHONE_E164_RE = re.compile(r"^\+?[1-9]\d{7,14}$")


@dataclass(frozen=True, slots=True)
class PhoneE164:
    """Phone number stored in E.164 form (always leading '+')."""

    value: str

    def __post_init__(self) -> None:
        raw = _PHONE_SANITIZE_RE.sub("", self.value.strip())
        if not _PHONE_E164_RE.match(raw):
            raise ValueError("Invalid phone number (E.164 expected).")
        normalized = raw if raw.startswith("+") else f"+{raw}"
        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.value


class Dosha(str, Enum):
    VATA = "vata"
    PITTA = "pitta"
    KAPHA = "kapha"


class Pillar(str, Enum):
    MIND = "Mind"
    FUEL = "Fuel"
    BODY = "Body"

    @classmethod
    def all(cls) -> tuple["Pillar", ...]:
        return (cls.MIND, cls.FUEL, cls.BODY)


class ChatRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"


class SafetyBlockReason(str, Enum):
    NONE = "none"
    EMERGENCY_OR_RED_FLAG = "emergency_or_red_flag"
    CONTRAINDICATION = "contraindication"


class HumidityBand(str, Enum):
    DRY = "dry"
    BALANCED = "balanced"
    DAMP = "damp"


class Habitat(str, Enum):
    URBAN = "Urban"
    RURAL = "Rural"


@dataclass(frozen=True, slots=True)
class Citation:
    """A grounded source citation the model emitted."""

    url: str
    title: str | None = None
    snippet: str | None = None


@dataclass(frozen=True, slots=True)
class DateRange:
    """Inclusive calendar range."""

    start: date
    end: date

    def __post_init__(self) -> None:
        if self.end < self.start:
            raise ValueError("DateRange end cannot be before start")

    @property
    def days(self) -> int:
        return (self.end - self.start).days + 1

    def contains(self, d: date) -> bool:
        return self.start <= d <= self.end

    @classmethod
    def week_starting(cls, start: date) -> "DateRange":
        return cls(start=start, end=start + timedelta(days=6))
