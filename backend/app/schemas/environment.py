from __future__ import annotations

import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field


class DailyEnvironmentTipRequest(BaseModel):
    user_id: uuid.UUID
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)


class DailyEnvironmentTipOut(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    tip_date: date
    tip_title: str
    tip_description: str
    icon_name: str
    created_at: datetime
    cached: bool = False

    model_config = {"from_attributes": True}
