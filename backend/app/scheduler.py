"""Standalone scheduler glue. Wires APScheduler to the batch plan use case.

This module intentionally lives at the app root (not under infrastructure) because
it composes an `application` use case with concrete adapters — the same role
`main.py` plays for HTTP. Runtime-only; no business rules.
"""

from __future__ import annotations

import asyncio
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.application.dtos import GenerateWeeklyPlanInput
from app.application.use_cases.plan import (
    GenerateWeeklyPlan,
    GenerateWeeklyPlansForAllUsers,
)
from app.database import get_session_factory
from app.infrastructure.auth.jose_token_service import JoseTokenService  # noqa: F401 (init side effects)
from app.infrastructure.db.repositories.audit_log_repository import SqlAlchemyAuditLogRepository
from app.infrastructure.db.repositories.chat_repository import SqlAlchemyChatRepository
from app.infrastructure.db.repositories.health_profile_repository import (
    SqlAlchemyHealthProfileRepository,
)
from app.infrastructure.db.repositories.user_repository import SqlAlchemyUserRepository
from app.infrastructure.db.repositories.weekly_plan_repository import (
    SqlAlchemyWeeklyPlanRepository,
)
from app.infrastructure.db.unit_of_work import SqlAlchemyUnitOfWork
from app.infrastructure.llm.factory import make_llm_gateway
from app.infrastructure.time.system_clock import SystemClock

logger = logging.getLogger(__name__)

_scheduler: AsyncIOScheduler | None = None


def _get_scheduler() -> AsyncIOScheduler:
    global _scheduler
    if _scheduler is None:
        _scheduler = AsyncIOScheduler()
    return _scheduler


async def _run_weekly_plan_batch() -> None:
    """Runs the weekly-plan batch inside its own DB session + a shared LLM client."""
    try:
        llm = make_llm_gateway()
    except Exception as exc:
        logger.warning("Weekly plan batch: LLM gateway unavailable: %s", exc)
        return

    clock = SystemClock()
    SessionLocal = get_session_factory()
    processed = 0

    session = SessionLocal()
    try:
        users = SqlAlchemyUserRepository(session)
        plans = SqlAlchemyWeeklyPlanRepository(session)
        profiles = SqlAlchemyHealthProfileRepository(session)
        chat = SqlAlchemyChatRepository(session)
        audit = SqlAlchemyAuditLogRepository(session)
        uow = SqlAlchemyUnitOfWork(session)

        generate_one = GenerateWeeklyPlan(
            profiles=profiles,
            chat=chat,
            plans=plans,
            audit=audit,
            llm=llm,
            clock=clock,
            uow=uow,
        )
        batch = GenerateWeeklyPlansForAllUsers(
            users=users,
            generate_one=generate_one,
            plans=plans,
            clock=clock,
        )
        processed = batch.execute()
    except Exception as exc:
        logger.exception("Weekly plan batch failed: %s", exc)
    finally:
        session.close()

    logger.info("Weekly plan batch completed: processed=%d", processed)
    await asyncio.sleep(0)


def start_scheduler() -> None:
    sched = _get_scheduler()
    if sched.running:
        return
    sched.add_job(
        _run_weekly_plan_batch,
        CronTrigger(day_of_week="sun", hour=2, minute=0),
        id="holistica_weekly_plans",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )
    sched.start()
    logger.info("APScheduler started (weekly plans: Sunday 02:00 server local time).")


def shutdown_scheduler() -> None:
    global _scheduler
    sched = _scheduler
    if sched is None or not sched.running:
        return
    sched.shutdown(wait=False)
    logger.info("APScheduler shut down.")
