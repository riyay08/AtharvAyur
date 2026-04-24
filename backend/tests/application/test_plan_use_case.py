from __future__ import annotations

import json
import uuid
from datetime import date

import pytest

from app.application.dtos import (
    GenerateWeeklyPlanInput,
    GetCurrentPlanInput,
    UpdatePlanTaskInput,
)
from app.application.use_cases.plan import (
    GenerateWeeklyPlan,
    GenerateWeeklyPlansForAllUsers,
    GetCurrentPlan,
    UpdatePlanTask,
)
from app.domain.errors import NotFoundError, ValidationError
from app.domain.value_objects import Pillar
from tests.fakes import (
    FakeAuditLogRepository,
    FakeChatRepository,
    FakeClock,
    FakeHealthProfileRepository,
    FakeLLMGateway,
    FakeUnitOfWork,
    FakeUserRepository,
    FakeWeeklyPlanRepository,
)


def _make_generate(today: date = date(2026, 4, 22), llm: FakeLLMGateway | None = None):
    plans = FakeWeeklyPlanRepository()
    llm = llm or FakeLLMGateway()
    uc = GenerateWeeklyPlan(
        profiles=FakeHealthProfileRepository(),
        chat=FakeChatRepository(),
        plans=plans,
        audit=FakeAuditLogRepository(),
        llm=llm,
        clock=FakeClock(today=today),
        uow=FakeUnitOfWork(),
    )
    return uc, plans, llm


def test_generate_plan_saves_seven_day_envelope() -> None:
    uc, plans, _ = _make_generate()
    user_id = uuid.uuid4()
    out = uc.execute(GenerateWeeklyPlanInput(user_id=user_id))
    saved = plans.get_for_week(user_id, date(2026, 4, 20))
    assert saved is not None
    assert saved.is_envelope is True
    assert len(saved.tasks["days"]) == 7
    assert out.start_date == date(2026, 4, 20)


def test_generate_plan_raises_on_empty_llm_output() -> None:
    uc, _, _ = _make_generate(llm=FakeLLMGateway(plan_json="   "))
    with pytest.raises(ValidationError):
        uc.execute(GenerateWeeklyPlanInput(user_id=uuid.uuid4()))


def test_get_current_plan_returns_none_when_absent() -> None:
    uc = GetCurrentPlan(plans=FakeWeeklyPlanRepository(), clock=FakeClock(today=date(2026, 4, 22)))
    assert uc.execute(GetCurrentPlanInput(user_id=uuid.uuid4())) is None


def test_get_current_plan_returns_view_when_present() -> None:
    gen_uc, plans, _ = _make_generate()
    user_id = uuid.uuid4()
    gen_uc.execute(GenerateWeeklyPlanInput(user_id=user_id))
    uc = GetCurrentPlan(plans=plans, clock=FakeClock(today=date(2026, 4, 22)))
    view = uc.execute(GetCurrentPlanInput(user_id=user_id))
    assert view is not None
    assert view.start_date == date(2026, 4, 20)


def test_update_plan_task_raises_when_no_plan() -> None:
    uc = UpdatePlanTask(
        profiles=FakeHealthProfileRepository(),
        plans=FakeWeeklyPlanRepository(),
        audit=FakeAuditLogRepository(),
        llm=FakeLLMGateway(),
        clock=FakeClock(today=date(2026, 4, 22)),
        uow=FakeUnitOfWork(),
    )
    with pytest.raises(NotFoundError):
        uc.execute(
            UpdatePlanTaskInput(
                user_id=uuid.uuid4(),
                day_index=0,
                pillar="Mind",
                task_id=1,
                completed=True,
            )
        )


def test_update_plan_task_marks_completed_and_appends_followup() -> None:
    gen_uc, plans, _ = _make_generate(llm=FakeLLMGateway())
    user_id = uuid.uuid4()
    gen_uc.execute(GenerateWeeklyPlanInput(user_id=user_id))

    followup = FakeLLMGateway(
        followup_json='{"task": "Extra stretch", "context_reason": "Builds flexibility."}'
    )
    uc = UpdatePlanTask(
        profiles=FakeHealthProfileRepository(),
        plans=plans,
        audit=FakeAuditLogRepository(),
        llm=followup,
        clock=FakeClock(today=date(2026, 4, 22)),
        uow=FakeUnitOfWork(),
    )
    uc.execute(
        UpdatePlanTaskInput(
            user_id=user_id, day_index=0, pillar="Body", task_id=3, completed=True
        )
    )
    saved = plans.get_for_week(user_id, date(2026, 4, 20))
    body_tasks = saved.pillar_tasks(0, Pillar.BODY)
    assert any(t["task"] == "Extra stretch" for t in body_tasks)
    assert next(t for t in body_tasks if t["id"] == 3)["completed"] is True


def test_update_plan_task_unknown_pillar_raises() -> None:
    gen_uc, plans, _ = _make_generate()
    user_id = uuid.uuid4()
    gen_uc.execute(GenerateWeeklyPlanInput(user_id=user_id))

    uc = UpdatePlanTask(
        profiles=FakeHealthProfileRepository(),
        plans=plans,
        audit=FakeAuditLogRepository(),
        llm=FakeLLMGateway(),
        clock=FakeClock(today=date(2026, 4, 22)),
        uow=FakeUnitOfWork(),
    )
    with pytest.raises(ValidationError):
        uc.execute(
            UpdatePlanTaskInput(
                user_id=user_id, day_index=0, pillar="Spirit", task_id=1, completed=True
            )
        )


def test_generate_plans_for_all_users_skips_users_with_existing_plan() -> None:
    a, b = uuid.uuid4(), uuid.uuid4()
    users = FakeUserRepository()
    users.mark_has_profile(a)
    users.mark_has_profile(b)

    # Use a Wednesday so both `week_start_monday` (used by GenerateWeeklyPlan)
    # and `week_start_for_scheduled_job` (used by the batch) resolve to the
    # same Monday of the current week — no anchor-week mismatch.
    clock = FakeClock(today=date(2026, 4, 22))

    plans = FakeWeeklyPlanRepository()
    llm = FakeLLMGateway()
    gen_one = GenerateWeeklyPlan(
        profiles=FakeHealthProfileRepository(),
        chat=FakeChatRepository(),
        plans=plans,
        audit=FakeAuditLogRepository(),
        llm=llm,
        clock=clock,
        uow=FakeUnitOfWork(),
    )
    gen_one.execute(GenerateWeeklyPlanInput(user_id=a))

    batch = GenerateWeeklyPlansForAllUsers(
        users=users,
        generate_one=gen_one,
        plans=plans,
        clock=clock,
    )
    assert batch.execute() == 1
