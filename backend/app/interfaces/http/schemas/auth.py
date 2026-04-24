from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, EmailStr, Field


class AuthSessionRequest(BaseModel):
    """Optional existing user id (e.g. from localStorage) to mint a new access token."""

    user_id: uuid.UUID | None = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: uuid.UUID


class SessionResponse(BaseModel):
    """Returned by every non-anonymous login / signup endpoint."""

    access_token: str
    token_type: str = "bearer"
    user_id: uuid.UUID
    email: str | None = None
    phone: str | None = None
    display_name: str | None = None
    primary_provider: str
    email_verified: bool = False
    phone_verified: bool = False
    has_password: bool = False
    has_passkey: bool = False
    is_new_user: bool = False


class SignUpEmailRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    display_name: str | None = Field(default=None, max_length=120)
    anonymous_user_id: uuid.UUID | None = None


class LogInEmailRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=256)


class RequestPhoneOtpRequest(BaseModel):
    phone: str = Field(min_length=6, max_length=32)


class RequestPhoneOtpResponse(BaseModel):
    phone: str
    expires_at: datetime
    dev_code: str | None = None


class VerifyPhoneOtpRequest(BaseModel):
    phone: str = Field(min_length=6, max_length=32)
    code: str = Field(min_length=4, max_length=10)
    display_name: str | None = Field(default=None, max_length=120)
    anonymous_user_id: uuid.UUID | None = None


class GoogleSignInRequest(BaseModel):
    id_token: str = Field(min_length=10)
    anonymous_user_id: uuid.UUID | None = None


class PasskeyChallengeResponse(BaseModel):
    options: Any
    challenge: str = Field(
        description="Opaque challenge handle to send back with the finish call."
    )


class PasskeyRegisterFinishRequest(BaseModel):
    challenge: str
    response: Any
    label: str | None = Field(default=None, max_length=120)


class PasskeyLoginStartRequest(BaseModel):
    email: EmailStr | None = None


class PasskeyLoginFinishRequest(BaseModel):
    challenge: str
    response: Any


class AuthenticatedUserResponse(BaseModel):
    user_id: uuid.UUID
    email: str | None = None
    phone: str | None = None
    display_name: str | None = None
    primary_provider: str
    email_verified: bool = False
    phone_verified: bool = False
    has_password: bool = False
    passkey_count: int = 0
    google_client_id: str | None = None
