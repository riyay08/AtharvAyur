"""Translate domain errors + SQLAlchemy errors into HTTP responses."""

from __future__ import annotations

import logging

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import OperationalError, ProgrammingError

from app.domain.errors import (
    AuthConflictError,
    AuthenticationError,
    ConfigurationError,
    DomainError,
    ExternalServiceError,
    NotFoundError,
    SafetyBlockedError,
    ValidationError,
)

logger = logging.getLogger(__name__)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(NotFoundError)
    async def _not_found(_req: Request, exc: NotFoundError) -> JSONResponse:
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"detail": str(exc)})

    @app.exception_handler(ValidationError)
    async def _validation(_req: Request, exc: ValidationError) -> JSONResponse:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"detail": str(exc)})

    @app.exception_handler(AuthenticationError)
    async def _auth(_req: Request, exc: AuthenticationError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": str(exc)},
            headers={"WWW-Authenticate": "Bearer"},
        )

    @app.exception_handler(AuthConflictError)
    async def _auth_conflict(_req: Request, exc: AuthConflictError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"detail": str(exc)},
        )

    @app.exception_handler(ConfigurationError)
    async def _config(_req: Request, exc: ConfigurationError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"detail": str(exc)},
        )

    @app.exception_handler(ExternalServiceError)
    async def _external(_req: Request, exc: ExternalServiceError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"detail": str(exc)},
        )

    @app.exception_handler(SafetyBlockedError)
    async def _safety(_req: Request, exc: SafetyBlockedError) -> JSONResponse:
        # Normally the use case handles this inline; this is a safety net.
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "blocked": True,
                "response_text": exc.escalation_message,
                "safety_reason": exc.reason,
                "matched_terms": list(exc.matched_terms),
            },
        )

    @app.exception_handler(DomainError)
    async def _domain(_req: Request, exc: DomainError) -> JSONResponse:
        logger.warning("Unhandled domain error: %s", exc)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": str(exc)},
        )

    @app.exception_handler(OperationalError)
    async def _db_unreachable(_req: Request, _exc: OperationalError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "detail": (
                    "Database is unreachable. Start PostgreSQL (from backend/: "
                    "docker compose up -d) and ensure DATABASE_URL in .env matches."
                )
            },
        )

    @app.exception_handler(ProgrammingError)
    async def _db_schema(_req: Request, _exc: ProgrammingError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "detail": (
                    "Database tables are missing or out of date. From backend/ with your venv "
                    "active, run: alembic upgrade head"
                )
            },
        )
