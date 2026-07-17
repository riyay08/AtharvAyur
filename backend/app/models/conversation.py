from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.chat_history import ChatHistory
    from app.models.session_summary import SessionSummary
    from app.models.user import User


class ConversationStatus(str, enum.Enum):
    ACTIVE = "active"
    ENDED = "ended"


class Conversation(Base):
    """A bounded chat session. Groups `chat_history` rows and owns `SessionSummary` recaps."""

    __tablename__ = "conversations"

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
    status: Mapped[ConversationStatus] = mapped_column(
        SAEnum(ConversationStatus, native_enum=False, values_callable=lambda m: [e.value for e in m]),
        nullable=False,
        default=ConversationStatus.ACTIVE,
    )
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    user: Mapped[User] = relationship(back_populates="conversations")
    messages: Mapped[list[ChatHistory]] = relationship(back_populates="conversation")
    summaries: Mapped[list[SessionSummary]] = relationship(
        back_populates="conversation",
        cascade="all, delete-orphan",
    )
