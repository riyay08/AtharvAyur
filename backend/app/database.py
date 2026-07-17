from collections.abc import AsyncGenerator, Generator

from pgvector.psycopg2 import register_vector
from sqlalchemy import event
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings


class Base(DeclarativeBase):
    pass


_engine = None
_SessionLocal: sessionmaker[Session] | None = None

# Async engine/session — used ONLY by new v2.0 modules (Conversation, SessionSummary,
# the orchestrator, the summary worker). All pre-existing repositories stay on the sync
# engine above; this is an intentional hybrid, not a full migration. Model classes
# themselves are shared (plain `Base` subclasses) — only the engine/session are async.
_async_engine: AsyncEngine | None = None
_AsyncSessionLocal: async_sessionmaker[AsyncSession] | None = None


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


def _to_asyncpg_url(url: str) -> str:
    """Swap the sync psycopg2 driver for asyncpg in an otherwise identical DSN."""
    if url.startswith("postgresql+psycopg2://"):
        return "postgresql+asyncpg://" + url[len("postgresql+psycopg2://") :]
    if url.startswith("postgresql://"):
        return "postgresql+asyncpg://" + url[len("postgresql://") :]
    return url


def get_async_engine() -> AsyncEngine:
    """Second engine, async-only, pointed at the same database as `get_engine()`."""
    global _async_engine
    if _async_engine is None:
        _async_engine = create_async_engine(
            _to_asyncpg_url(settings.database_url),
            pool_pre_ping=True,
        )
    return _async_engine


def get_async_session_factory() -> async_sessionmaker[AsyncSession]:
    global _AsyncSessionLocal
    if _AsyncSessionLocal is None:
        _AsyncSessionLocal = async_sessionmaker(
            bind=get_async_engine(),
            expire_on_commit=False,
        )
    return _AsyncSessionLocal


async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    session_local = get_async_session_factory()
    async with session_local() as session:
        yield session
