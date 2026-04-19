from __future__ import annotations

from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db
from app.models.audit_log import AuditLog
from app.models.daily_environment_tip import DailyEnvironmentTip
from app.models.health_profile import HealthProfile
from app.models.user import User
from app.schemas.environment import DailyEnvironmentTipOut, DailyEnvironmentTipRequest
from app.services.environment_service import EnvironmentServiceError, get_environment_context
from app.services.environment_tip_llm import synthesize_daily_environment_tip

router = APIRouter(tags=["environment"])


def _utc_today() -> date:
    return datetime.now(timezone.utc).date()


def _dominant_dosha_from_profile(profile: HealthProfile | None) -> str:
    if profile is None or profile.conditions is None:
        return "unknown"
    c = profile.conditions
    if not isinstance(c, dict):
        return "unknown"
    pq = c.get("prakriti_quiz")
    if isinstance(pq, dict):
        d = pq.get("dominant_dosha")
        if isinstance(d, str) and d.strip():
            return d.strip().lower()
    return "unknown"


def _tip_to_out(row: DailyEnvironmentTip, *, cached: bool) -> DailyEnvironmentTipOut:
    return DailyEnvironmentTipOut(
        id=row.id,
        user_id=row.user_id,
        tip_date=row.tip_date,
        tip_title=row.tip_title,
        tip_description=row.tip_description,
        icon_name=row.icon_name,
        created_at=row.created_at,
        cached=cached,
    )


@router.post("/environment/daily-tip", response_model=DailyEnvironmentTipOut)
async def create_or_get_daily_environment_tip(
    body: DailyEnvironmentTipRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DailyEnvironmentTipOut:
    tip_date = _utc_today()
    existing = db.execute(
        select(DailyEnvironmentTip).where(
            DailyEnvironmentTip.user_id == current_user.id,
            DailyEnvironmentTip.tip_date == tip_date,
        )
    ).scalar_one_or_none()
    if existing is not None:
        return _tip_to_out(existing, cached=True)

    try:
        env_ctx = await get_environment_context(body.latitude, body.longitude)
    except EnvironmentServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc

    profile = db.execute(
        select(HealthProfile).where(HealthProfile.user_id == current_user.id)
    ).scalar_one_or_none()
    dosha = _dominant_dosha_from_profile(profile)

    tip_payload = synthesize_daily_environment_tip(
        dominant_dosha=dosha,
        environment_context=env_ctx,
    )

    row = DailyEnvironmentTip(
        user_id=current_user.id,
        tip_date=tip_date,
        tip_title=tip_payload["tip_title"],
        tip_description=tip_payload["tip_description"],
        icon_name=tip_payload["icon_name"],
    )
    db.add(row)
    db.add(
        AuditLog(
            actor=str(current_user.id),
            action=f"environment.daily_tip_generated date={tip_date}",
        )
    )
    db.commit()
    db.refresh(row)
    return _tip_to_out(row, cached=False)
