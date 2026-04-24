from __future__ import annotations

from datetime import date, datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field


class PlanGenerateRequest(BaseModel):
    week_start: date | None = Field(
        default=None,
        description="Monday of the plan week; defaults to Monday of the current week.",
    )


class WeeklyPlanOut(BaseModel):
    id: UUID
    start_date: date
    tasks: dict[str, Any] | list[Any]
    created_at: datetime | None = None


class PlanTaskUpdateRequest(BaseModel):
    plan_id: UUID | None = Field(
        default=None,
        description="Weekly plan id; if omitted, the current week's plan is used.",
    )
    day_index: int = Field(ge=0, le=6)
    pillar: Literal["Mind", "Fuel", "Body"]
    task_id: int = Field(ge=1)
    completed: bool | None = Field(
        default=None,
        description="Set explicitly; if omitted, toggles the task's completed flag.",
    )
