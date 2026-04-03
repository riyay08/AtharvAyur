"""
Weekly plan LLM generation, normalization, persistence, and batch scheduling helpers.

Plan JSON envelope (stored in `weekly_plans.tasks` JSONB):
  daily_focus_message, days[{ date, pillars: { Mind, Fuel, Body: [{ id, task, context_reason, completed }] } }]
"""

from __future__ import annotations

import asyncio
import json
import logging
import re
import uuid
from datetime import date, datetime, timedelta, timezone
from typing import Any

from google import genai
from google.genai import types
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_session_factory
from app.models.chat_history import ChatHistory, ChatRole
from app.models.health_profile import HealthProfile
from app.models.user import User
from app.models.weekly_plan import WeeklyPlan
from app.services.llm_orchestrator import (
    WEEKLY_PLAN_DYNAMIC_STACK_SYSTEM,
    OrchestratorConfigError,
)

logger = logging.getLogger(__name__)

PILLAR_KEYS = ("Mind", "Fuel", "Body")


def week_start_monday(d: date) -> date:
    return d - timedelta(days=d.weekday())


def week_start_for_scheduled_job(run_date: date) -> date:
    """When the Sunday 02:00 job runs, the plan week starts the next Monday."""
    if run_date.weekday() == 6:
        return run_date + timedelta(days=1)
    return week_start_monday(run_date)


def _profile_json(profile: HealthProfile | None) -> str:
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
        return json.dumps(
            {
                "conditions": str(profile.conditions),
                "allergies": str(profile.allergies),
                "medications": str(profile.medications),
            },
            indent=2,
        )


def fetch_recent_user_messages(db: Session, user_id: uuid.UUID, days: int = 7) -> str:
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    stmt = (
        select(ChatHistory)
        .where(
            ChatHistory.user_id == user_id,
            ChatHistory.role == ChatRole.USER,
            ChatHistory.timestamp >= cutoff,
        )
        .order_by(desc(ChatHistory.timestamp))
        .limit(80)
    )
    rows = list(db.execute(stmt).scalars().all())
    if not rows:
        return "No user messages in the last 7 days."
    chronological = list(reversed(rows))
    return "\n".join(f"- {r.message}" for r in chronological)


def fetch_semantic_user_messages_last_days(
    db: Session,
    user_id: uuid.UUID,
    query_embedding: list[float],
    days: int = 7,
    limit: int = 5,
) -> list[ChatHistory]:
    if not query_embedding:
        return []
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    stmt = (
        select(ChatHistory)
        .where(
            ChatHistory.user_id == user_id,
            ChatHistory.role == ChatRole.USER,
            ChatHistory.timestamp >= cutoff,
            ChatHistory.embedding.is_not(None),
        )
        .order_by(ChatHistory.embedding.cosine_distance(query_embedding))
        .limit(limit)
    )
    return list(db.execute(stmt).scalars().all())


def _strip_code_fence(text: str) -> str:
    s = text.strip()
    m = re.match(r"^```(?:json)?\s*([\s\S]*?)\s*```$", s, re.IGNORECASE)
    if m:
        return m.group(1).strip()
    return s


def _extract_json_object(text: str) -> dict[str, Any]:
    s = _strip_code_fence(text)
    try:
        data = json.loads(s)
        if isinstance(data, dict):
            return data
    except json.JSONDecodeError:
        pass
    start = s.find("{")
    if start == -1:
        raise ValueError("Model output did not contain a JSON object.")
    depth = 0
    in_string = False
    escape = False
    for i in range(start, len(s)):
        ch = s[i]
        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
            continue
        if ch == '"':
            in_string = True
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                chunk = s[start : i + 1]
                return json.loads(chunk)
    raise ValueError("Unbalanced JSON object in model output.")


