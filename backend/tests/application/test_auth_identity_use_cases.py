from __future__ import annotations

import base64
import uuid
from datetime import date, datetime, timedelta, timezone

import pytest

from app.application.dtos import (
    LogInWithEmailInput,
    PasskeyLoginFinishInput,
    PasskeyLoginStartInput,
    PasskeyRegisterFinishInput,
    PasskeyRegisterStartInput,
    RequestPhoneOtpInput,
    SignInWithGoogleInput,
    SignUpWithEmailInput,
    VerifyPhoneOtpInput,
)
from app.application.use_cases.auth import (
    FinishPasskeyLogin,
    FinishPasskeyRegistration,
    GetAuthenticatedUser,
    LogInWithEmail,
    RequestPhoneOtp,
    SignInWithGoogle,
    SignUpWithEmail,
    StartPasskeyLogin,
    StartPasskeyRegistration,
    VerifyPhoneOtp,
)
from app.domain.entities import User
from app.domain.errors import (
    AuthConflictError,
    AuthenticationError,
    NotFoundError,
    ValidationError,
)
from app.domain.value_objects import AuthProvider, Email, PhoneE164
from tests.fakes import (
    FakeAuditLogRepository,
    FakeClock,
    FakeGoogleTokenVerifier,
    FakeOtpCodeGenerator,
    FakePasswordHasher,
    FakePhoneOtpRepository,
    FakeSmsSender,
    FakeTokenService,
    FakeUnitOfWork,
    FakeUserRepository,
    FakeWebAuthnCredentialRepository,
    FakeWebAuthnService,
)


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _bundle():
    return {
        "users": FakeUserRepository(),
        "credentials": FakeWebAuthnCredentialRepository(),
        "hasher": FakePasswordHasher(),
        "audit": FakeAuditLogRepository(),
        "tokens": FakeTokenService(),
        "clock": FakeClock(today=date(2026, 4, 21)),
        "uow": FakeUnitOfWork(),
    }


# ---------- Email signup / login ----------


def test_signup_email_creates_authenticated_user_with_session():
    b = _bundle()
    uc = SignUpWithEmail(**b)
    out = uc.execute(
        SignUpWithEmailInput(email="Alice@Example.com", password="hunter22!", display_name="Alice")
    )
    assert out.is_new_user is True
    assert out.email == "alice@example.com"
    assert out.has_password is True
    assert out.primary_provider == AuthProvider.PASSWORD.value
    assert out.access_token == f"fake-token-for-{out.user_id}"
    assert b["users"].get_by_email(Email("alice@example.com")) is not None
    assert b["uow"].commits == 1


def test_signup_email_rejects_short_password():
    b = _bundle()
    uc = SignUpWithEmail(**b)
    with pytest.raises(ValidationError):
        uc.execute(SignUpWithEmailInput(email="bob@example.com", password="short"))


def test_signup_email_conflicts_when_email_already_taken():
    b = _bundle()
    SignUpWithEmail(**b).execute(
        SignUpWithEmailInput(email="dup@example.com", password="hunter22!")
    )
    with pytest.raises(AuthConflictError):
        SignUpWithEmail(**b).execute(
            SignUpWithEmailInput(email="dup@example.com", password="another1!")
        )


def test_signup_email_links_anonymous_user_id_when_anonymous():
    b = _bundle()
    anon = User.new()
    b["users"].add(anon)
    out = SignUpWithEmail(**b).execute(
        SignUpWithEmailInput(
            email="anon@example.com",
            password="hunter22!",
            anonymous_user_id=anon.id,
        )
    )
    # Same id is reused because it was anonymous.
    assert out.user_id == anon.id


def test_login_email_returns_session_on_correct_password():
    b = _bundle()
    SignUpWithEmail(**b).execute(
        SignUpWithEmailInput(email="bob@example.com", password="hunter22!")
    )
    out = LogInWithEmail(**b).execute(
        LogInWithEmailInput(email="bob@example.com", password="hunter22!")
    )
    assert out.email == "bob@example.com"
    assert out.has_password is True


def test_login_email_rejects_wrong_password():
    b = _bundle()
    SignUpWithEmail(**b).execute(
        SignUpWithEmailInput(email="bob@example.com", password="hunter22!")
    )
    with pytest.raises(AuthenticationError):
        LogInWithEmail(**b).execute(
            LogInWithEmailInput(email="bob@example.com", password="wrong-password")
        )


def test_login_email_rejects_unknown_user():
    b = _bundle()
    with pytest.raises(AuthenticationError):
        LogInWithEmail(**b).execute(
            LogInWithEmailInput(email="ghost@example.com", password="hunter22!")
        )


# ---------- Phone OTP ----------


