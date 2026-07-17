"""Repository port interfaces.

Repositories hide persistence and translate ORM rows to domain entities. Use cases
depend only on these Protocols; infrastructure supplies concrete SQLAlchemy impls.
"""

from __future__ import annotations

import uuid
from datetime import date
from typing import Protocol, Sequence

from app.domain.entities import (
    ChatMessage,
    Conversation,
    DailyCheckIn,
    DailyEnvironmentTip,
    HealthProfile,
    PhoneOtp,
    SessionSummary,
    User,
    UserMemory,
    WebAuthnCredential,
    WeeklyPlan,
)
from app.domain.value_objects import ChatRole, Email, PhoneE164


class UserRepository(Protocol):
    def get_by_id(self, user_id: uuid.UUID) -> User | None: ...
    def get_by_email(self, email: Email) -> User | None: ...
    def get_by_phone(self, phone: PhoneE164) -> User | None: ...
    def get_by_google_sub(self, google_sub: str) -> User | None: ...
    def add(self, user: User) -> User: ...
    def update(self, user: User) -> User: ...
    def list_ids_with_profile(self) -> list[uuid.UUID]: ...


class PhoneOtpRepository(Protocol):
    def add(self, otp: PhoneOtp) -> PhoneOtp: ...
    def get_latest_active_for_phone(self, phone: PhoneE164) -> PhoneOtp | None: ...
    def update(self, otp: PhoneOtp) -> PhoneOtp: ...


class WebAuthnCredentialRepository(Protocol):
    def add(self, credential: WebAuthnCredential) -> WebAuthnCredential: ...
    def list_for_user(self, user_id: uuid.UUID) -> list[WebAuthnCredential]: ...
    def get_by_credential_id(self, credential_id: bytes) -> WebAuthnCredential | None: ...
    def update(self, credential: WebAuthnCredential) -> WebAuthnCredential: ...
    def delete(self, credential_id: uuid.UUID) -> None: ...


class HealthProfileRepository(Protocol):
    def get_by_user_id(self, user_id: uuid.UUID) -> HealthProfile | None: ...
    def upsert(self, profile: HealthProfile) -> HealthProfile: ...


class ChatRepository(Protocol):
    def add(self, message: ChatMessage) -> ChatMessage: ...
    def list_recent_user_messages(
        self, user_id: uuid.UUID, days: int = 7, limit: int = 80
    ) -> list[ChatMessage]: ...
    def list_semantic_user_messages(
        self,
        user_id: uuid.UUID,
        query_embedding: list[float],
        days: int = 7,
        limit: int = 5,
    ) -> list[ChatMessage]: ...
    def list_for_conversation(self, conversation_id: uuid.UUID) -> list[ChatMessage]:
        """All messages (both roles) tagged with this conversation, oldest first.

        Still a sync method on the legacy `chat_history` table/engine — the
        Orchestrator calls this directly from its async `observe()`, matching the
        hybrid-async strategy (only the new Conversation/SessionSummary repos are
        async)."""
        ...


class CheckInRepository(Protocol):
    def get_for_date(self, user_id: uuid.UUID, d: date) -> DailyCheckIn | None: ...
    def list_week(
        self, user_id: uuid.UUID, start: date, end: date
    ) -> list[DailyCheckIn]: ...
    def upsert(self, check_in: DailyCheckIn) -> DailyCheckIn: ...


class WeeklyPlanRepository(Protocol):
    def get_for_week(
        self, user_id: uuid.UUID, week_start: date
    ) -> WeeklyPlan | None: ...
    def upsert(self, plan: WeeklyPlan) -> WeeklyPlan: ...
    def save_envelope(self, plan: WeeklyPlan) -> WeeklyPlan:
        """Save mutations inside `plan.tasks` (JSONB must be flagged as modified)."""
        ...


class EnvironmentTipRepository(Protocol):
    def get_for_date(
        self, user_id: uuid.UUID, tip_date: date
    ) -> DailyEnvironmentTip | None: ...
    def add(self, tip: DailyEnvironmentTip) -> DailyEnvironmentTip: ...


class AuditLogRepository(Protocol):
    def record(self, actor: str, action: str) -> None: ...


# ---------- Async ports (v2.0 modules only — see app/database.py hybrid engine note) ----------


class ConversationRepository(Protocol):
    """Async port. Backed by `get_async_db()`, not the legacy sync session."""

    async def add(self, conversation: Conversation) -> Conversation: ...
    async def get_by_id(self, conversation_id: uuid.UUID) -> Conversation | None: ...
    async def update(self, conversation: Conversation) -> Conversation: ...


class SessionSummaryRepository(Protocol):
    """Async port. Backed by `get_async_db()`, not the legacy sync session."""

    async def add(self, summary: SessionSummary) -> SessionSummary: ...
    async def list_for_conversation(
        self, conversation_id: uuid.UUID
    ) -> list[SessionSummary]: ...
    async def list_recent_for_user(
        self, user_id: uuid.UUID, limit: int = 3
    ) -> list[SessionSummary]: ...


class UserMemoryRepository(Protocol):
    """Async port. Backed by `get_async_db()`, not the legacy sync session.

    Long-Term Memory (LTM) facts — durable, declarative statements about a
    user (e.g. "User is lactose intolerant"), as opposed to `SessionSummary`'s
    per-conversation recap or `ChatMessage`'s raw transcript."""

    async def add_fact(
        self,
        *,
        user_id: uuid.UUID,
        fact_text: str,
        embedding: list[float] | None,
        source: str | None,
    ) -> UserMemory: ...

    async def search_relevant_facts(
        self,
        user_id: uuid.UUID,
        query_embedding: list[float],
        limit: int = 3,
    ) -> list[UserMemory]: ...
