"""Passkey (WebAuthn) implementation backed by the `py-webauthn` package.

The port (``app.application.ports.webauthn_service.WebAuthnService``) is
intentionally coarse so we can swap implementations without touching use
cases. This adapter translates between our domain types and py-webauthn's
structs, handling the registration + authentication ceremonies.
"""

from __future__ import annotations

import json
import uuid
from typing import Any

from app.application.ports.webauthn_service import (
    AuthenticationChallenge,
    RegistrationChallenge,
    VerifiedAuthentication,
    VerifiedRegistration,
)
from app.config import settings
from app.domain.entities import WebAuthnCredential
from app.domain.errors import AuthenticationError, ConfigurationError


def _import_webauthn():
    try:
        import webauthn  # type: ignore[import-not-found]
        from webauthn.helpers import options_to_json  # type: ignore[import-not-found]
        from webauthn.helpers.structs import (  # type: ignore[import-not-found]
            AuthenticatorSelectionCriteria,
            PublicKeyCredentialDescriptor,
            ResidentKeyRequirement,
            UserVerificationRequirement,
        )
    except ImportError as exc:  # pragma: no cover - runtime guard
        raise ConfigurationError(
            "The `webauthn` package is not installed. Add it to requirements.txt and reinstall."
        ) from exc
    return webauthn, options_to_json, (
        AuthenticatorSelectionCriteria,
        PublicKeyCredentialDescriptor,
        ResidentKeyRequirement,
        UserVerificationRequirement,
    )


class PyWebAuthnService:
    def __init__(
        self,
        *,
        rp_id: str | None = None,
        rp_name: str | None = None,
        origin: str | None = None,
    ) -> None:
        self._rp_id = rp_id or settings.webauthn_rp_id
        self._rp_name = rp_name or settings.webauthn_rp_name
        self._origin = origin or settings.webauthn_origin

    # ---------- Registration ----------

    def begin_registration(
        self,
        *,
        user_id: uuid.UUID,
        user_name: str,
        user_display_name: str,
        existing_credential_ids: list[bytes],
    ) -> RegistrationChallenge:
        webauthn, options_to_json, structs = _import_webauthn()
        (
            AuthenticatorSelectionCriteria,
            PublicKeyCredentialDescriptor,
            ResidentKeyRequirement,
            UserVerificationRequirement,
        ) = structs

        exclude = [PublicKeyCredentialDescriptor(id=cid) for cid in existing_credential_ids]
        options = webauthn.generate_registration_options(
            rp_id=self._rp_id,
            rp_name=self._rp_name,
            user_id=user_id.bytes,
            user_name=user_name,
            user_display_name=user_display_name,
            exclude_credentials=exclude,
            authenticator_selection=AuthenticatorSelectionCriteria(
                resident_key=ResidentKeyRequirement.PREFERRED,
                user_verification=UserVerificationRequirement.PREFERRED,
            ),
        )
        options_dict: dict[str, Any] = json.loads(options_to_json(options))
        return RegistrationChallenge(options=options_dict, challenge=bytes(options.challenge))

    def verify_registration(
        self,
        *,
        challenge: bytes,
        response: dict[str, Any],
    ) -> VerifiedRegistration:
        webauthn, _opts, _structs = _import_webauthn()
        try:
            verified = webauthn.verify_registration_response(
                credential=response,
                expected_challenge=challenge,
                expected_origin=self._origin,
                expected_rp_id=self._rp_id,
            )
        except Exception as exc:  # py-webauthn raises InvalidRegistrationResponse
            raise AuthenticationError("Passkey registration could not be verified.") from exc

        transports = _extract_transports(response)
        return VerifiedRegistration(
            credential_id=bytes(verified.credential_id),
            public_key=bytes(verified.credential_public_key),
            sign_count=int(verified.sign_count),
            transports=transports,
        )

    # ---------- Authentication ----------

    def begin_authentication(
        self,
        *,
        allowed_credentials: list[WebAuthnCredential],
    ) -> AuthenticationChallenge:
        webauthn, options_to_json, structs = _import_webauthn()
        (
            _AuthenticatorSelectionCriteria,
            PublicKeyCredentialDescriptor,
            _ResidentKeyRequirement,
            UserVerificationRequirement,
        ) = structs

        allow = [
            PublicKeyCredentialDescriptor(id=c.credential_id) for c in allowed_credentials
        ]
        options = webauthn.generate_authentication_options(
            rp_id=self._rp_id,
            allow_credentials=allow,
            user_verification=UserVerificationRequirement.PREFERRED,
        )
        options_dict: dict[str, Any] = json.loads(options_to_json(options))
        return AuthenticationChallenge(options=options_dict, challenge=bytes(options.challenge))

    def verify_authentication(
        self,
        *,
        challenge: bytes,
        response: dict[str, Any],
        credential: WebAuthnCredential,
    ) -> VerifiedAuthentication:
        webauthn, _opts, _structs = _import_webauthn()
        try:
            verified = webauthn.verify_authentication_response(
                credential=response,
                expected_challenge=challenge,
                expected_origin=self._origin,
                expected_rp_id=self._rp_id,
                credential_public_key=credential.public_key,
                credential_current_sign_count=credential.sign_count,
            )
        except Exception as exc:
            raise AuthenticationError("Passkey could not be verified.") from exc
        return VerifiedAuthentication(
            credential_id=bytes(verified.credential_id),
            new_sign_count=int(verified.new_sign_count),
        )


def _extract_transports(response: dict[str, Any]) -> tuple[str, ...]:
    resp = response.get("response") or {}
    transports = resp.get("transports") or response.get("transports")
    if isinstance(transports, list):
        return tuple(str(t) for t in transports)
    return ()