def _normalize_pillar_tasks(raw: Any) -> list[dict[str, Any]]:
    if not isinstance(raw, list):
        raw = []
    out: list[dict[str, Any]] = []
    for t in raw:
        if len(out) >= 8:
            break
        if not isinstance(t, dict):
            continue
        text = str(t.get("task") or t.get("title") or "Wellness task").strip()[:500]
        reason = str(
            t.get("context_reason")
            or t.get("context")
            or "Grounded in your Dosha and recent wellness themes."
        ).strip()[:2000]
        done = t.get("completed")
        if done is None:
            done = t.get("is_completed")
        completed = bool(done) if isinstance(done, bool) else False
        out.append(
            {
                "id": 0,
                "task": text,
                "context_reason": reason,
                "completed": completed,
            }
        )
    return out


def _default_task(pillar: str, reason: str) -> dict[str, Any]:
    labels = {
        "Mind": "Five minutes of slow breathing or journaling",
        "Fuel": "Warm, simple meal with mindful pacing",
        "Body": "Gentle walk or light stretching",
    }
    return {
        "id": 0,
        "task": labels.get(pillar, "Gentle wellness check-in"),
        "context_reason": reason,
        "completed": False,
    }


def max_task_id_in_envelope(root: dict[str, Any]) -> int:
    m = 0
    for day in root.get("days") or []:
        if not isinstance(day, dict):
            continue
        pillars = day.get("pillars")
        if not isinstance(pillars, dict):
            continue
        for pk in PILLAR_KEYS:
            for t in pillars.get(pk) or []:
                if not isinstance(t, dict):
                    continue
                try:
                    m = max(m, int(t.get("id") or 0))
                except (TypeError, ValueError):
                    continue
    return m


FOLLOWUP_PILLAR_TASK_SYSTEM = (
    "You are a safe wellness planner. The user just completed a task in their daily plan. "
    "Propose exactly ONE new actionable task in the SAME pillar only: "
    "Mind (mental calm, sleep routine, stress literacy), "
    "Fuel (food, hydration, meal rhythm), "
    "or Body (movement, stretching, physical recovery). "
    "Do not prescribe medicine or supplements as treatment. "
    "Respond with a single raw JSON object, no markdown, with keys "
    '"task" (short imperative, under 200 characters) and '
    '"context_reason" (under 280 characters) that explicitly links to their Dosha from the '
    "profile OR a specific recent chat theme/symptom — never vague."
)


def generate_followup_pillar_task(
    db: Session,
    user_id: uuid.UUID,
    health_profile: HealthProfile | None,
    pillar: str,
    completed_task: str,
    completed_context: str,
    plan_day_date: str,
    *,
    api_key: str | None = None,
    model: str | None = None,
) -> dict[str, Any]:
    """
    Returns one new task dict: { "task", "context_reason" } (no id; caller assigns).
    """
    key = api_key or settings.gemini_api_key
    if not key or not str(key).strip():
        raise OrchestratorConfigError("GEMINI_API_KEY is not set.")
    model_id = model or settings.gemini_model
    client = genai.Client(api_key=key)
    profile_blob = _profile_json(health_profile)
    recent = fetch_recent_user_messages(db, user_id, 7)
    recent_short = "\n".join(recent.split("\n")[-24:]) if recent else ""

    user_content = (
        f'Pillar for the new task (must stay in this pillar only): "{pillar}".\n'
        f"Plan calendar day: {plan_day_date}.\n\n"
        "The user just completed this task:\n"
        f"- Task: {completed_task}\n"
        f"- Prior context note: {completed_context}\n\n"
        f"User HealthProfile (JSON):\n{profile_blob}\n\n"
        f"Recent user messages (excerpt):\n{recent_short}\n\n"
        "Output one JSON object: {\"task\": \"...\", \"context_reason\": \"...\"}."
    )

    config = types.GenerateContentConfig(system_instruction=FOLLOWUP_PILLAR_TASK_SYSTEM)
    response = client.models.generate_content(
        model=model_id,
        contents=[
            types.Content(
                role="user",
                parts=[types.Part.from_text(text=user_content)],
            )
        ],
        config=config,
    )
    raw = (response.text or "").strip()
    if not raw:
        raise ValueError("Empty follow-up task response.")
    parsed = _extract_json_object(raw)
    task_text = str(parsed.get("task") or parsed.get("Task") or "").strip()[:500]
    reason = str(parsed.get("context_reason") or parsed.get("context") or "").strip()[:2000]
    if not task_text:
        task_text = "Short wellness check-in aligned with your day."
    if not reason:
        reason = "Continues your pillar focus using your profile and recent themes."
    return {"task": task_text, "context_reason": reason}