def _phone_uc_bundle(*, expose_dev_code: bool = False):
    return {
        "otps": FakePhoneOtpRepository(),
        "sms": FakeSmsSender(),
        "code_generator": FakeOtpCodeGenerator("424242"),
        "clock": FakeClock(today=date(2026, 4, 21)),
        "audit": FakeAuditLogRepository(),
        "uow": FakeUnitOfWork(),
        "expose_dev_code": expose_dev_code,
    }


def test_request_phone_otp_dispatches_sms_and_persists_hashed_code():
    b = _phone_uc_bundle()
    out = RequestPhoneOtp(**b).execute(RequestPhoneOtpInput(phone="+15555550100"))
    assert out.phone == "+15555550100"
    assert out.dev_code is None
    assert b["sms"].sent == [("+15555550100", "424242")]
    assert len(b["otps"].added) == 1
    assert b["otps"].added[0].code_hash != "424242"  # stored hashed
    assert b["uow"].commits == 1


def test_request_phone_otp_exposes_dev_code_when_configured():
    b = _phone_uc_bundle(expose_dev_code=True)
    out = RequestPhoneOtp(**b).execute(RequestPhoneOtpInput(phone="+15555550100"))
    assert out.dev_code == "424242"


def test_request_phone_otp_rolls_back_when_sms_fails():
    b = _phone_uc_bundle()
    b["sms"] = FakeSmsSender(raise_external=True)
    from app.domain.errors import ExternalServiceError

    with pytest.raises(ExternalServiceError):
        RequestPhoneOtp(**b).execute(RequestPhoneOtpInput(phone="+15555550100"))
    assert b["uow"].commits == 0
    assert b["uow"].rollbacks == 1


def _verify_uc_bundle():
    return {
        "users": FakeUserRepository(),
        "credentials": FakeWebAuthnCredentialRepository(),
        "otps": FakePhoneOtpRepository(),
        "audit": FakeAuditLogRepository(),
        "tokens": FakeTokenService(),
        "clock": FakeClock(today=date(2026, 4, 21)),
        "uow": FakeUnitOfWork(),
    }


def test_verify_phone_otp_creates_user_and_marks_phone_verified():
    request_b = _phone_uc_bundle()
    RequestPhoneOtp(**request_b).execute(RequestPhoneOtpInput(phone="+15555550100"))

    verify_b = _verify_uc_bundle()
    verify_b["otps"] = request_b["otps"]
    verify_b["clock"] = request_b["clock"]

    out = VerifyPhoneOtp(**verify_b).execute(
        VerifyPhoneOtpInput(phone="+15555550100", code="424242")
    )
    assert out.is_new_user is True
    assert out.phone == "+15555550100"
    assert out.phone_verified is True
    assert out.primary_provider == AuthProvider.PHONE.value
    assert request_b["otps"].added[0].consumed is True


def test_verify_phone_otp_rejects_wrong_code_and_increments_attempts():
    request_b = _phone_uc_bundle()
    RequestPhoneOtp(**request_b).execute(RequestPhoneOtpInput(phone="+15555550100"))

    verify_b = _verify_uc_bundle()
    verify_b["otps"] = request_b["otps"]

    with pytest.raises(AuthenticationError):
        VerifyPhoneOtp(**verify_b).execute(
            VerifyPhoneOtpInput(phone="+15555550100", code="999999")
        )
    assert request_b["otps"].added[0].attempts == 1
    assert request_b["otps"].added[0].consumed is False


def test_verify_phone_otp_rejects_expired_code():
    request_b = _phone_uc_bundle()
    RequestPhoneOtp(**request_b).execute(RequestPhoneOtpInput(phone="+15555550100"))

    verify_b = _verify_uc_bundle()
    verify_b["otps"] = request_b["otps"]
    # Move clock 1 hour forward — TTL is 10 minutes.
    verify_b["clock"] = FakeClock(
        today=date(2026, 4, 21),
        now=datetime(2026, 4, 21, 1, 0, 0, tzinfo=timezone.utc),
    )

    with pytest.raises(AuthenticationError):
        VerifyPhoneOtp(**verify_b).execute(
            VerifyPhoneOtpInput(phone="+15555550100", code="424242")
        )


# ---------- Google ----------


def test_signin_google_creates_user_when_unknown():
    b = _bundle()
    verifier = FakeGoogleTokenVerifier(sub="g-1", email="newgoogle@example.com", name="Greg")
    out = SignInWithGoogle(
        users=b["users"],
        credentials=b["credentials"],
        verifier=verifier,
        audit=b["audit"],
        tokens=b["tokens"],
        clock=b["clock"],
        uow=b["uow"],
    ).execute(SignInWithGoogleInput(id_token="opaque"))
    assert out.is_new_user is True
    assert out.email == "newgoogle@example.com"
    assert out.primary_provider == AuthProvider.GOOGLE.value


