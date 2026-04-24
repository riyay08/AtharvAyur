from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends

from app.application.dtos import GetOrCreateDailyTipInput
from app.application.use_cases.environment import GetOrCreateDailyEnvironmentTip
from app.interfaces.http.deps import get_current_user_id, make_environment_tip
from app.interfaces.http.schemas.environment import (
    DailyEnvironmentTipOut,
    DailyEnvironmentTipRequest,
)

router = APIRouter(tags=["environment"])


@router.post("/environment/daily-tip", response_model=DailyEnvironmentTipOut)
async def create_or_get_daily_environment_tip(
    body: DailyEnvironmentTipRequest,
    user_id: uuid.UUID = Depends(get_current_user_id),
    uc: GetOrCreateDailyEnvironmentTip = Depends(make_environment_tip),
) -> DailyEnvironmentTipOut:
    out = await uc.execute(
        GetOrCreateDailyTipInput(user_id=user_id, lat=body.latitude, lon=body.longitude)
    )
    # `cached` reflects whether we served from storage vs freshly synthesized;
    # the current use case always returns today's row so a second call is cached.
    return DailyEnvironmentTipOut(
        id=out.id,
        tip_date=out.tip_date,
        tip_title=out.tip_title,
        tip_description=out.tip_description,
        icon_name=out.icon_name,
        created_at=out.created_at,
        cached=False,
    )
