from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.models.audit_log import AuditLog
from app.models.health_profile import HealthProfile
from app.models.user import User
from app.schemas.profile import ProfileUpsertRequest, ProfileUpsertResponse

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
) -> ProfileUpsertResponse:
    created_user = False
    if body.user_id is not None:
        user = db.get(User, body.user_id)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found for the given user_id.",
            )
    else:
        user = User()
        db.add(user)
        db.flush()
        created_user = True

    data = body.model_dump(exclude_unset=True)

    if "region" in data:
        user.region = body.region
    if "consent_flags" in data:
        user.consent_flags = body.consent_flags

    profile = db.execute(
        select(HealthProfile).where(HealthProfile.user_id == user.id)
    ).scalar_one_or_none()
    if profile is None:
        profile = HealthProfile(user_id=user.id)
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
            actor=str(user.id),
            action="profile.upsert",
        )
    )
    db.commit()
    db.refresh(profile)
    db.refresh(user)

    return ProfileUpsertResponse(
        user_id=user.id,
        health_profile_id=profile.id,
        created_user=created_user,
    )
