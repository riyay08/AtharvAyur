"""JWT-backed `TokenService` implementation using python-jose."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt

from app.config import settings
from app.domain.errors import ValidationError


class JoseTokenService:
    def __init__(
        self,
        *,
        secret: str | None = None,
        algorithm: str | None = None,
        token_ttl_days: int = 30,
    ) -> None:
        self._secret = secret or settings.jwt_secret_key
        self._algorithm = algorithm or settings.jwt_algorithm
        self._ttl = timedelta(days=token_ttl_days)

    def issue(self, *, user_id: uuid.UUID) -> str:
        now = datetime.now(timezone.utc)
        payload = {
            "sub": str(user_id),
            "iat": int(now.timestamp()),
            "exp": int((now + self._ttl).timestamp()),
        }
        return jwt.encode(payload, self._secret, algorithm=self._algorithm)

    def verify(self, token: str) -> uuid.UUID:
        try:
            payload = jwt.decode(token, self._secret, algorithms=[self._algorithm])
        except JWTError as exc:
            raise ValidationError("Invalid or expired token.") from exc
        sub = payload.get("sub")
        if not isinstance(sub, str):
            raise ValidationError("Token missing subject.")
        try:
            return uuid.UUID(sub)
        except ValueError as exc:
            raise ValidationError("Token subject is not a UUID.") from exc
