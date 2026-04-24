"""Authentication & account-management use cases.

Each class is a single workflow wired from ports (repositories, gateways,
clock, token service, unit-of-work). All cross-cutting details — password
hashing, SMS delivery, Google ID token verification, WebAuthn — live
behind Protocols in ``app.application.ports`` and are injected here.
"""

from __future__ import annotations

import base64
import hashlib
import uuid
from dataclasses import dataclass
from datetime import timedelta
from typing import Any

from app.application.dtos import (
    AuthSessionView,
    AuthenticatedUserView,
    IssueTokenInput,
    IssueTokenOutput,
    LogInWithEmailInput,
    PasskeyChallengeView,
    PasskeyLoginFinishInput,
    PasskeyLoginStartInput,
    PasskeyRegisterFinishInput,
    PasskeyRegisterStartInput,
    RequestPhoneOtpInput,
    RequestPhoneOtpOutput,
    SignInWithGoogleInput,
    SignUpWithEmailInput,
    VerifyPhoneOtpInput,
)
from app.application.ports.clock import Clock
from app.application.ports.google_token_verifier import GoogleTokenVerifier
from app.application.ports.otp_code_generator import OtpCodeGenerator
from app.application.ports.password_hasher import PasswordHasher
from app.application.ports.repositories import (
    AuditLogRepository,
    PhoneOtpRepository,
    UserRepository,
    WebAuthnCredentialRepository,
)
from app.application.ports.sms_sender import SmsSender
from app.application.ports.token_service import TokenService
from app.application.ports.unit_of_work import UnitOfWork
from app.application.ports.webauthn_service import WebAuthnService
from app.application.use_cases._auth_helpers import (
    build_authenticated_view,
    build_session_view,
)
from app.domain.entities import PhoneOtp, User, WebAuthnCredential
from app.domain.errors import (
    AuthConflictError,
    AuthenticationError,
    ExternalServiceError,
    NotFoundError,
    ValidationError,
)
from app.domain.value_objects import AuthProvider, Email, PhoneE164

_OTP_TTL = timedelta(minutes=10)
_OTP_MAX_ATTEMPTS = 5
_MIN_PASSWORD_LEN = 8


def _hash_otp(code: str) -> str:
    """Non-reversible fingerprint so the OTP column never stores a working credential."""

    return hashlib.sha256(code.encode("utf-8")).hexdigest()


def _validate_password(plain: str) -> None:
    if len(plain) < _MIN_PASSWORD_LEN:
        raise ValidationError(
            f"Password must be at least {_MIN_PASSWORD_LEN} characters."
        )


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(s: str) -> bytes:
    padding = "=" * (-len(s) % 4)
    return base64.urlsafe_b64decode(s + padding)


# ---------- Anonymous token (legacy; kept for the quiz-first flow) ----------


@dataclass(frozen=True, slots=True)
class IssueAccessToken:
    users: UserRepository
    audit: AuditLogRepository
    tokens: TokenService
    uow: UnitOfWork

    def execute(self, cmd: IssueTokenInput) -> IssueTokenOutput:
        user: User | None = None
        if cmd.user_id is not None:
            user = self.users.get_by_id(cmd.user_id)
        if user is None:
            user = self.users.add(User.new())
            self.audit.record(actor=str(user.id), action="auth.user_created")
        token = self.tokens.issue(user_id=user.id)
        self.audit.record(actor=str(user.id), action="auth.token_issued")
        self.uow.commit()
        return IssueTokenOutput(access_token=token, token_type="bearer", user_id=user.id)


# ---------- Email + password ----------


