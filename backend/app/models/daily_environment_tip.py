from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class DailyEnvironmentTip(Base):
    __tablename__ = "daily_environment_tips"
    __table_args__ = (UniqueConstraint("user_id", "tip_date", name="uq_daily_env_tip_user_date"),)

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tip_date: Mapped[date] = mapped_column(Date(), nullable=False, index=True)
    tip_title: Mapped[str] = mapped_column(String(512), nullable=False)
    tip_description: Mapped[str] = mapped_column(Text(), nullable=False)
    icon_name: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    user: Mapped[User] = relationship(back_populates="daily_environment_tips")
