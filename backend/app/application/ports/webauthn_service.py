from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any, Protocol

from app.domain.entities import WebAuthnCredential


@dataclass(frozen=True, slots=True)
class RegistrationChallenge:
    """Server-generated challenge used to tie a register/verify round-trip.

    ``options`` is a PublicKeyCredentialCreationOptions dict ready to be
    JSON-serialized to the browser. ``challenge`` is the raw bytes the
    server remembers (separately from the options the browser gets) so
    the verifier can confirm the authenticator signed the right value.
    """

    options: dict[str, Any]
    challenge: bytes


@dataclass(frozen=True, slots=True)
class AuthenticationChallenge:
    options: dict[str, Any]
    challenge: bytes


@dataclass(frozen=True, slots=True)
class VerifiedRegistration:
    credential_id: bytes
    public_key: bytes
    sign_count: int
    transports: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class VerifiedAuthentication:
    credential_id: bytes
    new_sign_count: int


class WebAuthnService(Protocol):
    """Port for WebAuthn (passkey) registration + authentication ceremonies."""

    def begin_registration(
        self,
        *,
        user_id: uuid.UUID,
        user_name: str,
        user_display_name: str,
        existing_credential_ids: list[bytes],
    ) -> RegistrationChallenge: ...

    def verify_registration(
        self,
        *,
        challenge: bytes,
        response: dict[str, Any],
    ) -> VerifiedRegistration: ...

    def begin_authentication(
        self,
        *,
        allowed_credentials: list[WebAuthnCredential],
    ) -> AuthenticationChallenge: ...

    def verify_authentication(
        self,
        *,
        challenge: bytes,
        response: dict[str, Any],
        credential: WebAuthnCredential,
    ) -> VerifiedAuthentication: ...
