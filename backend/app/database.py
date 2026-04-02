from collections.abc import Generator

from pgvector.psycopg2 import register_vector
from sqlalchemy import event
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings


class Base(DeclarativeBase):
    pass


_engine = None
_SessionLocal: sessionmaker[Session] | None = None


def get_engine():
    """Create the SQLAlchemy engine on first use (avoids import-time DB driver requirements)."""
    global _engine
    if _engine is None:
        _engine = create_engine(
            settings.database_url,
            pool_pre_ping=True,
        )
        # Register pgvector adapters for psycopg2 connections.
        @event.listens_for(_engine, "connect")
        def _register_pgvector(dbapi_connection, _):  # type: ignore[no-untyped-def]
            try:
                register_vector(dbapi_connection)
            except Exception:
                # Keep startup resilient if extension is not yet created.
                pass
    return _engine


def get_session_factory() -> sessionmaker[Session]:
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=get_engine())
    return _SessionLocal


def get_db() -> Generator[Session, None, None]:
    session_local = get_session_factory()
    db = session_local()
    try:
        yield db
    finally:
        db.close()
