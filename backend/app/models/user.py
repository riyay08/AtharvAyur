from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import JSON, Boolean, DateTime, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.chat_history import ChatHistory
    from app.models.daily_check_in import DailyCheckIn
    from app.models.daily_environment_tip import DailyEnvironmentTip
    from app.models.health_profile import HealthProfile
    from app.models.webauthn_credential import WebAuthnCredential
    from app.models.weekly_plan import WeeklyPlan


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    region: Mapped[str | None] = mapped_column(String(255), nullable=True)
    consent_flags: Mapped[dict | list | None] = mapped_column(JSON, nullable=True)

    email: Mapped[str | None] = mapped_column(String(320), nullable=True, unique=True, index=True)
    email_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    phone: Mapped[str | None] = mapped_column(String(32), nullable=True, unique=True, index=True)
    phone_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    google_sub: Mapped[str | None] = mapped_column(
        String(128), nullable=True, unique=True, index=True
    )
    display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    primary_provider: Mapped[str] = mapped_column(
        String(32), nullable=False, default="anonymous"
    )
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
   
    health_profile: Mapped[HealthProfile | None] = relationship(
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    chat_messages: Mapped[list[ChatHistory]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    daily_check_ins: Mapped[list[DailyCheckIn]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    weekly_plans: Mapped[list[WeeklyPlan]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    daily_environment_tips: Mapped[list[DailyEnvironmentTip]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    webauthn_credentials: Mapped[list[WebAuthnCredential]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