def _assign_sequential_task_ids(envelope: dict[str, Any]) -> None:
    """Stable unique ids for PUT /plan/task (day order × Mind → Fuel → Body × task order)."""
    n = 1
    for day in envelope.get("days", []):
        if not isinstance(day, dict):
            continue
        pillars = day.get("pillars")
        if not isinstance(pillars, dict):
            continue
        for pk in PILLAR_KEYS:
            for t in pillars.get(pk) or []:
                if isinstance(t, dict):
                    t["id"] = n
                    n += 1


def normalize_weekly_plan_payload(raw: Any, week_start: date) -> dict[str, Any]:
    """
    Returns envelope: { daily_focus_message, days: [ { date, pillars: { Mind, Fuel, Body } } ] }.
    """
    base_msg = (
        "This week emphasizes steady routines aligned with your profile and recent check-in themes."
    )

    if isinstance(raw, list):
        raw = {"daily_focus_message": base_msg, "days": raw}

    if not isinstance(raw, dict):
        raw = {}

    msg = raw.get("daily_focus_message")
    daily_focus_message = str(msg).strip() if isinstance(msg, str) and msg.strip() else base_msg

    days_in = raw.get("days")
    if not isinstance(days_in, list):
        days_in = []

    days_out: list[dict[str, Any]] = []
    for i in range(7):
        d = week_start + timedelta(days=i)
        d_str = d.isoformat()
        day_obj: dict[str, Any] = {}
        if i < len(days_in) and isinstance(days_in[i], dict):
            day_obj = days_in[i]
        if isinstance(day_obj.get("date"), str) and re.match(r"^\d{4}-\d{2}-\d{2}$", day_obj["date"]):
            d_str = day_obj["date"]

        pillars_in = day_obj.get("pillars")
        if not isinstance(pillars_in, dict):
            pillars_in = {}

        pillars_out: dict[str, list[dict[str, Any]]] = {}
        for pk in PILLAR_KEYS:
            raw_list = None
            for key, val in pillars_in.items():
                if isinstance(key, str) and key.strip().lower() == pk.lower():
                    raw_list = val
                    break
            tasks = _normalize_pillar_tasks(raw_list)
            if not tasks:
                tasks = [
                    _default_task(
                        pk,
                        f"Supports your balance for {pk.lower()} this week based on your profile.",
                    )
                ]
            pillars_out[pk] = tasks

        days_out.append({"date": d_str, "pillars": pillars_out})

    envelope = {"daily_focus_message": daily_focus_message, "days": days_out}
    _assign_sequential_task_ids(envelope)
    return envelope


