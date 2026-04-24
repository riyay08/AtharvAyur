"""FastAPI dependency providers.

This is the single place that knows how to wire concrete adapters to the
abstract ports that use cases depend on. Add a new port here and every
use case that needs it can pull it via FastAPI's `Depends`.
"""

from __future__ import annotations

import uuid
from collections.abc import Generator

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.application.ports.clock import Clock
from app.application.ports.google_token_verifier import GoogleTokenVerifier
from app.application.ports.llm_gateway import LLMGateway
from app.application.ports.otp_code_generator import OtpCodeGenerator
from app.application.ports.password_hasher import PasswordHasher
from app.application.ports.sms_sender import SmsSender
from app.application.ports.token_service import TokenService
from app.application.ports.weather_gateway import WeatherGateway
from app.application.ports.webauthn_service import WebAuthnService
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
from app.application.use_cases.chat import GenerateHealthReply
from app.application.use_cases.checkin import GetCheckInWeek, UpsertCheckIn
from app.application.use_cases.environment import GetOrCreateDailyEnvironmentTip
from app.application.use_cases.plan import (
    GenerateWeeklyPlan,
    GenerateWeeklyPlansForAllUsers,
    GetCurrentPlan,
    UpdatePlanTask,
)
from app.application.use_cases.profile import GetProfileMe, UpsertProfile
from app.config import settings
from app.database import get_session_factory
from app.domain.errors import ConfigurationError, ValidationError
from app.infrastructure.auth.bcrypt_password_hasher import BcryptPasswordHasher
from app.infrastructure.auth.google_token_verifier import GoogleIdTokenVerifier
from app.infrastructure.auth.jose_token_service import JoseTokenService
from app.infrastructure.auth.otp_code_generator import SecureOtpCodeGenerator
from app.infrastructure.auth.py_webauthn_service import PyWebAuthnService
from app.infrastructure.db.repositories.audit_log_repository import SqlAlchemyAuditLogRepository
from app.infrastructure.db.repositories.chat_repository import SqlAlchemyChatRepository
from app.infrastructure.db.repositories.checkin_repository import SqlAlchemyCheckInRepository
from app.infrastructure.db.repositories.environment_tip_repository import (
    SqlAlchemyEnvironmentTipRepository,
)
from app.infrastructure.db.repositories.health_profile_repository import (
    SqlAlchemyHealthProfileRepository,
)
from app.infrastructure.db.repositories.phone_otp_repository import (
    SqlAlchemyPhoneOtpRepository,
)
from app.infrastructure.db.repositories.user_repository import SqlAlchemyUserRepository
from app.infrastructure.db.repositories.webauthn_credential_repository import (
    SqlAlchemyWebAuthnCredentialRepository,
)
from app.infrastructure.db.repositories.weekly_plan_repository import (
    SqlAlchemyWeeklyPlanRepository,
)
from app.infrastructure.db.unit_of_work import SqlAlchemyUnitOfWork
from app.infrastructure.llm.factory import make_llm_gateway
from app.infrastructure.sms.stub_sms_sender import StubSmsSender
from app.infrastructure.time.system_clock import SystemClock
from app.infrastructure.weather.openweather_gateway import OpenWeatherWeatherGateway
from app.models.user import User as UserORM


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


# ---------- Session / UoW ----------


def get_db() -> Generator[Session, None, None]:
    session_local = get_session_factory()
    db = session_local()
    try:
        yield db
    finally:
        db.close()


def get_uow(db: Session = Depends(get_db)) -> SqlAlchemyUnitOfWork:
    return SqlAlchemyUnitOfWork(db)


# ---------- Singletons (resolved per request but cheap) ----------


def get_clock() -> Clock:
    return SystemClock()


def get_token_service() -> TokenService:
    return JoseTokenService()


def get_llm_gateway() -> LLMGateway:
    try:
        return make_llm_gateway()
    except ConfigurationError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc


def get_weather_gateway() -> WeatherGateway:
    return OpenWeatherWeatherGateway()


def get_password_hasher() -> PasswordHasher:
    return BcryptPasswordHasher()


def get_sms_sender() -> SmsSender:
    return StubSmsSender()


def get_otp_code_generator() -> OtpCodeGenerator:
    return SecureOtpCodeGenerator()


def get_google_token_verifier() -> GoogleTokenVerifier:
    return GoogleIdTokenVerifier()


