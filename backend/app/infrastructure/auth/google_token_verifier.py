"""Google Identity Services ID-token verifier.

Delegates the cryptographic checks to ``google-auth``; we pin the audience
to our configured ``GOOGLE_CLIENT_ID`` so tokens minted for a different
app cannot be replayed.
"""

from __future__ import annotations

import logging

from app.application.ports.google_token_verifier import GoogleIdClaims
from app.config import settings
from app.domain.errors import AuthenticationError, ConfigurationError

logger = logging.getLogger(__name__)


class GoogleIdTokenVerifier:
    def __init__(self, *, client_id: str | None = None) -> None:
        self._client_id = client_id or settings.google_client_id

    def verify(self, id_token: str) -> GoogleIdClaims:
        if not self._client_id:
            raise ConfigurationError(
                "Google sign-in is not configured (set GOOGLE_CLIENT_ID in .env)."
            )
        try:
            from google.auth.transport import requests as google_requests
            from google.oauth2 import id_token as google_id_token
        except ImportError as exc:  # pragma: no cover - runtime guard
            raise ConfigurationError(
                "google-auth is not installed. Add it to requirements and reinstall."
            ) from exc

        try:
            info = google_id_token.verify_oauth2_token(
                id_token,
                google_requests.Request(),
                self._client_id,
            )
        except ValueError as exc:
            raise AuthenticationError("Google sign-in token is invalid.") from exc
        except Exception as exc:  # google.auth.exceptions.GoogleAuthError, transport errors, etc.
            logger.warning("Google ID token verification failed: %s", exc)
            raise AuthenticationError(
                "Google sign-in could not be verified. Ensure GOOGLE_CLIENT_ID in backend .env "
                "matches VITE_GOOGLE_CLIENT_ID (same OAuth Web client ID)."
            ) from exc

        sub = info.get("sub")
        if not isinstance(sub, str):
            raise AuthenticationError("Google sign-in token is missing sub.")

        return GoogleIdClaims(
            sub=sub,
            email=info.get("email"),
            email_verified=bool(info.get("email_verified", False)),
            name=info.get("name") or info.get("given_name"),
        )
