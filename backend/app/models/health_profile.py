from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, JSON, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class HealthProfile(Base):
    __tablename__ = "health_profiles"
    __table_args__ = (UniqueConstraint("user_id", name="uq_health_profiles_user_id"),)

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
    conditions: Mapped[dict | list | None] = mapped_column(JSON, nullable=True)
    allergies: Mapped[dict | list | None] = mapped_column(JSON, nullable=True)
    medications: Mapped[dict | list | None] = mapped_column(JSON, nullable=True)

    user: Mapped[User] = relationship(back_populates="health_profile")
