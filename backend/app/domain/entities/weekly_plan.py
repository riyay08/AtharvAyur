from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any

from app.domain.errors import NotFoundError, ValidationError
from app.domain.value_objects import Pillar


@dataclass(slots=True)
class WeeklyPlan:
    """A 7-day plan envelope stored as structured JSON.

    The `tasks` dict follows:
      {
        "daily_focus_message": str,
        "days": [
          {
            "date": "YYYY-MM-DD",
            "pillars": { "Mind": [...], "Fuel": [...], "Body": [...] }
          }, ...
        ]
      }

    Each task is `{ "id": int, "task": str, "context_reason": str, "completed": bool }`.
    """

    id: uuid.UUID
    user_id: uuid.UUID
    start_date: date
    tasks: dict[str, Any] | list[Any]
    created_at: datetime | None = None

    @property
    def is_envelope(self) -> bool:
        """True when `tasks` is the new structured envelope (not legacy list)."""
        return (
            isinstance(self.tasks, dict)
            and isinstance(self.tasks.get("days"), list)
        )

    @property
    def daily_focus_message(self) -> str | None:
        if not self.is_envelope:
            return None
        msg = self.tasks.get("daily_focus_message")  # type: ignore[union-attr]
        return msg if isinstance(msg, str) else None

    def pillar_tasks(self, day_index: int, pillar: Pillar) -> list[dict[str, Any]]:
        """Return the task list for a given day + pillar. Raises NotFoundError if missing."""
        if not self.is_envelope:
            raise ValidationError("Plan uses legacy format; cannot access pillar tasks.")
        days = self.tasks.get("days")  # type: ignore[union-attr]
        if not isinstance(days, list) or not (0 <= day_index < len(days)):
            raise NotFoundError(f"Day index {day_index} out of range for plan.")
        day = days[day_index]
        if not isinstance(day, dict):
            raise NotFoundError(f"Day {day_index} is malformed.")
        pillars = day.get("pillars")
        if not isinstance(pillars, dict):
            raise NotFoundError(f"Day {day_index} has no pillars.")
        tasks = pillars.get(pillar.value)
        if not isinstance(tasks, list):
            raise NotFoundError(f"Pillar {pillar.value} missing on day {day_index}.")
        return tasks

    def set_task_completed(
        self,
        day_index: int,
        pillar: Pillar,
        task_id: int,
        completed: bool,
    ) -> dict[str, Any]:
        """Mark a task complete/incomplete in place. Returns the updated task dict."""
        tasks = self.pillar_tasks(day_index, pillar)
        for task in tasks:
            if isinstance(task, dict) and int(task.get("id") or 0) == task_id:
                task["completed"] = bool(completed)
                return task
        raise NotFoundError(f"Task id {task_id} not found on day {day_index} / {pillar.value}.")

    def append_pillar_task(
        self,
        day_index: int,
        pillar: Pillar,
        task_text: str,
        context_reason: str,
    ) -> dict[str, Any]:
        """Append a new task to a pillar; assigns an id higher than any existing."""
        tasks = self.pillar_tasks(day_index, pillar)
        max_id = self.max_task_id()
        new_task = {
            "id": max_id + 1,
            "task": task_text,
            "context_reason": context_reason,
            "completed": False,
        }
        tasks.append(new_task)
        return new_task

    def max_task_id(self) -> int:
        if not self.is_envelope:
            return 0
        m = 0
        for day in self.tasks.get("days") or []:  # type: ignore[union-attr]
            if not isinstance(day, dict):
                continue
            pillars = day.get("pillars")
            if not isinstance(pillars, dict):
                continue
            for pk in Pillar.all():
                for task in pillars.get(pk.value) or []:
                    if not isinstance(task, dict):
                        continue
                    try:
                        m = max(m, int(task.get("id") or 0))
                    except (TypeError, ValueError):
                        continue
        return m
