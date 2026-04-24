from __future__ import annotations

from datetime import date, datetime, timezone


class SystemClock:
    """Real-world wall clock. Implements `app.application.ports.clock.Clock`."""

    def today(self) -> date:
        return date.today()

    def utc_now(self) -> datetime:
        return datetime.now(timezone.utc)

    def utc_today(self) -> date:
        return datetime.now(timezone.utc).date()
