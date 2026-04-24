from __future__ import annotations

from sqlalchemy.orm import Session


class SqlAlchemyUnitOfWork:
    """Wraps a SQLAlchemy Session to satisfy `app.application.ports.unit_of_work.UnitOfWork`.

    The dependency that created the Session is responsible for closing it; the
    use case just calls `commit()` on the happy path and the FastAPI wrapper
    calls `rollback()` on any exception.
    """

    def __init__(self, session: Session) -> None:
        self._session = session

    @property
    def session(self) -> Session:
        return self._session

    def commit(self) -> None:
        self._session.commit()

    def rollback(self) -> None:
        self._session.rollback()
