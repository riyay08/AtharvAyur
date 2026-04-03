from __future__ import annotations

import uuid
from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.models.audit_log import AuditLog
from app.models.daily_check_in import (
    DailyCheckIn,
    Digestion,
    EnergyState,
    MovementLevel,
    SleepQuality,
)
from app.models.user import User
from app.schemas.checkin import (
    DailyCheckInCreate,
    DailyCheckInOut,
    DailyCheckInWeekResponse,
    DailyCheckInWeekSlot,
)

router = APIRouter(tags=["checkin"])


@router.get("/checkin/week", response_model=DailyCheckInWeekResponse)
def get_checkin_week(
    user_id: uuid.UUID = Query(..., description="User UUID"),
    end_date: date | None = Query(
        default=None,
        description="Last day of the 7-day window (inclusive); defaults to server today. "
        "Pass the client's local today for alignment with the UI strip.",
    ),
    db: Session = Depends(get_db),
) -> DailyCheckInWeekResponse:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    anchor = end_date or date.today()
    start = anchor - timedelta(days=6)
    rows = db.execute(
        select(DailyCheckIn).where(
            DailyCheckIn.user_id == user_id,
            DailyCheckIn.check_in_date >= start,
            DailyCheckIn.check_in_date <= anchor,
        )
    ).scalars().all()
    by_date: dict[date, DailyCheckIn] = {r.check_in_date: r for r in rows}

    slots: list[DailyCheckInWeekSlot] = []
    for i in range(7):
        d = start + timedelta(days=i)
        rec = by_date.get(d)
        slots.append(
            DailyCheckInWeekSlot(
                check_in_date=d,
                record=DailyCheckInOut.model_validate(rec) if rec is not None else None,
            )
        )
    return DailyCheckInWeekResponse(days=slots)


@router.post("/checkin", response_model=DailyCheckInOut)
def create_or_update_checkin(
    body: DailyCheckInCreate,
    db: Session = Depends(get_db),
) -> DailyCheckInOut:
    """
    Upsert: creates or updates the row for (user_id, check_in_date) so past days can be edited.
    """
    user = db.get(User, body.user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    check_date = body.check_in_date or date.today()
    existing = db.execute(
        select(DailyCheckIn).where(
            DailyCheckIn.user_id == body.user_id,
            DailyCheckIn.check_in_date == check_date,
        )
    ).scalar_one_or_none()

    payload = {
        "sleep_quality": SleepQuality(body.sleep_quality),
        "digestion": Digestion(body.digestion),
        "energy_state": EnergyState(body.energy_state),
        "movement": MovementLevel(body.movement),
        "water_glasses": body.water_glasses,
    }

    if existing is None:
        row = DailyCheckIn(
            user_id=body.user_id,
            check_in_date=check_date,
            **payload,
        )
        db.add(row)
        db.flush()
        db.refresh(row)
        out = row
    else:
        for k, v in payload.items():
            setattr(existing, k, v)
        db.flush()
        db.refresh(existing)
        out = existing

    db.add(
        AuditLog(
            actor=str(body.user_id),
            action=f"checkin.upsert date={check_date}",
        )
    )
    db.commit()
    db.refresh(out)
    return DailyCheckInOut.model_validate(out)
