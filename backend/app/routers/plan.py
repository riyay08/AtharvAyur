from __future__ import annotations

import copy
import json
import logging
import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from app.dependencies import get_db
from app.models.audit_log import AuditLog
from app.models.health_profile import HealthProfile
from app.models.user import User
from app.models.weekly_plan import WeeklyPlan
from app.schemas.plan import PlanGenerateRequest, PlanTaskUpdateRequest, WeeklyPlanOut
from app.services.llm_orchestrator import OrchestratorConfigError
from app.services.weekly_plan_service import (
    generate_followup_pillar_task,
    generate_weekly_plan_via_llm,
    get_current_week_plan,
    max_task_id_in_envelope,
    upsert_weekly_plan,
    week_start_monday,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["plan"])

_MAX_TASKS_PER_PILLAR_DAY = 28


def _pillar_task_list(pillars: dict, pillar_name: str) -> list | None:
    if pillar_name in pillars and isinstance(pillars[pillar_name], list):
        return pillars[pillar_name]
    pl = pillar_name.strip().lower()
    for key, val in pillars.items():
        if isinstance(key, str) and key.strip().lower() == pl and isinstance(val, list):
            return val
    return None


@router.post("/plan/generate", response_model=WeeklyPlanOut)
def generate_weekly_plan(
    body: PlanGenerateRequest,
    db: Session = Depends(get_db),
) -> WeeklyPlanOut:
    user = db.get(User, body.user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    profile = db.execute(
        select(HealthProfile).where(HealthProfile.user_id == user.id)
    ).scalar_one_or_none()

    week_start = body.week_start or week_start_monday(date.today())
    try:
        payload = generate_weekly_plan_via_llm(db, user.id, profile, week_start=week_start)
    except OrchestratorConfigError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except (ValueError, json.JSONDecodeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Weekly plan generation failed: {exc}",
        ) from exc

    plan = upsert_weekly_plan(db, user.id, week_start, payload)
    db.add(
        AuditLog(
            actor=str(user.id),
            action=f"plan.generate week_start={week_start}",
        )
    )
    db.commit()
    db.refresh(plan)
    return WeeklyPlanOut.model_validate(plan)


@router.get("/plan/current", response_model=WeeklyPlanOut | None)
def get_current_plan(
    user_id: uuid.UUID = Query(..., description="User UUID"),
    db: Session = Depends(get_db),
) -> WeeklyPlanOut | None:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    plan = get_current_week_plan(db, user_id, date.today())
    if plan is None:
        return None
    return WeeklyPlanOut.model_validate(plan)


@router.put("/plan/task", response_model=WeeklyPlanOut)
def update_plan_task(
    body: PlanTaskUpdateRequest,
    db: Session = Depends(get_db),
) -> WeeklyPlanOut:
    user = db.get(User, body.user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    profile = db.execute(
        select(HealthProfile).where(HealthProfile.user_id == user.id)
    ).scalar_one_or_none()

    if body.plan_id is not None:
        plan = db.get(WeeklyPlan, body.plan_id)
        if plan is None or plan.user_id != body.user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Weekly plan not found for this user.",
            )
    else:
        plan = get_current_week_plan(db, body.user_id, date.today())
        if plan is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No weekly plan for the current week. Generate one first.",
            )

    raw_root = plan.tasks
    if isinstance(raw_root, list):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This weekly plan uses a legacy format. Please generate a new plan.",
        )
    if not isinstance(raw_root, dict):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Malformed weekly plan payload.",
        )

    root = copy.deepcopy(raw_root)
    days = root.get("days")
    if not isinstance(days, list) or body.day_index < 0 or body.day_index >= len(days):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid day_index for this plan.",
        )
    day = days[body.day_index]
    if not isinstance(day, dict):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Malformed plan day entry.",
        )
    pillars = day.get("pillars")
    if not isinstance(pillars, dict):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Malformed pillars for this day.",
        )

    pillar_list = _pillar_task_list(pillars, body.pillar)
    if pillar_list is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Pillar {body.pillar!r} not found for this day.",
        )

    found = False
    completed_snapshot: dict[str, str] | None = None
    now_completed = False
    for t in pillar_list:
        if not isinstance(t, dict):
            continue
        tid = t.get("id")
        try:
            tid_int = int(tid) if tid is not None else None
        except (TypeError, ValueError):
            tid_int = None
        if tid_int == body.task_id:
            found = True
            completed_snapshot = {
                "task": str(t.get("task") or ""),
                "context_reason": str(t.get("context_reason") or ""),
            }
            if body.completed is None:
                t["completed"] = not bool(t.get("completed"))
            else:
                t["completed"] = body.completed
            now_completed = bool(t.get("completed"))
            break

    if not found:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Task id not found in the given pillar and day.",
        )

    if now_completed and completed_snapshot is not None and len(pillar_list) < _MAX_TASKS_PER_PILLAR_DAY:
        day_date_str = str(day.get("date") or "")
        try:
            follow = generate_followup_pillar_task(
                db,
                user.id,
                profile,
                body.pillar,
                completed_snapshot.get("task", ""),
                completed_snapshot.get("context_reason", ""),
                day_date_str,
            )
            new_id = max_task_id_in_envelope(root) + 1
            pillar_list.append(
                {
                    "id": new_id,
                    "task": follow["task"],
                    "context_reason": follow["context_reason"],
                    "completed": False,
                }
            )
        except Exception as exc:
            logger.warning("Follow-up task for pillar %s failed: %s", body.pillar, exc)

    plan.tasks = root
    flag_modified(plan, "tasks")
    db.add(
        AuditLog(
            actor=str(body.user_id),
            action="plan.task_update",
        )
    )
    db.commit()
    db.refresh(plan)
    return WeeklyPlanOut.model_validate(plan)
