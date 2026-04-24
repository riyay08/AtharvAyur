from __future__ import annotations

import uuid
from datetime import date

from fastapi import APIRouter, Depends, Query

from app.application.dtos import GetCheckInWeekInput, UpsertCheckInInput
from app.application.ports.clock import Clock
from app.application.use_cases.checkin import GetCheckInWeek, UpsertCheckIn
from app.interfaces.http.deps import (
    get_clock,
    get_current_user_id,
    make_get_checkin_week,
    make_upsert_checkin,
)
from app.interfaces.http.schemas.checkin import (
    DailyCheckInCreate,
    DailyCheckInOut,
    DailyCheckInWeekResponse,
    DailyCheckInWeekSlot,
)

router = APIRouter(tags=["checkin"])


@router.get("/checkin/week", response_model=DailyCheckInWeekResponse)
def get_checkin_week(
    end_date: date | None = Query(default=None),
    user_id: uuid.UUID = Depends(get_current_user_id),
    uc: GetCheckInWeek = Depends(make_get_checkin_week),
) -> DailyCheckInWeekResponse:
    out = uc.execute(GetCheckInWeekInput(user_id=user_id, end_date=end_date))
    slots = [
        DailyCheckInWeekSlot(
            check_in_date=s.date,
            record=(
                DailyCheckInOut(
                    id=s.check_in.id,
                    check_in_date=s.check_in.check_in_date,
                    sleep_quality=s.check_in.sleep_quality,
                    digestion=s.check_in.digestion,
                    energy_state=s.check_in.energy_state,
                    movement=s.check_in.movement,
                    water_glasses=s.check_in.water_glasses,
                    timestamp=s.check_in.timestamp,
                )
                if s.check_in
                else None
            ),
        )
        for s in out.slots
    ]
    return DailyCheckInWeekResponse(days=slots)


@router.post("/checkin", response_model=DailyCheckInOut)
def create_or_update_checkin(
    body: DailyCheckInCreate,
    user_id: uuid.UUID = Depends(get_current_user_id),
    uc: UpsertCheckIn = Depends(make_upsert_checkin),
    clock: Clock = Depends(get_clock),
) -> DailyCheckInOut:
    out = uc.execute(
        UpsertCheckInInput(
            user_id=user_id,
            check_in_date=body.check_in_date or clock.today(),
            sleep_quality=body.sleep_quality,
            digestion=body.digestion,
            energy_state=body.energy_state,
            movement=body.movement,
            water_glasses=body.water_glasses,
        )
    )
    return DailyCheckInOut(
        id=out.id,
        check_in_date=out.check_in_date,
        sleep_quality=out.sleep_quality,
        digestion=out.digestion,
        energy_state=out.energy_state,
        movement=out.movement,
        water_glasses=out.water_glasses,
        timestamp=out.timestamp,
    )