def generate_weekly_plan_via_llm(
    db: Session,
    user_id: uuid.UUID,
    health_profile: HealthProfile | None,
    *,
    week_start: date | None = None,
    api_key: str | None = None,
    model: str | None = None,
) -> dict[str, Any]:
    key = api_key or settings.gemini_api_key
    if not key or not str(key).strip():
        raise OrchestratorConfigError(
            "GEMINI_API_KEY is not set. Add it to backend/.env or pass api_key=."
        )
    ws = week_start or week_start_monday(date.today())
    model_id = model or settings.gemini_model
    client = genai.Client(api_key=key)
    plan_context_query = (
        "Symptoms, complaints, energy, sleep, digestion, stress, and wellness goals the user "
        "mentioned in conversation."
    )
    query_embedding: list[float] = []
    try:
        emb = client.models.embed_content(
            model=settings.gemini_embedding_model,
            contents=[plan_context_query],
            config=types.EmbedContentConfig(output_dimensionality=768),
        )
        if emb.embeddings and emb.embeddings[0].values:
            query_embedding = list(emb.embeddings[0].values)
    except Exception as exc:
        logger.warning("Weekly plan: embedding for semantic chat context failed: %s", exc)

    semantic_rows = fetch_semantic_user_messages_last_days(db, user_id, query_embedding, 7, 5)
    semantic_block = (
        "\n".join(f"- {r.message}" for r in semantic_rows)
        if semantic_rows
        else "(No embedded messages matched in the last 7 days.)"
    )
    chronological_block = fetch_recent_user_messages(db, user_id, 7)
    profile_blob = _profile_json(health_profile)

    week_end = ws + timedelta(days=6)
    user_content = (
        f"Plan week: Monday {ws.isoformat()} through Sunday {week_end.isoformat()}.\n"
        f"User HealthProfile (JSON; includes Dosha / prakriti when available):\n{profile_blob}\n\n"
        "Semantically relevant user messages from the last 7 days (pgvector; themes only; do not diagnose):\n"
        f"{semantic_block}\n\n"
        "All user messages from the last 7 days (chronological excerpts):\n"
        f"{chronological_block}\n\n"
        "Return ONE JSON object only (no markdown), matching the schema in the system instruction. "
        f'The 7 "days[].date" values must be consecutive calendar dates from {ws.isoformat()} onward.'
    )

    config = types.GenerateContentConfig(system_instruction=WEEKLY_PLAN_DYNAMIC_STACK_SYSTEM)
    response = client.models.generate_content(
        model=model_id,
        contents=[
            types.Content(
                role="user",
                parts=[types.Part.from_text(text=user_content)],
            )
        ],
        config=config,
    )
    raw = (response.text or "").strip()
    if not raw:
        raise ValueError("Empty response from model for weekly plan.")
    parsed = _extract_json_object(raw)
    return normalize_weekly_plan_payload(parsed, ws)


def upsert_weekly_plan(
    db: Session,
    user_id: uuid.UUID,
    start_date: date,
    tasks: dict[str, Any] | list[Any],
) -> WeeklyPlan:
    existing = db.execute(
        select(WeeklyPlan).where(
            WeeklyPlan.user_id == user_id,
            WeeklyPlan.start_date == start_date,
        )
    ).scalar_one_or_none()
    if existing is not None:
        existing.tasks = tasks
        db.flush()
        db.refresh(existing)
        return existing
    row = WeeklyPlan(user_id=user_id, start_date=start_date, tasks=tasks)
    db.add(row)
    db.flush()
    db.refresh(row)
    return row


def get_current_week_plan(db: Session, user_id: uuid.UUID, today: date | None = None) -> WeeklyPlan | None:
    d = today or date.today()
    ws = week_start_monday(d)
    return db.execute(
        select(WeeklyPlan).where(
            WeeklyPlan.user_id == user_id,
            WeeklyPlan.start_date == ws,
        )
    ).scalar_one_or_none()


def user_ids_with_profile(db: Session) -> list[uuid.UUID]:
    stmt = select(User.id).join(HealthProfile, HealthProfile.user_id == User.id)
    return list(db.execute(stmt).scalars().all())


async def generate_weekly_plans_for_all_users() -> None:
    run_date = date.today()
    week_start = week_start_for_scheduled_job(run_date)
    SessionLocal = get_session_factory()
    session = SessionLocal()
    try:
        candidates = user_ids_with_profile(session)
        needing: list[uuid.UUID] = []
        for uid in candidates:
            exists = session.execute(
                select(WeeklyPlan.id).where(
                    WeeklyPlan.user_id == uid,
                    WeeklyPlan.start_date == week_start,
                )
            ).first()
            if not exists:
                needing.append(uid)
    finally:
        session.close()

    logger.info(
        "Weekly plan batch: week_start=%s users_to_process=%d",
        week_start,
        len(needing),
    )

    for uid in needing:
        db = SessionLocal()
        try:
            profile = db.execute(
                select(HealthProfile).where(HealthProfile.user_id == uid)
            ).scalar_one_or_none()
            payload = generate_weekly_plan_via_llm(db, uid, profile, week_start=week_start)
            upsert_weekly_plan(db, uid, week_start, payload)
            db.commit()
            logger.info("Weekly plan saved for user %s", uid)
        except Exception as exc:
            logger.exception("Weekly plan generation failed for user %s: %s", uid, exc)
            db.rollback()
        finally:
            db.close()
        await asyncio.sleep(2)
