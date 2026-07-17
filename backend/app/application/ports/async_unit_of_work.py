from __future__ import annotations

from typing import Protocol


class AsyncUnitOfWork(Protocol):
    """Transactional boundary for the async (v2.0) SQLAlchemy session.

    Mirrors `app.application.ports.unit_of_work.UnitOfWork` but for the
    `sqlalchemy.ext.asyncio` session used by the Conversation/SessionSummary/
    UserMemory repositories. Use cases call `commit()` on the happy path; the
    outer layer (e.g. a FastAPI dependency) rolls back on exception.
    """

    async def commit(self) -> None: ...
    async def rollback(self) -> None: ...
