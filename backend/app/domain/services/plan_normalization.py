"""Pure normalization rules for a weekly plan envelope.

Takes a raw dict/list (shape may vary based on LLM output) and returns the canonical
7-day envelope. No LLM, no DB — just shape enforcement and sensible defaults.
"""

from __future__ import annotations

import json
import re
from datetime import date, timedelta
from typing import Any

from app.domain.errors import ValidationError
from app.domain.value_objects import Pillar

_BASE_FOCUS_MESSAGE = (
    "This week emphasizes steady routines aligned with your profile and recent check-in themes."
)

_PILLAR_DEFAULT_TASKS: dict[Pillar, str] = {
    Pillar.MIND: "Five minutes of slow breathing or journaling",
    Pillar.FUEL: "Warm, simple meal with mindful pacing",
    Pillar.BODY: "Gentle walk or light stretching",
}

_MAX_TASKS_PER_PILLAR = 8
_MAX_TASK_TEXT = 500
_MAX_REASON_TEXT = 2000


def strip_code_fence(text: str) -> str:
    s = text.strip()
    m = re.match(r"^```(?:json)?\s*([\s\S]*?)\s*```$", s, re.IGNORECASE)
    if m:
        return m.group(1).strip()
    return s


def extract_json_object(text: str) -> dict[str, Any]:
    """Best-effort JSON object extractor tolerant of LLM chatter and code fences."""
    s = strip_code_fence(text)
    try:
        data = json.loads(s)
        if isinstance(data, dict):
            return data
    except json.JSONDecodeError:
        pass

    start = s.find("{")
    if start == -1:
        raise ValidationError("Model output did not contain a JSON object.")

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
    raise ValidationError("Unbalanced JSON object in model output.")


def _normalize_pillar_tasks(raw: Any) -> list[dict[str, Any]]:
    if not isinstance(raw, list):
        raw = []
    out: list[dict[str, Any]] = []
    for t in raw:
        if len(out) >= _MAX_TASKS_PER_PILLAR:
            break
        if not isinstance(t, dict):
            continue
        text = str(t.get("task") or t.get("title") or "Wellness task").strip()[:_MAX_TASK_TEXT]
        reason = str(
            t.get("context_reason")
            or t.get("context")
            or "Grounded in your Dosha and recent wellness themes."
        ).strip()[:_MAX_REASON_TEXT]
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


def _default_pillar_task(pillar: Pillar, reason: str) -> dict[str, Any]:
    return {
        "id": 0,
        "task": _PILLAR_DEFAULT_TASKS.get(pillar, "Gentle wellness check-in"),
        "context_reason": reason,
        "completed": False,
    }


def _assign_sequential_task_ids(envelope: dict[str, Any]) -> None:
    """Stable ids across day order × Mind → Fuel → Body × task order."""
    n = 1
    for day in envelope.get("days", []):
        if not isinstance(day, dict):
            continue
        pillars = day.get("pillars")
        if not isinstance(pillars, dict):
            continue
        for pk in Pillar.all():
            for t in pillars.get(pk.value) or []:
                if isinstance(t, dict):
                    t["id"] = n
                    n += 1


def normalize_weekly_plan_payload(raw: Any, week_start: date) -> dict[str, Any]:
    """Coerce whatever the LLM returned into a strict 7-day envelope."""
    if isinstance(raw, list):
        raw = {"daily_focus_message": _BASE_FOCUS_MESSAGE, "days": raw}
    if not isinstance(raw, dict):
        raw = {}

    msg = raw.get("daily_focus_message")
    daily_focus_message = (
        str(msg).strip() if isinstance(msg, str) and msg.strip() else _BASE_FOCUS_MESSAGE
    )

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
        for pk in Pillar.all():
            raw_list = None
            for key, val in pillars_in.items():
                if isinstance(key, str) and key.strip().lower() == pk.value.lower():
                    raw_list = val
                    break
            tasks = _normalize_pillar_tasks(raw_list)
            if not tasks:
                tasks = [
                    _default_pillar_task(
                        pk,
                        f"Supports your balance for {pk.value.lower()} this week based on your profile.",
                    )
                ]
            pillars_out[pk.value] = tasks

        days_out.append({"date": d_str, "pillars": pillars_out})

    envelope = {"daily_focus_message": daily_focus_message, "days": days_out}
    _assign_sequential_task_ids(envelope)
    return envelope
