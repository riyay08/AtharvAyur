from __future__ import annotations

import uuid
from datetime import date

import pytest

from app.domain.entities import WeeklyPlan
from app.domain.errors import NotFoundError
from app.domain.services.plan_normalization import normalize_weekly_plan_payload
from app.domain.value_objects import Pillar


def _plan() -> WeeklyPlan:
    envelope = normalize_weekly_plan_payload({}, date(2026, 4, 20))
    return WeeklyPlan(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        start_date=date(2026, 4, 20),
        tasks=envelope,
    )


def test_plan_is_envelope_after_normalization() -> None:
    assert _plan().is_envelope is True


def test_set_task_completed_toggles_flag() -> None:
    plan = _plan()
    updated = plan.set_task_completed(day_index=0, pillar=Pillar.MIND, task_id=1, completed=True)
    assert updated["completed"] is True
    again = plan.set_task_completed(day_index=0, pillar=Pillar.MIND, task_id=1, completed=False)
    assert again["completed"] is False


def test_set_task_completed_raises_for_unknown_task() -> None:
    plan = _plan()
    with pytest.raises(NotFoundError):
        plan.set_task_completed(day_index=0, pillar=Pillar.MIND, task_id=9999, completed=True)


def test_set_task_completed_raises_for_out_of_range_day() -> None:
    plan = _plan()
    with pytest.raises(NotFoundError):
        plan.set_task_completed(day_index=99, pillar=Pillar.MIND, task_id=1, completed=True)


def test_append_pillar_task_assigns_higher_id() -> None:
    plan = _plan()
    max_before = plan.max_task_id()
    new = plan.append_pillar_task(
        day_index=0, pillar=Pillar.BODY, task_text="Stretch", context_reason="Mobility"
    )
    assert new["id"] == max_before + 1
    assert new["completed"] is False
    assert plan.pillar_tasks(0, Pillar.BODY)[-1]["task"] == "Stretch"
