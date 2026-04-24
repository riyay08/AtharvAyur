from __future__ import annotations

import uuid
from typing import Protocol


class TokenService(Protocol):
    """JWT (or similar) issuance + verification."""

    def issue(self, *, user_id: uuid.UUID) -> str: ...
    def verify(self, token: str) -> uuid.UUID:
        """Return user_id on success; raise `app.domain.errors.ValidationError` on failure."""
        ...