def test_signin_google_links_existing_email_user():
    b = _bundle()
    SignUpWithEmail(**b).execute(
        SignUpWithEmailInput(email="link@example.com", password="hunter22!")
    )
    verifier = FakeGoogleTokenVerifier(sub="g-2", email="link@example.com")
    out = SignInWithGoogle(
        users=b["users"],
        credentials=b["credentials"],
        verifier=verifier,
        audit=b["audit"],
        tokens=b["tokens"],
        clock=b["clock"],
        uow=b["uow"],
    ).execute(SignInWithGoogleInput(id_token="opaque"))
    assert out.is_new_user is False
    assert b["users"].get_by_email(Email("link@example.com")).google_sub == "g-2"


# ---------- Passkey (WebAuthn) ----------


def _passkey_bundle():
    base = _bundle()
    base["webauthn"] = FakeWebAuthnService()
    return base


def test_passkey_register_round_trip_records_credential():
    b = _passkey_bundle()
    user = User.new()
    user.email = Email("pass@example.com")
    user.display_name = "Pass"
    b["users"].add(user)

    start = StartPasskeyRegistration(
        users=b["users"], credentials=b["credentials"], webauthn=b["webauthn"]
    ).execute(PasskeyRegisterStartInput(user_id=user.id))
    assert "options" in dir(start) or hasattr(start, "options")

    finish_uc = FinishPasskeyRegistration(
        users=b["users"],
        credentials=b["credentials"],
        webauthn=b["webauthn"],
        audit=b["audit"],
        clock=b["clock"],
        uow=b["uow"],
    )
    view = finish_uc.execute(
        PasskeyRegisterFinishInput(
            user_id=user.id,
            challenge_b64=start.challenge_b64,
            response={"id": "x"},
            label="MacBook",
        )
    )
    assert view.passkey_count == 1
    assert b["credentials"].list_for_user(user.id)[0].label == "MacBook"


def test_passkey_login_returns_session_for_registered_credential():
    b = _passkey_bundle()
    user = User.new()
    user.email = Email("pass@example.com")
    b["users"].add(user)

    finish_register = FinishPasskeyRegistration(
        users=b["users"],
        credentials=b["credentials"],
        webauthn=b["webauthn"],
        audit=b["audit"],
        clock=b["clock"],
        uow=b["uow"],
    )
    finish_register.execute(
        PasskeyRegisterFinishInput(
            user_id=user.id,
            challenge_b64=_b64url(b"reg-challenge"),
            response={"id": "x"},
        )
    )

    cred = b["credentials"].list_for_user(user.id)[0]
    initial_sign_count = cred.sign_count
    out = FinishPasskeyLogin(
        users=b["users"],
        credentials=b["credentials"],
        webauthn=b["webauthn"],
        audit=b["audit"],
        tokens=b["tokens"],
        clock=b["clock"],
        uow=b["uow"],
    ).execute(
        PasskeyLoginFinishInput(
            challenge_b64=_b64url(b"auth-challenge"),
            response={"rawId": _b64url(cred.credential_id)},
        )
    )
    assert out.user_id == user.id
    assert out.has_passkey is True
    assert b["credentials"].list_for_user(user.id)[0].sign_count == initial_sign_count + 1


def test_passkey_login_rejects_unknown_credential():
    b = _passkey_bundle()
    with pytest.raises(AuthenticationError):
        FinishPasskeyLogin(
            users=b["users"],
            credentials=b["credentials"],
            webauthn=b["webauthn"],
            audit=b["audit"],
            tokens=b["tokens"],
            clock=b["clock"],
            uow=b["uow"],
        ).execute(
            PasskeyLoginFinishInput(
                challenge_b64=_b64url(b"auth-challenge"),
                response={"rawId": _b64url(b"never-seen")},
            )
        )


# ---------- /auth/me ----------


def test_get_authenticated_user_returns_view():
    b = _bundle()
    out = SignUpWithEmail(**b).execute(
        SignUpWithEmailInput(email="me@example.com", password="hunter22!")
    )
    me = GetAuthenticatedUser(users=b["users"], credentials=b["credentials"]).execute(
        user_id=out.user_id
    )
    assert me.email == "me@example.com"
    assert me.has_password is True
    assert me.passkey_count == 0


def test_get_authenticated_user_404s_when_missing():
    b = _bundle()
    with pytest.raises(NotFoundError):
        GetAuthenticatedUser(users=b["users"], credentials=b["credentials"]).execute(
            user_id=uuid.uuid4()
        )
