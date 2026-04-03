from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import JSON, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.chat_history import ChatHistory
    from app.models.daily_check_in import DailyCheckIn
    from app.models.health_profile import HealthProfile
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
