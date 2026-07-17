from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities import Conversation as ConversationEntity
from app.domain.entities import ConversationStatus
from app.domain.errors import NotFoundError
from app.models.conversation import Conversation as ConversationORM
from app.models.conversation import ConversationStatus as OrmConversationStatus


def _to_entity(row: ConversationORM) -> ConversationEntity:
    return ConversationEntity(
        id=row.id,
        user_id=row.user_id,
        status=ConversationStatus(row.status.value),
        title=row.title,
        created_at=row.created_at,
    )


class SqlAlchemyConversationRepository:
    """Async repository — uses `AsyncSession` (see app/database.py get_async_db)."""

    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def add(self, conversation: ConversationEntity) -> ConversationEntity:
        row = ConversationORM(
            id=conversation.id,
            user_id=conversation.user_id,
            status=OrmConversationStatus(conversation.status.value),
            title=conversation.title,
        )
        self._s.add(row)
        await self._s.flush()
        return _to_entity(row)

    async def get_by_id(self, conversation_id: uuid.UUID) -> ConversationEntity | None:
        row = await self._s.get(ConversationORM, conversation_id)
        return _to_entity(row) if row else None

    async def update(self, conversation: ConversationEntity) -> ConversationEntity:
        row = await self._s.get(ConversationORM, conversation.id)
        if row is None:
            raise NotFoundError(f"Conversation {conversation.id} not found")
        row.status = OrmConversationStatus(conversation.status.value)
        row.title = conversation.title
        await self._s.flush()
        return _to_entity(row)
