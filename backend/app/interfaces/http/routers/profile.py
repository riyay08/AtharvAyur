from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.application.dtos import UpsertProfileInput
from app.application.use_cases.profile import GetProfileMe, UpsertProfile
from app.interfaces.http.deps import (
    get_current_user_id,
    get_db,
    make_get_profile_me,
    make_upsert_profile,
)
from app.interfaces.http.schemas.profile import (
    CheckInLiteOut,
    HealthProfileOut,
    ProfileMeResponse,
    ProfileUpsertRequest,
    ProfileUpsertResponse,
    WeeklyPlanLiteOut,
)
from app.models.user import User as UserORM

router = APIRouter(tags=["profile"])


@router.post("/profile", response_model=ProfileUpsertResponse)
def upsert_profile(
    body: ProfileUpsertRequest,
    user_id: uuid.UUID = Depends(get_current_user_id),
    uc: UpsertProfile = Depends(make_upsert_profile),
    db: Session = Depends(get_db),
) -> ProfileUpsertResponse:
    # `region` and `consent_flags` live on `User`, which isn't owned by the profile
    # use case. Mutate the row directly here — it's a trivial write on a single
    # table and the UoW will commit when the use case finishes.
    data = body.model_dump(exclude_unset=True)
    if "region" in data or "consent_flags" in data:
        user_row = db.get(UserORM, user_id)
        if user_row is not None:
            if "region" in data:
                user_row.region = body.region
            if "consent_flags" in data:
                user_row.consent_flags = body.consent_flags

    kwargs: dict = {"user_id": user_id, "prakriti_payload": body.prakriti_quiz}
    if "region" in data:
        kwargs["region"] = body.region
    if "consent_flags" in data:
        kwargs["consent_flags"] = body.consent_flags
    if "conditions" in data:
        kwargs["conditions"] = body.conditions
    if "allergies" in data:
        kwargs["allergies"] = body.allergies
    if "medications" in data:
        kwargs["medications"] = body.medications
    out = uc.execute(UpsertProfileInput(**kwargs))
    return ProfileUpsertResponse(user_id=out.user_id, health_profile_id=out.health_profile_id)


@router.get("/profile/me", response_model=ProfileMeResponse)
def get_profile_me(
    user_id: uuid.UUID = Depends(get_current_user_id),
    uc: GetProfileMe = Depends(make_get_profile_me),
    db: Session = Depends(get_db),
) -> ProfileMeResponse:
    out = uc.execute(user_id=user_id)
    user_row = db.get(UserORM, user_id)
    return ProfileMeResponse(
        user_id=out.user_id,
        region=user_row.region if user_row else None,
        consent_flags=user_row.consent_flags if user_row else None,
        health_profile=(
            HealthProfileOut(
                id=out.health_profile.id,
                user_id=out.user_id,
                conditions=out.health_profile.conditions,
                allergies=out.health_profile.allergies,
                medications=out.health_profile.medications,
            )
            if out.health_profile
            else None
        ),
        latest_checkin=(
            CheckInLiteOut(
                check_in_date=out.latest_check_in.check_in_date,
                sleep_quality=out.latest_check_in.sleep_quality,
                digestion=out.latest_check_in.digestion,
                energy_state=out.latest_check_in.energy_state,
                movement=out.latest_check_in.movement,
                water_glasses=out.latest_check_in.water_glasses,
            )
            if out.latest_check_in
            else None
        ),
        active_weekly_plan=(
            WeeklyPlanLiteOut(
                id=out.current_plan.id,
                start_date=out.current_plan.start_date,
                tasks=out.current_plan.tasks,
            )
            if out.current_plan
            else None
        ),
    )