def get_webauthn_service() -> WebAuthnService:
    return PyWebAuthnService()


# ---------- Current user (authenticated) ----------


def get_current_user_id(
    token: str = Depends(oauth2_scheme),
    tokens: TokenService = Depends(get_token_service),
    db: Session = Depends(get_db),
) -> uuid.UUID:
    invalid = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        user_id = tokens.verify(token)
    except ValidationError as exc:
        raise invalid from exc
    # Verify the user still exists.
    if db.get(UserORM, user_id) is None:
        raise invalid
    return user_id


# ---------- Repositories ----------


def get_user_repo(db: Session = Depends(get_db)) -> SqlAlchemyUserRepository:
    return SqlAlchemyUserRepository(db)


def get_profile_repo(db: Session = Depends(get_db)) -> SqlAlchemyHealthProfileRepository:
    return SqlAlchemyHealthProfileRepository(db)


def get_chat_repo(db: Session = Depends(get_db)) -> SqlAlchemyChatRepository:
    return SqlAlchemyChatRepository(db)


def get_checkin_repo(db: Session = Depends(get_db)) -> SqlAlchemyCheckInRepository:
    return SqlAlchemyCheckInRepository(db)


def get_plan_repo(db: Session = Depends(get_db)) -> SqlAlchemyWeeklyPlanRepository:
    return SqlAlchemyWeeklyPlanRepository(db)


def get_tip_repo(db: Session = Depends(get_db)) -> SqlAlchemyEnvironmentTipRepository:
    return SqlAlchemyEnvironmentTipRepository(db)


def get_audit_repo(db: Session = Depends(get_db)) -> SqlAlchemyAuditLogRepository:
    return SqlAlchemyAuditLogRepository(db)


def get_phone_otp_repo(db: Session = Depends(get_db)) -> SqlAlchemyPhoneOtpRepository:
    return SqlAlchemyPhoneOtpRepository(db)


def get_webauthn_repo(
    db: Session = Depends(get_db),
) -> SqlAlchemyWebAuthnCredentialRepository:
    return SqlAlchemyWebAuthnCredentialRepository(db)


# ---------- Use cases ----------


def make_issue_access_token(
    users: SqlAlchemyUserRepository = Depends(get_user_repo),
    audit: SqlAlchemyAuditLogRepository = Depends(get_audit_repo),
    tokens: TokenService = Depends(get_token_service),
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
) -> IssueAccessToken:
    return IssueAccessToken(users=users, audit=audit, tokens=tokens, uow=uow)


def make_upsert_profile(
    users: SqlAlchemyUserRepository = Depends(get_user_repo),
    profiles: SqlAlchemyHealthProfileRepository = Depends(get_profile_repo),
    audit: SqlAlchemyAuditLogRepository = Depends(get_audit_repo),
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
) -> UpsertProfile:
    return UpsertProfile(users=users, profiles=profiles, audit=audit, uow=uow)


def make_get_profile_me(
    users: SqlAlchemyUserRepository = Depends(get_user_repo),
    profiles: SqlAlchemyHealthProfileRepository = Depends(get_profile_repo),
    check_ins: SqlAlchemyCheckInRepository = Depends(get_checkin_repo),
    plans: SqlAlchemyWeeklyPlanRepository = Depends(get_plan_repo),
    clock: Clock = Depends(get_clock),
) -> GetProfileMe:
    return GetProfileMe(
        users=users, profiles=profiles, check_ins=check_ins, plans=plans, clock=clock
    )


def make_upsert_checkin(
    check_ins: SqlAlchemyCheckInRepository = Depends(get_checkin_repo),
    audit: SqlAlchemyAuditLogRepository = Depends(get_audit_repo),
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
) -> UpsertCheckIn:
    return UpsertCheckIn(check_ins=check_ins, audit=audit, uow=uow)


def make_get_checkin_week(
    check_ins: SqlAlchemyCheckInRepository = Depends(get_checkin_repo),
    clock: Clock = Depends(get_clock),
) -> GetCheckInWeek:
    return GetCheckInWeek(check_ins=check_ins, clock=clock)


