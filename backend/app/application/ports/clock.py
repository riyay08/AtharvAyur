from __future__ import annotations

from datetime import date, datetime
from typing import Protocol


class Clock(Protocol):
    """Time source. Override in tests to get deterministic `today` / `now`."""

    def today(self) -> date: ...
    def utc_now(self) -> datetime: ...
    def utc_today(self) -> date: ...
