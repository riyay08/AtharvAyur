from __future__ import annotations

from datetime import date

from app.domain.services.week_calendar import (
    week_start_for_scheduled_job,
    week_start_monday,
)


def test_week_start_for_monday_is_itself() -> None:
    assert week_start_monday(date(2026, 4, 20)) == date(2026, 4, 20)


def test_week_start_for_mid_week_rolls_back_to_monday() -> None:
    assert week_start_monday(date(2026, 4, 23)) == date(2026, 4, 20)


def test_week_start_for_sunday_rolls_back_6_days() -> None:
    assert week_start_monday(date(2026, 4, 26)) == date(2026, 4, 20)


def test_scheduled_job_on_sunday_targets_next_monday() -> None:
    assert week_start_for_scheduled_job(date(2026, 4, 26)) == date(2026, 4, 27)


def test_scheduled_job_on_weekday_targets_current_monday() -> None:
    assert week_start_for_scheduled_job(date(2026, 4, 22)) == date(2026, 4, 20)
