from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from datetime import timedelta

from app.application.dtos import (
    GenerateWeeklyPlanInput,
    GetCurrentPlanInput,
    UpdatePlanTaskInput,
    WeeklyPlanView,
)
from app.application.ports.clock import Clock
from app.application.ports.llm_gateway import LLMGateway
from app.application.ports.repositories import (
    AuditLogRepository,
    ChatRepository,
    HealthProfileRepository,
    UserRepository,
    WeeklyPlanRepository,
)
from app.application.ports.unit_of_work import UnitOfWork
from app.domain.entities import WeeklyPlan
from app.domain.errors import NotFoundError, ValidationError
from app.domain.services.plan_normalization import (
    extract_json_object,
    normalize_weekly_plan_payload,
)
from app.domain.services.week_calendar import (
    week_start_for_scheduled_job,
    week_start_monday,
)
from app.domain.value_objects import Pillar


def _profile_blob(profile) -> str:
    if profile is None:
        return "{}"
    payload = {
        "conditions": profile.conditions,
        "allergies": profile.allergies,
        "medications": profile.medications,
    }
    try:
        return json.dumps(payload, indent=2, default=str)
    except TypeError:
        return json.dumps(
            {
                "conditions": str(profile.conditions),
                "allergies": str(profile.allergies),
                "medications": str(profile.medications),
            },
            indent=2,
        )


def _to_view(plan: WeeklyPlan) -> WeeklyPlanView:
    return WeeklyPlanView(id=plan.id, start_date=plan.start_date, tasks=plan.tasks)


@dataclass(frozen=True, slots=True)
class GenerateWeeklyPlan:
    profiles: HealthProfileRepository
    chat: ChatRepository
    plans: WeeklyPlanRepository
    audit: AuditLogRepository
    llm: LLMGateway
    clock: Clock
    uow: UnitOfWork

    def execute(self, cmd: GenerateWeeklyPlanInput) -> WeeklyPlanView:
        today = self.clock.today()
        ws = week_start_monday(today)
        we = ws + timedelta(days=6)

        profile = self.profiles.get_by_user_id(cmd.user_id)

        query_embedding = self.llm.embed(
            "Symptoms, complaints, energy, sleep, digestion, stress, and wellness goals "
            "the user mentioned in conversation."
        )
        semantic = (
            self.chat.list_semantic_user_messages(cmd.user_id, query_embedding, days=7, limit=5)
            if query_embedding
            else []
        )
        recent = self.chat.list_recent_user_messages(cmd.user_id, days=7, limit=80)

        def _block(msgs) -> str:
            if not msgs:
                return "(No embedded messages matched in the last 7 days.)"
            chrono = sorted(msgs, key=lambda m: m.timestamp or 0)
            return "\n".join(f"- {m.message}" for m in chrono)

        raw = self.llm.generate_weekly_plan_json(
            profile_blob_json=_profile_blob(profile),
            recent_history_block=_block(recent),
            semantic_history_block=_block(semantic),
            week_start_iso=ws.isoformat(),
            week_end_iso=we.isoformat(),
        )
        if not raw.strip():
            raise ValidationError("Empty response from model for weekly plan.")
        parsed = extract_json_object(raw)
        envelope = normalize_weekly_plan_payload(parsed, ws)

        plan = WeeklyPlan(
            id=uuid.uuid4(),
            user_id=cmd.user_id,
            start_date=ws,
            tasks=envelope,
        )
        saved = self.plans.upsert(plan)
        self.audit.record(actor=str(cmd.user_id), action="plan.generated")
        self.uow.commit()
        return _to_view(saved)


@dataclass(frozen=True, slots=True)
class GetCurrentPlan:
    plans: WeeklyPlanRepository
    clock: Clock

    def execute(self, cmd: GetCurrentPlanInput) -> WeeklyPlanView | None:
        ws = week_start_monday(self.clock.today())
        plan = self.plans.get_for_week(cmd.user_id, ws)
        return _to_view(plan) if plan else None


@dataclass(frozen=True, slots=True)
class UpdatePlanTask:
    profiles: HealthProfileRepository
    plans: WeeklyPlanRepository
    audit: AuditLogRepository
    llm: LLMGateway
    clock: Clock
    uow: UnitOfWork

    def execute(self, cmd: UpdatePlanTaskInput) -> WeeklyPlanView:
        ws = week_start_monday(self.clock.today())
        plan = self.plans.get_for_week(cmd.user_id, ws)
        if plan is None:
            raise NotFoundError("No current weekly plan. Generate one first.")

        try:
            pillar = Pillar(cmd.pillar)
        except ValueError as exc:
            raise ValidationError(f"Unknown pillar: {cmd.pillar}") from exc

        updated_task = plan.set_task_completed(
            day_index=cmd.day_index,
            pillar=pillar,
            task_id=cmd.task_id,
            completed=cmd.completed,
        )

        if cmd.completed:
            try:
                day = plan.tasks["days"][cmd.day_index]  # type: ignore[index]
                day_date_iso = str(day.get("date") or (ws + timedelta(days=cmd.day_index)).isoformat())
                raw = self.llm.generate_followup_task_json(
                    pillar=pillar.value,
                    completed_task=str(updated_task.get("task") or ""),
                    completed_context=str(updated_task.get("context_reason") or ""),
                    plan_day_date=day_date_iso,
                    profile_blob_json=_profile_blob(self.profiles.get_by_user_id(cmd.user_id)),
                    recent_history_block="",
                )
                parsed = extract_json_object(raw)
                text = str(parsed.get("task") or "").strip()[:500]
                reason = str(parsed.get("context_reason") or "").strip()[:2000]
                if text:
                    plan.append_pillar_task(
                        day_index=cmd.day_index,
                        pillar=pillar,
                        task_text=text,
                        context_reason=reason or "Continues your pillar focus.",
                    )
            except Exception:
                # Follow-up is best-effort; primary completion still succeeded.
                pass

        saved = self.plans.save_envelope(plan)
        self.audit.record(actor=str(cmd.user_id), action="plan.task_updated")
        self.uow.commit()
        return _to_view(saved)


@dataclass(frozen=True, slots=True)
class GenerateWeeklyPlansForAllUsers:
    """Scheduled batch: generate plans for every user with a profile for the anchor week."""

    users: UserRepository
    generate_one: GenerateWeeklyPlan
    plans: WeeklyPlanRepository
    clock: Clock

    def execute(self) -> int:
        run_date = self.clock.today()
        ws = week_start_for_scheduled_job(run_date)
        candidates = self.users.list_ids_with_profile()
        count = 0
        for uid in candidates:
            if self.plans.get_for_week(uid, ws) is not None:
                continue
            try:
                self.generate_one.execute(GenerateWeeklyPlanInput(user_id=uid))
                count += 1
            except Exception:
                continue
        return count
