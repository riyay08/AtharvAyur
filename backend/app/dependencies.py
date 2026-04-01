"""FastAPI dependencies (e.g. DB session)."""

from app.database import get_db

__all__ = ["get_db"]
