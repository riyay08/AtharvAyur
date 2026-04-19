from __future__ import annotations

from datetime import date
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db
from app.models.audit_log import AuditLog
from app.models.daily_check_in import DailyCheckIn
from app.models.health_profile import HealthProfile
from app.models.user import User
from app.schemas.checkin import DailyCheckInOut
from app.schemas.plan import WeeklyPlanOut
from app.schemas.profile import (
    HealthProfileOut,
    ProfileMeResponse,
    ProfileUpsertRequest,
    ProfileUpsertResponse,
)
from app.services.weekly_plan_service import get_current_week_plan

router = APIRouter(tags=["profile"])


def _merge_prakriti_into_conditions(
    conditions: dict[str, Any] | list[Any] | None,
    prakriti: dict[str, Any],
) -> dict[str, Any] | list[Any]:
    if isinstance(conditions, dict):
        merged = {**conditions, "prakriti_quiz": prakriti}
        return merged
    if conditions is None:
        return {"prakriti_quiz": prakriti}
    return {"prior_conditions": conditions, "prakriti_quiz": prakriti}


@router.post("/profile", response_model=ProfileUpsertResponse)
def upsert_profile(
    body: ProfileUpsertRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProfileUpsertResponse:
    data = body.model_dump(exclude_unset=True)

    if "region" in data:
        current_user.region = body.region
    if "consent_flags" in data:
        current_user.consent_flags = body.consent_flags

    profile = db.execute(
        select(HealthProfile).where(HealthProfile.user_id == current_user.id)
    ).scalar_one_or_none()
    if profile is None:
        profile = HealthProfile(user_id=current_user.id)
        db.add(profile)
        db.flush()

    if "allergies" in data:
        profile.allergies = body.allergies
    if "medications" in data:
        profile.medications = body.medications

    if "conditions" in data or "prakriti_quiz" in data:
        conds = body.conditions if "conditions" in data else profile.conditions
        if "prakriti_quiz" in data and body.prakriti_quiz is not None:
            profile.conditions = _merge_prakriti_into_conditions(conds, body.prakriti_quiz)
        elif "conditions" in data:
            profile.conditions = body.conditions

    db.add(
        AuditLog(
            actor=str(current_user.id),
            action="profile.upsert",
        )
    )
    db.commit()
    db.refresh(profile)

    return ProfileUpsertResponse(
        user_id=current_user.id,
        health_profile_id=profile.id,
    )


@router.get("/profile/me", response_model=ProfileMeResponse)
def get_profile_me(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProfileMeResponse:
    profile = db.execute(
        select(HealthProfile).where(HealthProfile.user_id == current_user.id)
    ).scalar_one_or_none()

    latest_checkin = db.execute(
        select(DailyCheckIn)
        .where(DailyCheckIn.user_id == current_user.id)
        .order_by(desc(DailyCheckIn.check_in_date), desc(DailyCheckIn.timestamp))
        .limit(1)
    ).scalar_one_or_none()

    active_plan = get_current_week_plan(db, current_user.id, date.today())

    return ProfileMeResponse(
        user_id=current_user.id,
        region=current_user.region,
        consent_flags=current_user.consent_flags,
        health_profile=HealthProfileOut.model_validate(profile) if profile is not None else None,
        latest_checkin=DailyCheckInOut.model_validate(latest_checkin) if latest_checkin is not None else None,
        active_weekly_plan=WeeklyPlanOut.model_validate(active_plan) if active_plan is not None else None,
    )
