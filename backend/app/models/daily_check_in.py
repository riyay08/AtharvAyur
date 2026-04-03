from __future__ import annotations

import enum
import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, Enum as SAEnum, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class SleepQuality(str, enum.Enum):
    HEAVY = "heavy"
    RESTLESS = "restless"
    REFRESHED = "refreshed"


class Digestion(str, enum.Enum):
    BLOATED = "bloated"
    ACIDIC = "acidic"
    CALM = "calm"


class EnergyState(str, enum.Enum):
    WIRED = "wired"
    GROUNDED = "grounded"
    SLUGGISH = "sluggish"


class MovementLevel(str, enum.Enum):
    REST = "rest"
    LIGHT = "light"
    SWEAT = "sweat"


class DailyCheckIn(Base):
    __tablename__ = "daily_check_ins"
    __table_args__ = (UniqueConstraint("user_id", "check_in_date", name="uq_daily_check_ins_user_date"),)

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
    check_in_date: Mapped[date] = mapped_column(Date(), nullable=False, index=True)
    sleep_quality: Mapped[SleepQuality] = mapped_column(
        SAEnum(SleepQuality, native_enum=False, values_callable=lambda m: [e.value for e in m]),
        nullable=False,
    )
    digestion: Mapped[Digestion] = mapped_column(
        SAEnum(Digestion, native_enum=False, values_callable=lambda m: [e.value for e in m]),
        nullable=False,
    )
    energy_state: Mapped[EnergyState] = mapped_column(
        SAEnum(EnergyState, native_enum=False, values_callable=lambda m: [e.value for e in m]),
        nullable=False,
    )
    movement: Mapped[MovementLevel] = mapped_column(
        SAEnum(MovementLevel, native_enum=False, values_callable=lambda m: [e.value for e in m]),
        nullable=False,
    )
    water_glasses: Mapped[int] = mapped_column(Integer(), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    user: Mapped[User] = relationship(back_populates="daily_check_ins")
