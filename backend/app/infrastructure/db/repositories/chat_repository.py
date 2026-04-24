from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.domain.entities import ChatMessage
from app.domain.value_objects import ChatRole as DomainChatRole
from app.models.chat_history import ChatHistory as ChatHistoryORM
from app.models.chat_history import ChatRole as OrmChatRole


def _role_to_orm(role: DomainChatRole) -> OrmChatRole:
    return OrmChatRole.USER if role == DomainChatRole.USER else OrmChatRole.ASSISTANT


def _to_entity(row: ChatHistoryORM) -> ChatMessage:
    return ChatMessage(
        id=row.id,
        user_id=row.user_id,
        role=DomainChatRole(row.role.value),
        message=row.message,
        timestamp=row.timestamp,
        embedding=list(row.embedding) if row.embedding is not None else None,
    )


class SqlAlchemyChatRepository:
    def __init__(self, session: Session) -> None:
        self._s = session

    def add(self, message: ChatMessage) -> ChatMessage:
        row = ChatHistoryORM(
            id=message.id,
            user_id=message.user_id,
            role=_role_to_orm(message.role),
            message=message.message,
            embedding=message.embedding,
        )
        self._s.add(row)
        self._s.flush()
        return _to_entity(row)

    def list_recent_user_messages(
        self, user_id: uuid.UUID, days: int = 7, limit: int = 80
    ) -> list[ChatMessage]:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        stmt = (
            select(ChatHistoryORM)
            .where(
                ChatHistoryORM.user_id == user_id,
                ChatHistoryORM.role == OrmChatRole.USER,
                ChatHistoryORM.timestamp >= cutoff,
            )
            .order_by(desc(ChatHistoryORM.timestamp))
            .limit(limit)
        )
        rows = list(self._s.execute(stmt).scalars().all())
        return [_to_entity(r) for r in reversed(rows)]

    def list_semantic_user_messages(
        self,
        user_id: uuid.UUID,
        query_embedding: list[float],
        days: int = 7,
        limit: int = 5,
    ) -> list[ChatMessage]:
        if not query_embedding:
            return []
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        stmt = (
            select(ChatHistoryORM)
            .where(
                ChatHistoryORM.user_id == user_id,
                ChatHistoryORM.role == OrmChatRole.USER,
                ChatHistoryORM.timestamp >= cutoff,
                ChatHistoryORM.embedding.is_not(None),
            )
            .order_by(ChatHistoryORM.embedding.cosine_distance(query_embedding))
            .limit(limit)
        )
        rows = list(self._s.execute(stmt).scalars().all())
        return [_to_entity(r) for r in rows]
