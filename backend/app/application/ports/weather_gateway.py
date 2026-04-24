from __future__ import annotations

from typing import Protocol


class WeatherGateway(Protocol):
    """Fetches live weather context. Implementations must raise
    `app.domain.errors.ExternalServiceError` on failure.
    """

    async def get_context(self, *, lat: float, lon: float) -> dict[str, str]:
        """Return a context dict: `{weather, humidity_type, habitat}`."""
        ...