@dataclass(frozen=True, slots=True)
class SignUpWithEmail:
    users: UserRepository
    credentials: WebAuthnCredentialRepository
    hasher: PasswordHasher
    audit: AuditLogRepository
    tokens: TokenService
    clock: Clock
    uow: UnitOfWork

    def execute(self, cmd: SignUpWithEmailInput) -> AuthSessionView:
        email = Email(cmd.email)
        _validate_password(cmd.password)

        if self.users.get_by_email(email) is not None:
            raise AuthConflictError("That email is already registered. Try logging in instead.")

        user = self._resolve_base_user(cmd.anonymous_user_id)
        user.email = email
        user.password_hash = self.hasher.hash(cmd.password)
        user.display_name = cmd.display_name or (user.display_name or email.value.split("@")[0])
        user.primary_provider = AuthProvider.PASSWORD
        user.touch_login(self.clock.utc_now())
        self.users.update(user)

        token = self.tokens.issue(user_id=user.id)
        self.audit.record(actor=str(user.id), action="auth.signup.email")
        self.uow.commit()

        return build_session_view(
            user=user,
            token=token,
            has_passkey=False,
            is_new_user=True,
        )

    def _resolve_base_user(self, anonymous_user_id: uuid.UUID | None) -> User:
        if anonymous_user_id is not None:
            existing = self.users.get_by_id(anonymous_user_id)
            if existing is not None and existing.is_anonymous:
                return existing
        return self.users.add(User.new())


@dataclass(frozen=True, slots=True)
class LogInWithEmail:
    users: UserRepository
    credentials: WebAuthnCredentialRepository
    hasher: PasswordHasher
    audit: AuditLogRepository
    tokens: TokenService
    clock: Clock
    uow: UnitOfWork

    def execute(self, cmd: LogInWithEmailInput) -> AuthSessionView:
        email = Email(cmd.email)
        user = self.users.get_by_email(email)
        if user is None or user.password_hash is None:
            raise AuthenticationError("Email or password is incorrect.")
        if not self.hasher.verify(cmd.password, user.password_hash):
            self.audit.record(actor=str(user.id), action="auth.login.email.failed")
            raise AuthenticationError("Email or password is incorrect.")

        user.touch_login(self.clock.utc_now())
        self.users.update(user)
        token = self.tokens.issue(user_id=user.id)
        self.audit.record(actor=str(user.id), action="auth.login.email")
        self.uow.commit()

        has_passkey = bool(self.credentials.list_for_user(user.id))
        return build_session_view(user=user, token=token, has_passkey=has_passkey)


# ---------- Phone + OTP ----------


@dataclass(frozen=True, slots=True)
class RequestPhoneOtp:
    """Generate + send a fresh OTP for the provided phone.

    The same endpoint powers signup and login — we look up the user by
    phone at verify time, not here, so enumeration is limited to the
    SMS dispatch side.
    """

    otps: PhoneOtpRepository
    sms: SmsSender
    code_generator: OtpCodeGenerator
    clock: Clock
    audit: AuditLogRepository
    uow: UnitOfWork
    expose_dev_code: bool = False

    def execute(self, cmd: RequestPhoneOtpInput) -> RequestPhoneOtpOutput:
        phone = PhoneE164(cmd.phone)
        code = self.code_generator.generate()
        otp = PhoneOtp(
            id=uuid.uuid4(),
            phone=phone,
            code_hash=_hash_otp(code),
            expires_at=self.clock.utc_now() + _OTP_TTL,
        )
        self.otps.add(otp)

        try:
            self.sms.send_otp(phone=phone, code=code)
        except ExternalServiceError:
            self.uow.rollback()
            raise

        self.audit.record(actor=phone.value, action="auth.otp.requested")
        self.uow.commit()
        return RequestPhoneOtpOutput(
            phone=phone.value,
            expires_at=otp.expires_at,
            dev_code=code if self.expose_dev_code else None,
        )


