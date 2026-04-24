"""In-memory fakes for application ports. Used in use-case tests.

These are deliberately simple and hold state in plain dicts/lists. They implement
the port protocols structurally — no infrastructure (no DB, no SDK) is involved.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from typing import Any

from app.application.ports.google_token_verifier import GoogleIdClaims
from app.application.ports.llm_gateway import GroundedReply
from app.application.ports.webauthn_service import (
    AuthenticationChallenge,
    RegistrationChallenge,
    VerifiedAuthentication,
    VerifiedRegistration,
)
from app.domain.entities import (
    ChatMessage,
    DailyCheckIn,
    DailyEnvironmentTip,
    HealthProfile,
    PhoneOtp,
    User,
    WebAuthnCredential,
    WeeklyPlan,
)
from app.domain.errors import AuthenticationError, ConfigurationError
from app.domain.value_objects import Citation, Email, PhoneE164


class FakeClock:
    def __init__(self, today: date, now: datetime | None = None) -> None:
        self._today = today
        self._now = now or datetime.combine(today, datetime.min.time()).replace(tzinfo=timezone.utc)

    def today(self) -> date:
        return self._today

    def utc_now(self) -> datetime:
        return self._now

    def utc_today(self) -> date:
        return self._now.date()

    # Back-compat alias kept so existing tests / callers continue to work.
    def now_utc(self) -> datetime:
        return self._now


class FakeUnitOfWork:
    def __init__(self) -> None:
        self.commits = 0
        self.rollbacks = 0

    def commit(self) -> None:
        self.commits += 1

    def rollback(self) -> None:
        self.rollbacks += 1


class FakeUserRepository:
    def __init__(self, users: list[User] | None = None) -> None:
        self._by_id: dict[uuid.UUID, User] = {u.id: u for u in (users or [])}
        self._with_profile: set[uuid.UUID] = set()

    def get_by_id(self, user_id: uuid.UUID) -> User | None:
        return self._by_id.get(user_id)

    def get_by_email(self, email: Email) -> User | None:
        return next(
            (u for u in self._by_id.values() if u.email and u.email.value == email.value),
            None,
        )

    def get_by_phone(self, phone: PhoneE164) -> User | None:
        return next(
            (u for u in self._by_id.values() if u.phone and u.phone.value == phone.value),
            None,
        )

    def get_by_google_sub(self, google_sub: str) -> User | None:
        return next(
            (u for u in self._by_id.values() if u.google_sub == google_sub),
            None,
        )

    def add(self, user: User) -> User:
        self._by_id[user.id] = user
        return user

    def update(self, user: User) -> User:
        self._by_id[user.id] = user
        return user

    def list_ids_with_profile(self) -> list[uuid.UUID]:
        return list(self._with_profile)

    def mark_has_profile(self, user_id: uuid.UUID) -> None:
        self._with_profile.add(user_id)


class FakeHealthProfileRepository:
    def __init__(self) -> None:
        self._by_user: dict[uuid.UUID, HealthProfile] = {}

    def get_by_user_id(self, user_id: uuid.UUID) -> HealthProfile | None:
        return self._by_user.get(user_id)

    def upsert(self, profile: HealthProfile) -> HealthProfile:
        self._by_user[profile.user_id] = profile
        return profile


class FakeChatRepository:
    def __init__(self) -> None:
        self.messages: list[ChatMessage] = []

    def add(self, message: ChatMessage) -> ChatMessage:
        self.messages.append(message)
        return message

    def list_recent_user_messages(
        self, user_id: uuid.UUID, days: int = 7, limit: int = 80
    ) -> list[ChatMessage]:
        return [
            m for m in self.messages if m.user_id == user_id and m.role.value == "user"
        ][:limit]

    def list_semantic_user_messages(
        self,
        user_id: uuid.UUID,
        query_embedding: list[float],
        days: int = 7,
        limit: int = 5,
    ) -> list[ChatMessage]:
        return []


class FakeCheckInRepository:
    def __init__(self) -> None:
        self._by_user_date: dict[tuple[uuid.UUID, date], DailyCheckIn] = {}

    def get_for_date(self, user_id: uuid.UUID, d: date) -> DailyCheckIn | None:
        return self._by_user_date.get((user_id, d))

    def list_week(
        self, user_id: uuid.UUID, start: date, end: date
    ) -> list[DailyCheckIn]:
        return sorted(
            (
                ci
                for (uid, d), ci in self._by_user_date.items()
                if uid == user_id and start <= d <= end
            ),
            key=lambda c: c.check_in_date,
        )

    def upsert(self, check_in: DailyCheckIn) -> DailyCheckIn:
        self._by_user_date[(check_in.user_id, check_in.check_in_date)] = check_in
        return check_in


class FakeWeeklyPlanRepository:
    def __init__(self) -> None:
        self._by_user_week: dict[tuple[uuid.UUID, date], WeeklyPlan] = {}

    def get_for_week(
        self, user_id: uuid.UUID, week_start: date
    ) -> WeeklyPlan | None:
        return self._by_user_week.get((user_id, week_start))

    def upsert(self, plan: WeeklyPlan) -> WeeklyPlan:
        self._by_user_week[(plan.user_id, plan.start_date)] = plan
        return plan

    def save_envelope(self, plan: WeeklyPlan) -> WeeklyPlan:
        self._by_user_week[(plan.user_id, plan.start_date)] = plan
        return plan


class FakeEnvironmentTipRepository:
    def __init__(self) -> None:
        self._by_user_date: dict[tuple[uuid.UUID, date], DailyEnvironmentTip] = {}

    def get_for_date(
        self, user_id: uuid.UUID, tip_date: date
    ) -> DailyEnvironmentTip | None:
        return self._by_user_date.get((user_id, tip_date))

    def add(self, tip: DailyEnvironmentTip) -> DailyEnvironmentTip:
        self._by_user_date[(tip.user_id, tip.tip_date)] = tip
        return tip


class FakeAuditLogRepository:
    def __init__(self) -> None:
        self.records: list[tuple[str, str]] = []

    def record(self, actor: str, action: str) -> None:
        self.records.append((actor, action))


class FakeTokenService:
    def __init__(self) -> None:
        self.issued: list[uuid.UUID] = []

    def issue(self, *, user_id: uuid.UUID) -> str:
        self.issued.append(user_id)
        return f"fake-token-for-{user_id}"

    def verify(self, token: str) -> uuid.UUID:
        if not token.startswith("fake-token-for-"):
            raise ValueError("invalid token")
        return uuid.UUID(token.removeprefix("fake-token-for-"))


class FakeLLMGateway:
    """LLM gateway that returns canned outputs. Override attributes as needed."""

    def __init__(
        self,
        *,
        embedding: list[float] | None = None,
        reply_text: str = "Here is some gentle guidance.",
        plan_json: str | None = None,
        followup_json: str = '{"task": "10 minute walk", "context_reason": "Builds on your movement goal."}',
        daily_tip_json: str = '{"tip_title": "Hydrate Mindfully", "tip_description": "Sip warm water.", "icon_name": "droplet"}',
        citations: tuple[Citation, ...] = (),
        search_queries: tuple[str, ...] = (),
    ) -> None:
        self._embedding = embedding if embedding is not None else [0.1] * 8
        self._reply_text = reply_text
        self._plan_json = plan_json or _default_plan_json()
        self._followup_json = followup_json
        self._daily_tip_json = daily_tip_json
        self._citations = citations
        self._search_queries = search_queries
        self.calls: list[str] = []

    def embed(self, text: str) -> list[float]:
        self.calls.append(f"embed:{text[:20]}")
        return list(self._embedding)

    def generate_health_reply(
        self,
        *,
        user_message: str,
        profile_blob_json: str,
        recent_history_block: str,
        semantic_history_block: str,
        environment_block: str | None,
    ) -> GroundedReply:
        self.calls.append("generate_health_reply")
        return GroundedReply(
            reply_text=self._reply_text,
            citations=self._citations,
            search_queries=self._search_queries,
        )

    def generate_weekly_plan_json(
        self,
        *,
        profile_blob_json: str,
        recent_history_block: str,
        semantic_history_block: str,
        week_start_iso: str,
        week_end_iso: str,
    ) -> str:
        self.calls.append("generate_weekly_plan_json")
        return self._plan_json

    def generate_followup_task_json(
        self,
        *,
        pillar: str,
        completed_task: str,
        completed_context: str,
        plan_day_date: str,
        profile_blob_json: str,
        recent_history_block: str,
    ) -> str:
        self.calls.append("generate_followup_task_json")
        return self._followup_json

    def generate_environment_tip_json(
        self,
        *,
        profile_blob_json: str,
        dominant_dosha: str | None,
        environment_blob_json: str,
    ) -> str:
        self.calls.append("generate_environment_tip_json")
        return self._daily_tip_json


class FakeWeatherGateway:
    def __init__(self, ctx: dict[str, str] | None = None) -> None:
        self.ctx = ctx or {"weather": "20°C, clear", "humidity_type": "balanced", "habitat": "Rural"}

    async def get_context(self, *, lat: float, lon: float) -> dict[str, str]:
        return dict(self.ctx)


class FakePasswordHasher:
    """Reversible 'hash' (prefix-based) so tests can assert + verify cheaply."""

    def hash(self, plaintext: str) -> str:
        return f"hashed:{plaintext}"

    def verify(self, plaintext: str, hashed: str) -> bool:
        return hashed == f"hashed:{plaintext}"


class FakeOtpCodeGenerator:
    def __init__(self, code: str = "123456") -> None:
        self.code = code

    def generate(self) -> str:
        return self.code


class FakeSmsSender:
    def __init__(self, *, raise_external: bool = False) -> None:
        self.sent: list[tuple[str, str]] = []
        self.raise_external = raise_external

    def send_otp(self, *, phone: PhoneE164, code: str) -> None:
        if self.raise_external:
            from app.domain.errors import ExternalServiceError

            raise ExternalServiceError("sms provider down")
        self.sent.append((phone.value, code))


class FakePhoneOtpRepository:
    def __init__(self) -> None:
        self.added: list[PhoneOtp] = []
        self.updated: list[PhoneOtp] = []

    def add(self, otp: PhoneOtp) -> PhoneOtp:
        self.added.append(otp)
        return otp

    def get_latest_active_for_phone(self, phone: PhoneE164) -> PhoneOtp | None:
        candidates = [
            o for o in self.added if o.phone.value == phone.value and not o.consumed
        ]
        return candidates[-1] if candidates else None

    def update(self, otp: PhoneOtp) -> PhoneOtp:
        self.updated.append(otp)
        return otp


class FakeWebAuthnCredentialRepository:
    def __init__(self) -> None:
        self._by_id: dict[uuid.UUID, WebAuthnCredential] = {}

    def add(self, credential: WebAuthnCredential) -> WebAuthnCredential:
        self._by_id[credential.id] = credential
        return credential

    def list_for_user(self, user_id: uuid.UUID) -> list[WebAuthnCredential]:
        return [c for c in self._by_id.values() if c.user_id == user_id]

    def get_by_credential_id(self, credential_id: bytes) -> WebAuthnCredential | None:
        return next(
            (c for c in self._by_id.values() if c.credential_id == credential_id),
            None,
        )

    def update(self, credential: WebAuthnCredential) -> WebAuthnCredential:
        self._by_id[credential.id] = credential
        return credential

    def delete(self, credential_id: uuid.UUID) -> None:
        self._by_id.pop(credential_id, None)


class FakeGoogleTokenVerifier:
    def __init__(
        self,
        *,
        sub: str = "google-sub-1",
        email: str | None = "alice@example.com",
        email_verified: bool = True,
        name: str | None = "Alice",
        configured: bool = True,
        valid: bool = True,
    ) -> None:
        self.claims = GoogleIdClaims(
            sub=sub, email=email, email_verified=email_verified, name=name
        )
        self.configured = configured
        self.valid = valid
        self.calls: list[str] = []

    def verify(self, id_token: str):
        self.calls.append(id_token)
        if not self.configured:
            raise ConfigurationError("Google sign-in is not configured.")
        if not self.valid:
            raise AuthenticationError("Google token invalid.")
        return self.claims


class FakeWebAuthnService:
    """Trivial passkey adapter: ``response['rawId']`` is the credential id (b64url)."""

    def __init__(self) -> None:
        self.next_credential_id: bytes = b"cred-1"
        self.next_public_key: bytes = b"pubkey-bytes"
        self.next_sign_count: int = 1

    def begin_registration(
        self,
        *,
        user_id: uuid.UUID,
        user_name: str,
        user_display_name: str,
        existing_credential_ids: list[bytes],
    ) -> RegistrationChallenge:
        return RegistrationChallenge(
            options={"rp": {"id": "test"}, "user": {"name": user_name}},
            challenge=b"reg-challenge",
        )

    def verify_registration(
        self, *, challenge: bytes, response: dict[str, Any]
    ) -> VerifiedRegistration:
        return VerifiedRegistration(
            credential_id=self.next_credential_id,
            public_key=self.next_public_key,
            sign_count=self.next_sign_count,
            transports=("internal",),
        )

    def begin_authentication(
        self, *, allowed_credentials: list[WebAuthnCredential]
    ) -> AuthenticationChallenge:
        return AuthenticationChallenge(
            options={"allow": [c.credential_id.hex() for c in allowed_credentials]},
            challenge=b"auth-challenge",
        )

    def verify_authentication(
        self,
        *,
        challenge: bytes,
        response: dict[str, Any],
        credential: WebAuthnCredential,
    ) -> VerifiedAuthentication:
        return VerifiedAuthentication(
            credential_id=credential.credential_id,
            new_sign_count=credential.sign_count + 1,
        )


def _default_plan_json() -> str:
    return (
        '{"daily_focus_message": "Steady week",'
        ' "days": [{"date": "2026-04-20", "pillars": {'
        '"Mind": [{"task": "Breathwork", "context_reason": "Calm"}],'
        '"Fuel": [{"task": "Warm soup", "context_reason": "Gentle"}],'
        '"Body": [{"task": "Walk", "context_reason": "Movement"}]'
        "}}]}"
    )
