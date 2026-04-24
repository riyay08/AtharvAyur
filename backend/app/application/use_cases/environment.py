from __future__ import annotations

import json
import uuid
from dataclasses import dataclass

from app.application.dtos import DailyTipView, GetOrCreateDailyTipInput
from app.application.ports.clock import Clock
from app.application.ports.llm_gateway import LLMGateway
from app.application.ports.repositories import (
    AuditLogRepository,
    EnvironmentTipRepository,
    HealthProfileRepository,
)
from app.application.ports.unit_of_work import UnitOfWork
from app.application.ports.weather_gateway import WeatherGateway
from app.domain.entities import DailyEnvironmentTip
from app.domain.errors import ExternalServiceError
from app.domain.services.plan_normalization import extract_json_object


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
        return "{}"


def _fallback_tip() -> dict[str, str]:
    return {
        "tip_title": "Steady breath, steady day",
        "tip_description": (
            "Take two minutes to slow your breathing and notice your surroundings. "
            "Your day goes where your attention goes."
        ),
        "icon_name": "Wind",
    }


@dataclass(frozen=True, slots=True)
class GetOrCreateDailyEnvironmentTip:
    tips: EnvironmentTipRepository
    profiles: HealthProfileRepository
    audit: AuditLogRepository
    weather: WeatherGateway
    llm: LLMGateway
    clock: Clock
    uow: UnitOfWork

    async def execute(self, cmd: GetOrCreateDailyTipInput) -> DailyTipView:
        today = self.clock.utc_today()
        existing = self.tips.get_for_date(cmd.user_id, today)
        if existing is not None:
            return DailyTipView(
                id=existing.id,
                tip_date=existing.tip_date,
                tip_title=existing.tip_title,
                tip_description=existing.tip_description,
                icon_name=existing.icon_name,
                created_at=existing.created_at,
            )

        profile = self.profiles.get_by_user_id(cmd.user_id)
        dosha = profile.dominant_dosha.value if profile and profile.dominant_dosha else None

        try:
            ctx = await self.weather.get_context(lat=cmd.lat, lon=cmd.lon)
            env_blob = json.dumps(ctx, indent=2)
        except ExternalServiceError:
            env_blob = "{}"

        parsed: dict[str, str] = {}
        try:
            raw = self.llm.generate_environment_tip_json(
                profile_blob_json=_profile_blob(profile),
                dominant_dosha=dosha,
                environment_blob_json=env_blob,
            )
            if raw.strip():
                obj = extract_json_object(raw)
                parsed = {
                    "tip_title": str(obj.get("tip_title") or "").strip()[:512],
                    "tip_description": str(obj.get("tip_description") or "").strip()[:4000],
                    "icon_name": str(obj.get("icon_name") or "").strip()[:64],
                }
        except Exception:
            parsed = {}

        if not parsed.get("tip_title") or not parsed.get("tip_description"):
            parsed = _fallback_tip()

        tip = DailyEnvironmentTip(
            id=uuid.uuid4(),
            user_id=cmd.user_id,
            tip_date=today,
            tip_title=parsed["tip_title"],
            tip_description=parsed["tip_description"],
            icon_name=parsed.get("icon_name") or "Wind",
        )
        saved = self.tips.add(tip)
        self.audit.record(actor=str(cmd.user_id), action="environment.tip_created")
        self.uow.commit()
        return DailyTipView(
            id=saved.id,
            tip_date=saved.tip_date,
            tip_title=saved.tip_title,
            tip_description=saved.tip_description,
            icon_name=saved.icon_name,
            created_at=saved.created_at,
        )