@dataclass(frozen=True, slots=True)
class VerifyPhoneOtp:
    users: UserRepository
    credentials: WebAuthnCredentialRepository
    otps: PhoneOtpRepository
    audit: AuditLogRepository
    tokens: TokenService
    clock: Clock
    uow: UnitOfWork

    def execute(self, cmd: VerifyPhoneOtpInput) -> AuthSessionView:
        phone = PhoneE164(cmd.phone)
        pending = self.otps.get_latest_active_for_phone(phone)
        if pending is None:
            raise AuthenticationError("No active verification code for this phone.")
        if pending.is_expired(self.clock.utc_now()):
            raise AuthenticationError("Verification code expired. Request a new one.")
        if pending.attempts >= _OTP_MAX_ATTEMPTS:
            raise AuthenticationError("Too many incorrect attempts. Request a new code.")

        if _hash_otp(cmd.code.strip()) != pending.code_hash:
            pending.attempts += 1
            self.otps.update(pending)
            self.uow.commit()
            raise AuthenticationError("Incorrect verification code.")

        pending.consumed = True
        self.otps.update(pending)

        user = self.users.get_by_phone(phone)
        is_new = False
        if user is None:
            user = self._resolve_base_user(cmd.anonymous_user_id)
            user.phone = phone
            user.phone_verified = True
            user.display_name = cmd.display_name or user.display_name or phone.value
            if user.primary_provider == AuthProvider.ANONYMOUS:
                user.primary_provider = AuthProvider.PHONE
            is_new = True
        else:
            user.phone_verified = True

        user.touch_login(self.clock.utc_now())
        self.users.update(user)
        token = self.tokens.issue(user_id=user.id)
        self.audit.record(actor=str(user.id), action="auth.login.phone")
        self.uow.commit()

        has_passkey = bool(self.credentials.list_for_user(user.id))
        return build_session_view(
            user=user, token=token, has_passkey=has_passkey, is_new_user=is_new
        )

    def _resolve_base_user(self, anonymous_user_id: uuid.UUID | None) -> User:
        if anonymous_user_id is not None:
            existing = self.users.get_by_id(anonymous_user_id)
            if existing is not None and existing.is_anonymous:
                return existing
        return self.users.add(User.new())


# ---------- Google ----------


@dataclass(frozen=True, slots=True)
class SignInWithGoogle:
    users: UserRepository
    credentials: WebAuthnCredentialRepository
    verifier: GoogleTokenVerifier
    audit: AuditLogRepository
    tokens: TokenService
    clock: Clock
    uow: UnitOfWork

    def execute(self, cmd: SignInWithGoogleInput) -> AuthSessionView:
        claims = self.verifier.verify(cmd.id_token)
        user = self.users.get_by_google_sub(claims.sub)
        is_new = False

        if user is None and claims.email:
            # A user who signed up with email/password may now link Google by
            # reusing the same address.
            try:
                candidate = self.users.get_by_email(Email(claims.email))
            except ValueError:
                candidate = None
            if candidate is not None:
                candidate.google_sub = claims.sub
                candidate.email_verified = (
                    candidate.email_verified or bool(claims.email_verified)
                )
                user = candidate

        if user is None:
            user = self._resolve_base_user(cmd.anonymous_user_id)
            user.google_sub = claims.sub
            if claims.email:
                try:
                    user.email = Email(claims.email)
                    user.email_verified = bool(claims.email_verified)
                except ValueError:
                    pass
            user.display_name = claims.name or user.display_name
            user.primary_provider = AuthProvider.GOOGLE
            is_new = True

        user.touch_login(self.clock.utc_now())
        self.users.update(user)
        token = self.tokens.issue(user_id=user.id)
        self.audit.record(actor=str(user.id), action="auth.login.google")
        self.uow.commit()

        has_passkey = bool(self.credentials.list_for_user(user.id))
        return build_session_view(
            user=user, token=token, has_passkey=has_passkey, is_new_user=is_new
        )

    def _resolve_base_user(self, anonymous_user_id: uuid.UUID | None) -> User:
        if anonymous_user_id is not None:
            existing = self.users.get_by_id(anonymous_user_id)
            if existing is not None and existing.is_anonymous:
                return existing
        return self.users.add(User.new())


# ---------- WebAuthn (passkeys) ----------


@dataclass(frozen=True, slots=True)
class StartPasskeyRegistration:
    users: UserRepository
    credentials: WebAuthnCredentialRepository
    webauthn: WebAuthnService

    def execute(self, cmd: PasskeyRegisterStartInput) -> PasskeyChallengeView:
        user = self.users.get_by_id(cmd.user_id)
        if user is None:
            raise NotFoundError(f"User {cmd.user_id} not found.")
        existing = [c.credential_id for c in self.credentials.list_for_user(user.id)]
        name = (
            user.email.value
            if user.email
            else (user.phone.value if user.phone else str(user.id))
        )
        display = user.display_name or name
        result = self.webauthn.begin_registration(
            user_id=user.id,
            user_name=name,
            user_display_name=display,
            existing_credential_ids=existing,
        )
        return PasskeyChallengeView(
            options=result.options,
            challenge_b64=_b64url(result.challenge),
        )


