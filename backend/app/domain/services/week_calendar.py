"""Calendar helpers for week-based plans."""

from __future__ import annotations

from datetime import date, timedelta


def week_start_monday(d: date) -> date:
    """Return the Monday on or before `d`."""
    return d - timedelta(days=d.weekday())


def week_start_for_scheduled_job(run_date: date) -> date:
    """Anchor week for the Sunday-evening scheduled generation job.

    Sunday runs always target the *next* Monday (because by the time the job
    runs on Sunday night the user needs Monday's plan). Any other weekday
    resolves to the current week's Monday.
    """
    if run_date.weekday() == 6:
        return run_date + timedelta(days=1)
    return week_start_monday(run_date)
