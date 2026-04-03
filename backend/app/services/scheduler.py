"""
APScheduler wired to FastAPI lifespan: weekly batch plan generation Sunday 02:00 server time.
"""

from __future__ import annotations

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.services.weekly_plan_service import generate_weekly_plans_for_all_users

logger = logging.getLogger(__name__)

_scheduler: AsyncIOScheduler | None = None


def _get_scheduler() -> AsyncIOScheduler:
    global _scheduler
    if _scheduler is None:
        _scheduler = AsyncIOScheduler()
    return _scheduler


def start_scheduler() -> None:
    sched = _get_scheduler()
    if sched.running:
        return
    sched.add_job(
        generate_weekly_plans_for_all_users,
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
