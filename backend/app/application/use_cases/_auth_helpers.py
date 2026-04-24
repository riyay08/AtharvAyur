"""Internal helpers shared across auth use cases."""

from __future__ import annotations

from app.application.dtos import AuthSessionView, AuthenticatedUserView
from app.application.ports.repositories import WebAuthnCredentialRepository
from app.domain.entities import User


def build_session_view(
    *,
    user: User,
    token: str,
    has_passkey: bool,
    is_new_user: bool = False,
    token_type: str = "bearer",
) -> AuthSessionView:
    return AuthSessionView(
        user_id=user.id,
        access_token=token,
        token_type=token_type,
        email=user.email.value if user.email else None,
        phone=user.phone.value if user.phone else None,
        display_name=user.display_name,
        primary_provider=user.primary_provider.value,
        email_verified=user.email_verified,
        phone_verified=user.phone_verified,
        has_password=user.password_hash is not None,
        has_passkey=has_passkey,
        is_new_user=is_new_user,
    )


def build_authenticated_view(
    *,
    user: User,
    credentials: WebAuthnCredentialRepository,
) -> AuthenticatedUserView:
    passkeys = credentials.list_for_user(user.id)
    return AuthenticatedUserView(
        user_id=user.id,
        email=user.email.value if user.email else None,
        phone=user.phone.value if user.phone else None,
        display_name=user.display_name,
        primary_provider=user.primary_provider.value,
        email_verified=user.email_verified,
        phone_verified=user.phone_verified,
        has_password=user.password_hash is not None,
        passkey_count=len(passkeys),
    )