def make_chat_use_case(
    chat_repo: SqlAlchemyChatRepository = Depends(get_chat_repo),
    profiles: SqlAlchemyHealthProfileRepository = Depends(get_profile_repo),
    audit: SqlAlchemyAuditLogRepository = Depends(get_audit_repo),
    llm: LLMGateway = Depends(get_llm_gateway),
    weather: WeatherGateway = Depends(get_weather_gateway),
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
) -> GenerateHealthReply:
    return GenerateHealthReply(
        chat_repo=chat_repo,
        profiles=profiles,
        audit=audit,
        llm=llm,
        weather=weather,
        uow=uow,
    )


def make_environment_tip(
    tips: SqlAlchemyEnvironmentTipRepository = Depends(get_tip_repo),
    profiles: SqlAlchemyHealthProfileRepository = Depends(get_profile_repo),
    audit: SqlAlchemyAuditLogRepository = Depends(get_audit_repo),
    weather: WeatherGateway = Depends(get_weather_gateway),
    llm: LLMGateway = Depends(get_llm_gateway),
    clock: Clock = Depends(get_clock),
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
) -> GetOrCreateDailyEnvironmentTip:
    return GetOrCreateDailyEnvironmentTip(
        tips=tips,
        profiles=profiles,
        audit=audit,
        weather=weather,
        llm=llm,
        clock=clock,
        uow=uow,
    )


def make_generate_plan(
    profiles: SqlAlchemyHealthProfileRepository = Depends(get_profile_repo),
    chat: SqlAlchemyChatRepository = Depends(get_chat_repo),
    plans: SqlAlchemyWeeklyPlanRepository = Depends(get_plan_repo),
    audit: SqlAlchemyAuditLogRepository = Depends(get_audit_repo),
    llm: LLMGateway = Depends(get_llm_gateway),
    clock: Clock = Depends(get_clock),
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
) -> GenerateWeeklyPlan:
    return GenerateWeeklyPlan(
        profiles=profiles, chat=chat, plans=plans, audit=audit, llm=llm, clock=clock, uow=uow
    )


def make_get_current_plan(
    plans: SqlAlchemyWeeklyPlanRepository = Depends(get_plan_repo),
    clock: Clock = Depends(get_clock),
) -> GetCurrentPlan:
    return GetCurrentPlan(plans=plans, clock=clock)


def make_update_plan_task(
    profiles: SqlAlchemyHealthProfileRepository = Depends(get_profile_repo),
    plans: SqlAlchemyWeeklyPlanRepository = Depends(get_plan_repo),
    audit: SqlAlchemyAuditLogRepository = Depends(get_audit_repo),
    llm: LLMGateway = Depends(get_llm_gateway),
    clock: Clock = Depends(get_clock),
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
) -> UpdatePlanTask:
    return UpdatePlanTask(
        profiles=profiles, plans=plans, audit=audit, llm=llm, clock=clock, uow=uow
    )


# ---------- Auth use cases ----------


def make_signup_with_email(
    users: SqlAlchemyUserRepository = Depends(get_user_repo),
    credentials: SqlAlchemyWebAuthnCredentialRepository = Depends(get_webauthn_repo),
    hasher: PasswordHasher = Depends(get_password_hasher),
    audit: SqlAlchemyAuditLogRepository = Depends(get_audit_repo),
    tokens: TokenService = Depends(get_token_service),
    clock: Clock = Depends(get_clock),
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
) -> SignUpWithEmail:
    return SignUpWithEmail(
        users=users,
        credentials=credentials,
        hasher=hasher,
        audit=audit,
        tokens=tokens,
        clock=clock,
        uow=uow,
    )


def make_login_with_email(
    users: SqlAlchemyUserRepository = Depends(get_user_repo),
    credentials: SqlAlchemyWebAuthnCredentialRepository = Depends(get_webauthn_repo),
    hasher: PasswordHasher = Depends(get_password_hasher),
    audit: SqlAlchemyAuditLogRepository = Depends(get_audit_repo),
    tokens: TokenService = Depends(get_token_service),
    clock: Clock = Depends(get_clock),
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
) -> LogInWithEmail:
    return LogInWithEmail(
        users=users,
        credentials=credentials,
        hasher=hasher,
        audit=audit,
        tokens=tokens,
        clock=clock,
        uow=uow,
    )


