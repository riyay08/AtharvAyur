from __future__ import annotations

import uuid

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities import SessionSummary as SessionSummaryEntity
from app.models.conversation import Conversation as ConversationORM
from app.models.session_summary import SessionSummary as SessionSummaryORM


def _to_entity(row: SessionSummaryORM) -> SessionSummaryEntity:
    return SessionSummaryEntity(
        id=row.id,
        conversation_id=row.conversation_id,
        summary_text=row.summary_text,
        created_at=row.created_at,
    )


class SqlAlchemySessionSummaryRepository:
    """Async repository — uses `AsyncSession` (see app/database.py get_async_db)."""

    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def add(self, summary: SessionSummaryEntity) -> SessionSummaryEntity:
        row = SessionSummaryORM(
            id=summary.id,
            conversation_id=summary.conversation_id,
            summary_text=summary.summary_text,
        )
        self._s.add(row)
        await self._s.flush()
        return _to_entity(row)

    async def list_for_conversation(
        self, conversation_id: uuid.UUID
    ) -> list[SessionSummaryEntity]:
        stmt = (
            select(SessionSummaryORM)
            .where(SessionSummaryORM.conversation_id == conversation_id)
            .order_by(SessionSummaryORM.created_at.asc())
        )
        result = await self._s.execute(stmt)
        return [_to_entity(r) for r in result.scalars().all()]

    async def list_recent_for_user(
        self, user_id: uuid.UUID, limit: int = 3
    ) -> list[SessionSummaryEntity]:
        """Last N summaries across all of the user's conversations, newest first.

        This is what the Orchestrator's Observe phase injects into the system prompt.
        """
        stmt = (
            select(SessionSummaryORM)
            .join(ConversationORM, ConversationORM.id == SessionSummaryORM.conversation_id)
            .where(ConversationORM.user_id == user_id)
            .order_by(desc(SessionSummaryORM.created_at))
            .limit(limit)
        )
        result = await self._s.execute(stmt)
        return [_to_entity(r) for r in result.scalars().all()]
