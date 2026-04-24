from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends

from app.application.dtos import (
    AuthSessionView,
    AuthenticatedUserView,
    IssueTokenInput,
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
    IssueAccessToken,
    LogInWithEmail,
    RequestPhoneOtp,
    SignInWithGoogle,
    SignUpWithEmail,
    StartPasskeyLogin,
    StartPasskeyRegistration,
    VerifyPhoneOtp,
)
from app.config import settings
from app.interfaces.http.deps import (
    get_current_user_id,
    make_finish_passkey_login,
    make_finish_passkey_registration,
    make_get_authenticated_user,
    make_issue_access_token,
    make_login_with_email,
    make_request_phone_otp,
    make_signin_with_google,
    make_signup_with_email,
    make_start_passkey_login,
    make_start_passkey_registration,
    make_verify_phone_otp,
)
from app.interfaces.http.schemas.auth import (
    AuthenticatedUserResponse,
    AuthSessionRequest,
    GoogleSignInRequest,
    LogInEmailRequest,
    PasskeyChallengeResponse,
    PasskeyLoginFinishRequest,
    PasskeyLoginStartRequest,
    PasskeyRegisterFinishRequest,
    RequestPhoneOtpRequest,
    RequestPhoneOtpResponse,
    SessionResponse,
    SignUpEmailRequest,
    TokenResponse,
    VerifyPhoneOtpRequest,
)

router = APIRouter(tags=["auth"])


def _to_session_response(view: AuthSessionView) -> SessionResponse:
    return SessionResponse(
        access_token=view.access_token,
        token_type=view.token_type,
        user_id=view.user_id,
        email=view.email,
        phone=view.phone,
        display_name=view.display_name,
        primary_provider=view.primary_provider,
        email_verified=view.email_verified,
        phone_verified=view.phone_verified,
        has_password=view.has_password,
        has_passkey=view.has_passkey,
        is_new_user=view.is_new_user,
    )


@router.post("/auth/token", response_model=TokenResponse)
def issue_access_token(
    body: AuthSessionRequest = AuthSessionRequest(),
    uc: IssueAccessToken = Depends(make_issue_access_token),
) -> TokenResponse:
    """Issue or rotate an anonymous access token (legacy quiz-first flow)."""

    out = uc.execute(IssueTokenInput(user_id=body.user_id))
    return TokenResponse(
        access_token=out.access_token,
        token_type=out.token_type,
        user_id=out.user_id,
    )


@router.post("/auth/signup/email", response_model=SessionResponse)
def signup_email(
    body: SignUpEmailRequest,
    uc: SignUpWithEmail = Depends(make_signup_with_email),
) -> SessionResponse:
    out = uc.execute(
        SignUpWithEmailInput(
            email=body.email,
            password=body.password,
            display_name=body.display_name,
            anonymous_user_id=body.anonymous_user_id,
        )
    )
    return _to_session_response(out)


@router.post("/auth/login/email", response_model=SessionResponse)
def login_email(
    body: LogInEmailRequest,
    uc: LogInWithEmail = Depends(make_login_with_email),
) -> SessionResponse:
    out = uc.execute(LogInWithEmailInput(email=body.email, password=body.password))
    return _to_session_response(out)


@router.post("/auth/phone/request-otp", response_model=RequestPhoneOtpResponse)
def request_phone_otp(
    body: RequestPhoneOtpRequest,
    uc: RequestPhoneOtp = Depends(make_request_phone_otp),
) -> RequestPhoneOtpResponse:
    out = uc.execute(RequestPhoneOtpInput(phone=body.phone))
    return RequestPhoneOtpResponse(
        phone=out.phone,
        expires_at=out.expires_at,
        dev_code=out.dev_code,
    )


@router.post("/auth/phone/verify-otp", response_model=SessionResponse)
def verify_phone_otp(
    body: VerifyPhoneOtpRequest,
    uc: VerifyPhoneOtp = Depends(make_verify_phone_otp),
) -> SessionResponse:
    out = uc.execute(
        VerifyPhoneOtpInput(
            phone=body.phone,
            code=body.code,
            display_name=body.display_name,
            anonymous_user_id=body.anonymous_user_id,
        )
    )
    return _to_session_response(out)


@router.post("/auth/google", response_model=SessionResponse)
def signin_google(
    body: GoogleSignInRequest,
    uc: SignInWithGoogle = Depends(make_signin_with_google),
) -> SessionResponse:
    out = uc.execute(
        SignInWithGoogleInput(
            id_token=body.id_token,
            anonymous_user_id=body.anonymous_user_id,
        )
    )
    return _to_session_response(out)


@router.post(
    "/auth/webauthn/register/options",
    response_model=PasskeyChallengeResponse,
)
def passkey_register_options(
    user_id: uuid.UUID = Depends(get_current_user_id),
    uc: StartPasskeyRegistration = Depends(make_start_passkey_registration),
) -> PasskeyChallengeResponse:
    out = uc.execute(PasskeyRegisterStartInput(user_id=user_id))
    return PasskeyChallengeResponse(options=out.options, challenge=out.challenge_b64)


@router.post(
    "/auth/webauthn/register/verify",
    response_model=AuthenticatedUserResponse,
)
def passkey_register_verify(
    body: PasskeyRegisterFinishRequest,
    user_id: uuid.UUID = Depends(get_current_user_id),
    uc: FinishPasskeyRegistration = Depends(make_finish_passkey_registration),
) -> AuthenticatedUserResponse:
    out = uc.execute(
        PasskeyRegisterFinishInput(
            user_id=user_id,
            challenge_b64=body.challenge,
            response=body.response,
            label=body.label,
        )
    )
    return _authenticated_view_to_response(out)


@router.post(
    "/auth/webauthn/login/options",
    response_model=PasskeyChallengeResponse,
)
def passkey_login_options(
    body: PasskeyLoginStartRequest = PasskeyLoginStartRequest(),
    uc: StartPasskeyLogin = Depends(make_start_passkey_login),
) -> PasskeyChallengeResponse:
    out = uc.execute(PasskeyLoginStartInput(email=body.email))
    return PasskeyChallengeResponse(options=out.options, challenge=out.challenge_b64)


@router.post("/auth/webauthn/login/verify", response_model=SessionResponse)
def passkey_login_verify(
    body: PasskeyLoginFinishRequest,
    uc: FinishPasskeyLogin = Depends(make_finish_passkey_login),
) -> SessionResponse:
    out = uc.execute(
        PasskeyLoginFinishInput(challenge_b64=body.challenge, response=body.response)
    )
    return _to_session_response(out)


@router.get("/auth/me", response_model=AuthenticatedUserResponse)
def get_me(
    user_id: uuid.UUID = Depends(get_current_user_id),
    uc: GetAuthenticatedUser = Depends(make_get_authenticated_user),
) -> AuthenticatedUserResponse:
    out = uc.execute(user_id=user_id)
    return _authenticated_view_to_response(out)


def _authenticated_view_to_response(view: AuthenticatedUserView) -> AuthenticatedUserResponse:
    return AuthenticatedUserResponse(
        user_id=view.user_id,
        email=view.email,
        phone=view.phone,
        display_name=view.display_name,
        primary_provider=view.primary_provider,
        email_verified=view.email_verified,
        phone_verified=view.phone_verified,
        has_password=view.has_password,
        passkey_count=view.passkey_count,
        google_client_id=settings.google_client_id,
    )
