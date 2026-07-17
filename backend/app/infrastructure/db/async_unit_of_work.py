from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession


class SqlAlchemyAsyncUnitOfWork:
    """Wraps an `AsyncSession` to satisfy `app.application.ports.async_unit_of_work.AsyncUnitOfWork`.

    The dependency that created the session is responsible for closing it; the
    use case just calls `commit()` on the happy path and the FastAPI wrapper
    calls `rollback()` on any exception.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @property
    def session(self) -> AsyncSession:
        return self._session

    async def commit(self) -> None:
        await self._session.commit()

    async def rollback(self) -> None:
        await self._session.rollback()
