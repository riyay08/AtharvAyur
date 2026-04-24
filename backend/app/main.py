"""FastAPI composition root.

Assembles middleware, exception handlers, routers, and the scheduler. The file
itself contains no business rules and no persistence concerns — those live in
`app.application`, `app.domain`, and `app.infrastructure`.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.interfaces.http.exception_handlers import register_exception_handlers
from app.interfaces.http.routers import (
    auth as auth_router,
    chat as chat_router,
    checkin as checkin_router,
    environment as environment_router,
    plan as plan_router,
    profile as profile_router,
)
from app.scheduler import shutdown_scheduler, start_scheduler


@asynccontextmanager
async def lifespan(_app: FastAPI):
    start_scheduler()
    try:
        yield
    finally:
        shutdown_scheduler()


def create_app() -> FastAPI:
    app = FastAPI(
        title="HolisticAI Health API",
        description="Backend for HolisticAI Health — non-diagnostic GenAI health assistant.",
        version="0.2.0",
        lifespan=lifespan,
    )

    cors = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors or ["http://localhost:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_exception_handlers(app)

    app.include_router(auth_router.router)
    app.include_router(profile_router.router)
    app.include_router(chat_router.router)
    app.include_router(checkin_router.router)
    app.include_router(environment_router.router)
    app.include_router(plan_router.router)

    @app.get("/health")
    def _health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
