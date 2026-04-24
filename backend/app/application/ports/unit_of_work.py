from __future__ import annotations

from typing import Protocol


class UnitOfWork(Protocol):
    """Transactional boundary. Use cases call `commit()` on the happy path; the
    outer layer (e.g. a FastAPI dependency) rolls back on exception.
    """

    def commit(self) -> None: ...
    def rollback(self) -> None: ...