@dataclass(frozen=True, slots=True)
class FinishPasskeyRegistration:
    users: UserRepository
    credentials: WebAuthnCredentialRepository
    webauthn: WebAuthnService
    audit: AuditLogRepository
    clock: Clock
    uow: UnitOfWork

    def execute(self, cmd: PasskeyRegisterFinishInput) -> AuthenticatedUserView:
        user = self.users.get_by_id(cmd.user_id)
        if user is None:
            raise NotFoundError(f"User {cmd.user_id} not found.")

        verified = self.webauthn.verify_registration(
            challenge=_b64url_decode(cmd.challenge_b64),
            response=cmd.response,
        )
        credential = WebAuthnCredential(
            id=uuid.uuid4(),
            user_id=user.id,
            credential_id=verified.credential_id,
            public_key=verified.public_key,
            sign_count=verified.sign_count,
            transports=verified.transports,
            label=cmd.label,
            created_at=self.clock.utc_now(),
        )
        self.credentials.add(credential)
        self.audit.record(actor=str(user.id), action="auth.passkey.registered")
        self.uow.commit()
        return build_authenticated_view(user=user, credentials=self.credentials)


@dataclass(frozen=True, slots=True)
class StartPasskeyLogin:
    users: UserRepository
    credentials: WebAuthnCredentialRepository
    webauthn: WebAuthnService

    def execute(self, cmd: PasskeyLoginStartInput) -> PasskeyChallengeView:
        allowed: list[WebAuthnCredential] = []
        if cmd.email:
            try:
                user = self.users.get_by_email(Email(cmd.email))
            except ValueError as exc:
                raise ValidationError("Invalid email address.") from exc
            if user is not None:
                allowed = self.credentials.list_for_user(user.id)
        result = self.webauthn.begin_authentication(allowed_credentials=allowed)
        return PasskeyChallengeView(
            options=result.options,
            challenge_b64=_b64url(result.challenge),
        )


@dataclass(frozen=True, slots=True)
class FinishPasskeyLogin:
    users: UserRepository
    credentials: WebAuthnCredentialRepository
    webauthn: WebAuthnService
    audit: AuditLogRepository
    tokens: TokenService
    clock: Clock
    uow: UnitOfWork

    def execute(self, cmd: PasskeyLoginFinishInput) -> AuthSessionView:
        raw_cid = cmd.response.get("rawId") or cmd.response.get("id")
        if not isinstance(raw_cid, str):
            raise AuthenticationError("Passkey response missing credential id.")
        credential_id = _b64url_decode(raw_cid)
        credential = self.credentials.get_by_credential_id(credential_id)
        if credential is None:
            raise AuthenticationError("Passkey is not registered for this service.")

        verified = self.webauthn.verify_authentication(
            challenge=_b64url_decode(cmd.challenge_b64),
            response=cmd.response,
            credential=credential,
        )
        credential.sign_count = verified.new_sign_count
        credential.last_used_at = self.clock.utc_now()
        self.credentials.update(credential)

        user = self.users.get_by_id(credential.user_id)
        if user is None:
            raise AuthenticationError("Passkey owner no longer exists.")
        user.touch_login(self.clock.utc_now())
        self.users.update(user)
        token = self.tokens.issue(user_id=user.id)
        self.audit.record(actor=str(user.id), action="auth.login.passkey")
        self.uow.commit()

        return build_session_view(user=user, token=token, has_passkey=True)


# ---------- Current user / account management ----------


@dataclass(frozen=True, slots=True)
class GetAuthenticatedUser:
    users: UserRepository
    credentials: WebAuthnCredentialRepository

    def execute(self, *, user_id: uuid.UUID) -> AuthenticatedUserView:
        user = self.users.get_by_id(user_id)
        if user is None:
            raise NotFoundError(f"User {user_id} not found.")
        return build_authenticated_view(user=user, credentials=self.credentials)