def make_request_phone_otp(
    otps: SqlAlchemyPhoneOtpRepository = Depends(get_phone_otp_repo),
    sms: SmsSender = Depends(get_sms_sender),
    code_generator: OtpCodeGenerator = Depends(get_otp_code_generator),
    clock: Clock = Depends(get_clock),
    audit: SqlAlchemyAuditLogRepository = Depends(get_audit_repo),
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
) -> RequestPhoneOtp:
    return RequestPhoneOtp(
        otps=otps,
        sms=sms,
        code_generator=code_generator,
        clock=clock,
        audit=audit,
        uow=uow,
        expose_dev_code=settings.auth_expose_dev_otp,
    )


def make_verify_phone_otp(
    users: SqlAlchemyUserRepository = Depends(get_user_repo),
    credentials: SqlAlchemyWebAuthnCredentialRepository = Depends(get_webauthn_repo),
    otps: SqlAlchemyPhoneOtpRepository = Depends(get_phone_otp_repo),
    audit: SqlAlchemyAuditLogRepository = Depends(get_audit_repo),
    tokens: TokenService = Depends(get_token_service),
    clock: Clock = Depends(get_clock),
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
) -> VerifyPhoneOtp:
    return VerifyPhoneOtp(
        users=users,
        credentials=credentials,
        otps=otps,
        audit=audit,
        tokens=tokens,
        clock=clock,
        uow=uow,
    )


def make_signin_with_google(
    users: SqlAlchemyUserRepository = Depends(get_user_repo),
    credentials: SqlAlchemyWebAuthnCredentialRepository = Depends(get_webauthn_repo),
    verifier: GoogleTokenVerifier = Depends(get_google_token_verifier),
    audit: SqlAlchemyAuditLogRepository = Depends(get_audit_repo),
    tokens: TokenService = Depends(get_token_service),
    clock: Clock = Depends(get_clock),
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
) -> SignInWithGoogle:
    return SignInWithGoogle(
        users=users,
        credentials=credentials,
        verifier=verifier,
        audit=audit,
        tokens=tokens,
        clock=clock,
        uow=uow,
    )


def make_start_passkey_registration(
    users: SqlAlchemyUserRepository = Depends(get_user_repo),
    credentials: SqlAlchemyWebAuthnCredentialRepository = Depends(get_webauthn_repo),
    webauthn: WebAuthnService = Depends(get_webauthn_service),
) -> StartPasskeyRegistration:
    return StartPasskeyRegistration(
        users=users, credentials=credentials, webauthn=webauthn
    )


def make_finish_passkey_registration(
    users: SqlAlchemyUserRepository = Depends(get_user_repo),
    credentials: SqlAlchemyWebAuthnCredentialRepository = Depends(get_webauthn_repo),
    webauthn: WebAuthnService = Depends(get_webauthn_service),
    audit: SqlAlchemyAuditLogRepository = Depends(get_audit_repo),
    clock: Clock = Depends(get_clock),
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
) -> FinishPasskeyRegistration:
    return FinishPasskeyRegistration(
        users=users,
        credentials=credentials,
        webauthn=webauthn,
        audit=audit,
        clock=clock,
        uow=uow,
    )


def make_start_passkey_login(
    users: SqlAlchemyUserRepository = Depends(get_user_repo),
    credentials: SqlAlchemyWebAuthnCredentialRepository = Depends(get_webauthn_repo),
    webauthn: WebAuthnService = Depends(get_webauthn_service),
) -> StartPasskeyLogin:
    return StartPasskeyLogin(
        users=users, credentials=credentials, webauthn=webauthn
    )


def make_finish_passkey_login(
    users: SqlAlchemyUserRepository = Depends(get_user_repo),
    credentials: SqlAlchemyWebAuthnCredentialRepository = Depends(get_webauthn_repo),
    webauthn: WebAuthnService = Depends(get_webauthn_service),
    audit: SqlAlchemyAuditLogRepository = Depends(get_audit_repo),
    tokens: TokenService = Depends(get_token_service),
    clock: Clock = Depends(get_clock),
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
) -> FinishPasskeyLogin:
    return FinishPasskeyLogin(
        users=users,
        credentials=credentials,
        webauthn=webauthn,
        audit=audit,
        tokens=tokens,
        clock=clock,
        uow=uow,
    )


def make_get_authenticated_user(
    users: SqlAlchemyUserRepository = Depends(get_user_repo),
    credentials: SqlAlchemyWebAuthnCredentialRepository = Depends(get_webauthn_repo),
) -> GetAuthenticatedUser:
    return GetAuthenticatedUser(users=users, credentials=credentials)
