"""OpenWeatherMap-backed `WeatherGateway` implementation."""

from __future__ import annotations

import logging

import httpx

from app.config import settings
from app.domain.errors import ConfigurationError, ExternalServiceError
from app.domain.services.weather_interpretation import interpret_openweather_payload

logger = logging.getLogger(__name__)

_OWM_WEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"


class OpenWeatherWeatherGateway:
    def __init__(self, *, api_key: str | None = None, timeout_s: float = 12.0) -> None:
        self._api_key = (api_key or settings.openweather_api_key or "").strip()
        self._timeout = timeout_s

    async def get_context(self, *, lat: float, lon: float) -> dict[str, str]:
        if not self._api_key:
            raise ConfigurationError("OPENWEATHER_API_KEY is not set.")
        params = {
            "lat": lat,
            "lon": lon,
            "appid": self._api_key,
            "units": "metric",
        }
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(self._timeout)) as client:
                resp = await client.get(_OWM_WEATHER_URL, params=params)
                resp.raise_for_status()
                data = resp.json()
        except httpx.HTTPStatusError as exc:
            logger.warning("OpenWeather HTTP error: %s", exc)
            raise ExternalServiceError("Weather service returned an error.") from exc
        except httpx.RequestError as exc:
            logger.warning("OpenWeather request failed: %s", exc)
            raise ExternalServiceError("Could not reach weather service.") from exc

        if not isinstance(data, dict):
            raise ExternalServiceError("Invalid weather response.")
        return interpret_openweather_payload(data)
