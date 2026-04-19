from __future__ import annotations

import uuid

from pydantic import BaseModel


class AuthSessionRequest(BaseModel):
    """Optional existing user id (e.g. from localStorage) to mint a new access token."""

    user_id: uuid.UUID | None = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: uuid.UUID
