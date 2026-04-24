from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends

from app.application.dtos import (
    GenerateWeeklyPlanInput,
    GetCurrentPlanInput,
    UpdatePlanTaskInput,
)
from app.application.use_cases.plan import (
    GenerateWeeklyPlan,
    GetCurrentPlan,
    UpdatePlanTask,
)
from app.interfaces.http.deps import (
    get_current_user_id,
    make_generate_plan,
    make_get_current_plan,
    make_update_plan_task,
)
from app.interfaces.http.schemas.plan import (
    PlanGenerateRequest,
    PlanTaskUpdateRequest,
    WeeklyPlanOut,
)

router = APIRouter(tags=["plan"])


@router.post("/plan/generate", response_model=WeeklyPlanOut)
def generate_weekly_plan(
    _body: PlanGenerateRequest,
    user_id: uuid.UUID = Depends(get_current_user_id),
    uc: GenerateWeeklyPlan = Depends(make_generate_plan),
) -> WeeklyPlanOut:
    out = uc.execute(GenerateWeeklyPlanInput(user_id=user_id))
    return WeeklyPlanOut(id=out.id, start_date=out.start_date, tasks=out.tasks)


@router.get("/plan/current", response_model=WeeklyPlanOut | None)
def get_current_plan(
    user_id: uuid.UUID = Depends(get_current_user_id),
    uc: GetCurrentPlan = Depends(make_get_current_plan),
) -> WeeklyPlanOut | None:
    out = uc.execute(GetCurrentPlanInput(user_id=user_id))
    if out is None:
        return None
    return WeeklyPlanOut(id=out.id, start_date=out.start_date, tasks=out.tasks)


@router.put("/plan/task", response_model=WeeklyPlanOut)
def update_plan_task(
    body: PlanTaskUpdateRequest,
    user_id: uuid.UUID = Depends(get_current_user_id),
    uc: UpdatePlanTask = Depends(make_update_plan_task),
    get_plan: GetCurrentPlan = Depends(make_get_current_plan),
) -> WeeklyPlanOut:
    # The schema allows `completed` to be null (toggle). The use case expects a
    # concrete bool, so we resolve it here using the current plan as the source
    # of truth for toggle semantics.
    completed = body.completed
    if completed is None:
        current = get_plan.execute(GetCurrentPlanInput(user_id=user_id))
        if current is not None and isinstance(current.tasks, dict):
            try:
                days = current.tasks.get("days") or []
                pillar_tasks = (days[body.day_index] or {}).get("pillars", {}).get(body.pillar, [])
                for t in pillar_tasks:
                    if isinstance(t, dict) and int(t.get("id") or 0) == body.task_id:
                        completed = not bool(t.get("completed"))
                        break
            except Exception:
                completed = True
        if completed is None:
            completed = True

    out = uc.execute(
        UpdatePlanTaskInput(
            user_id=user_id,
            day_index=body.day_index,
            pillar=body.pillar,
            task_id=body.task_id,
            completed=bool(completed),
        )
    )
    return WeeklyPlanOut(id=out.id, start_date=out.start_date, tasks=out.tasks)
