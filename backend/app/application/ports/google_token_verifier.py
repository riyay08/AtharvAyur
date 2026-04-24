from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class GoogleIdClaims:
    """Trusted claims extracted from a verified Google ID token."""

    sub: str
    email: str | None
    email_verified: bool
    name: str | None


class GoogleTokenVerifier(Protocol):
    """Verify a Google Identity Services ID token.

    Implementations must check signature, issuer, audience (client id),
    and expiry. Raise ``app.domain.errors.AuthenticationError`` on any
    verification failure and ``app.domain.errors.ConfigurationError`` if
    the provider is not configured.
    """

    def verify(self, id_token: str) -> GoogleIdClaims: ...
