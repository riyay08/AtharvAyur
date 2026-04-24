"""Domain error hierarchy.

Raised by domain services and use cases. Interface layer translates these into
HTTP responses; infrastructure layer translates framework errors into these.
"""

from __future__ import annotations


class DomainError(Exception):
    """Base class for all domain-level errors."""


class NotFoundError(DomainError):
    """Referenced entity does not exist."""


class ValidationError(DomainError):
    """Input violates a domain invariant."""


class SafetyBlockedError(DomainError):
    """Deterministic safety gate blocked the request.

    Carries the user-facing escalation message and the matched terms so the
    caller can persist / audit without recomputing.
    """

    def __init__(
        self,
        reason: str,
        escalation_message: str,
        matched_terms: tuple[str, ...] = (),
    ) -> None:
        super().__init__(escalation_message)
        self.reason = reason
        self.escalation_message = escalation_message
        self.matched_terms = matched_terms


class ExternalServiceError(DomainError):
    """An outward dependency (LLM, weather, etc.) failed or is not configured."""


class ConfigurationError(DomainError):
    """Required configuration (API key, model, etc.) is missing."""


class AuthenticationError(DomainError):
    """Caller failed an authentication check (bad password, expired OTP, etc.)."""


class AuthConflictError(DomainError):
    """Identifier is already claimed by a different user (e.g. email in use)."""
