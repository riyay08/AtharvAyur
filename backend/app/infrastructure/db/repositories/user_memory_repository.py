from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities import UserMemory as UserMemoryEntity
from app.models.user_memory import UserMemory as UserMemoryORM


def _to_entity(row: UserMemoryORM) -> UserMemoryEntity:
    return UserMemoryEntity(
        id=row.id,
        user_id=row.user_id,
        fact_text=row.fact_text,
        embedding=list(row.embedding) if row.embedding is not None else None,
        source=row.source,
        created_at=row.created_at,
    )


class SqlAlchemyUserMemoryRepository:
    """Async repository — uses `AsyncSession` (see app/database.py get_async_db)."""

    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def add_fact(
        self,
        *,
        user_id: uuid.UUID,
        fact_text: str,
        embedding: list[float] | None,
        source: str | None,
    ) -> UserMemoryEntity:
        row = UserMemoryORM(
            id=uuid.uuid4(),
            user_id=user_id,
            fact_text=fact_text,
            embedding=embedding,
            source=source,
        )
        self._s.add(row)
        await self._s.flush()
        return _to_entity(row)

    async def search_relevant_facts(
        self,
        user_id: uuid.UUID,
        query_embedding: list[float],
        limit: int = 3,
    ) -> list[UserMemoryEntity]:
        """Top-`limit` facts by cosine distance to `query_embedding`.

        Returns `[]` (rather than an unfiltered/unordered scan) when no
        embedding is available — mirrors `ChatRepository.list_semantic_user_messages`,
        which does the same for Groq (no embedding endpoint)."""
        if not query_embedding:
            return []
        stmt = (
            select(UserMemoryORM)
            .where(
                UserMemoryORM.user_id == user_id,
                UserMemoryORM.embedding.is_not(None),
            )
            .order_by(UserMemoryORM.embedding.cosine_distance(query_embedding))
            .limit(limit)
        )
        result = await self._s.execute(stmt)
        return [_to_entity(r) for r in result.scalars().all()]
