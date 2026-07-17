from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import timedelta

from app.application.dtos import (
    CheckInLiteView,
    GetProfileMeOutput,
    HealthProfileView,
    UpsertProfileInput,
    UpsertProfileOutput,
    WeeklyPlanView,
)
from app.application.ports.clock import Clock
from app.application.ports.repositories import (
    AuditLogRepository,
    CheckInRepository,
    HealthProfileRepository,
    UserRepository,
    WeeklyPlanRepository,
)
from app.application.ports.unit_of_work import UnitOfWork
from app.domain.entities import HealthProfile
from app.domain.errors import NotFoundError
from app.domain.services.dosha_scoring import DoshaScores, extract_dosha_scores
from app.domain.services.profile_merge import merge_prakriti_into_conditions
from app.domain.services.week_calendar import week_start_monday


@dataclass(frozen=True, slots=True)
class UpsertProfile:
    users: UserRepository
    profiles: HealthProfileRepository
    audit: AuditLogRepository
    uow: UnitOfWork

    def execute(self, cmd: UpsertProfileInput) -> UpsertProfileOutput:
        user = self.users.get_by_id(cmd.user_id)
        if user is None:
            raise NotFoundError(f"User {cmd.user_id} not found.")

        # Note: region / consent_flags live on User, not HealthProfile. The repo
        # does not expose a direct field mutation API, so we mutate in-place via
        # a separate method the infra layer provides. For now, we assume the
        # interface layer handled these before calling the use case (see router).
        # This keeps the use case simple and focused on the profile entity.

        existing = self.profiles.get_by_user_id(cmd.user_id)

        new_allergies = (
            cmd.allergies
            if not UpsertProfileInput.is_unset(cmd.allergies)
            else (existing.allergies if existing else None)
        )
        new_medications = (
            cmd.medications
            if not UpsertProfileInput.is_unset(cmd.medications)
            else (existing.medications if existing else None)
        )

        existing_scores = DoshaScores(
            vata=existing.vata_score if existing else None,
            pitta=existing.pitta_score if existing else None,
            kapha=existing.kapha_score if existing else None,
        )

        if cmd.prakriti_payload is not None:
            base = (
                cmd.conditions
                if not UpsertProfileInput.is_unset(cmd.conditions)
                else (existing.conditions if existing else None)
            )
            new_conditions = merge_prakriti_into_conditions(base, cmd.prakriti_payload)
            # A new quiz submission re-derives the structured scores; anything else
            # (editing allergies/medications, etc.) must NOT touch them.
            dosha_scores = extract_dosha_scores(cmd.prakriti_payload)
        elif not UpsertProfileInput.is_unset(cmd.conditions):
            new_conditions = cmd.conditions
            dosha_scores = existing_scores
        else:
            new_conditions = existing.conditions if existing else None
            dosha_scores = existing_scores

        profile = HealthProfile(
            id=existing.id if existing else uuid.uuid4(),
            user_id=cmd.user_id,
            conditions=new_conditions,
            allergies=new_allergies,
            medications=new_medications,
            vata_score=dosha_scores.vata,
            pitta_score=dosha_scores.pitta,
            kapha_score=dosha_scores.kapha,
        )
        saved = self.profiles.upsert(profile)
        self.audit.record(actor=str(cmd.user_id), action="profile.upserted")
        self.uow.commit()

        return UpsertProfileOutput(
            user_id=cmd.user_id,
            health_profile=HealthProfileView(
                id=saved.id,
                conditions=saved.conditions,
                allergies=saved.allergies,
                medications=saved.medications,
            ),
            health_profile_id=saved.id,
        )


@dataclass(frozen=True, slots=True)
class GetProfileMe:
    users: UserRepository
    profiles: HealthProfileRepository
    check_ins: CheckInRepository
    plans: WeeklyPlanRepository
    clock: Clock

    def execute(self, *, user_id: uuid.UUID) -> GetProfileMeOutput:
        user = self.users.get_by_id(user_id)
        if user is None:
            raise NotFoundError(f"User {user_id} not found.")

        profile = self.profiles.get_by_user_id(user_id)
        today = self.clock.today()
        week_start = week_start_monday(today)
        window = self.check_ins.list_week(user_id, week_start - timedelta(days=30), today)
        latest = window[-1] if window else None
        current_plan = self.plans.get_for_week(user_id, week_start)

        return GetProfileMeOutput(
            user_id=user_id,
            health_profile=(
                HealthProfileView(
                    id=profile.id,
                    conditions=profile.conditions,
                    allergies=profile.allergies,
                    medications=profile.medications,
                )
                if profile
                else None
            ),
            latest_check_in=(
                CheckInLiteView(
                    check_in_date=latest.check_in_date,
                    sleep_quality=latest.sleep_quality.value,
                    digestion=latest.digestion.value,
                    energy_state=latest.energy_state.value,
                    movement=latest.movement.value,
                    water_glasses=latest.water_glasses,
                )
                if latest
                else None
            ),
            current_plan=(
                WeeklyPlanView(
                    id=current_plan.id,
                    start_date=current_plan.start_date,
                    tasks=current_plan.tasks,
                )
                if current_plan
                else None
            ),
        )
