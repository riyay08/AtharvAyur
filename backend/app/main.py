from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import OperationalError, ProgrammingError

from app.config import settings
from app.routers import auth, chat, checkin, environment, plan, profile
from app.services.scheduler import shutdown_scheduler, start_scheduler


@asynccontextmanager
async def lifespan(_app: FastAPI):
    start_scheduler()
    yield
    shutdown_scheduler()


app = FastAPI(
    title="HolisticAI Health API",
    description="Backend for HolisticAI Health — non-diagnostic GenAI health assistant.",
    version="0.1.0",
    lifespan=lifespan,
)


@app.exception_handler(OperationalError)
async def database_unreachable(_request: Request, _exc: OperationalError) -> JSONResponse:
    return JSONResponse(
        status_code=503,
        content={
            "detail": (
                "Database is unreachable. Start PostgreSQL (from backend/: docker compose up -d) "
                "and ensure DATABASE_URL in .env matches."
            )
        },
    )


@app.exception_handler(ProgrammingError)
async def database_schema_error(_request: Request, _exc: ProgrammingError) -> JSONResponse:
    return JSONResponse(
        status_code=503,
        content={
            "detail": (
                "Database tables are missing or out of date. From backend/ with your venv active, run: "
                "alembic upgrade head"
            )
        },
    )


_cors = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors or ["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(profile.router)
app.include_router(chat.router)
app.include_router(checkin.router)
app.include_router(environment.router)
app.include_router(plan.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
