"""
Fetch live environment context from OpenWeatherMap (current weather at lat/lon).
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

OWM_WEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"

# Lowercase city names from OWM — coarse signal for dense urban vs rural/suburban.
_MAJOR_URBAN_NAMES: frozenset[str] = frozenset(
    {
        "london",
        "paris",
        "tokyo",
        "new york",
        "los angeles",
        "chicago",
        "houston",
        "phoenix",
        "philadelphia",
        "san antonio",
        "san diego",
        "dallas",
        "san jose",
        "austin",
        "jacksonville",
        "san francisco",
        "columbus",
        "indianapolis",
        "seattle",
        "denver",
        "boston",
        "detroit",
        "nashville",
        "portland",
        "las vegas",
        "miami",
        "atlanta",
        "toronto",
        "vancouver",
        "montreal",
        "sydney",
        "melbourne",
        "brisbane",
        "perth",
        "delhi",
        "mumbai",
        "bengaluru",
        "bangalore",
        "kolkata",
        "chennai",
        "hyderabad",
        "singapore",
        "hong kong",
        "shanghai",
        "beijing",
        "guangzhou",
        "shenzhen",
        "seoul",
        "mexico city",
        "são paulo",
        "sao paulo",
        "rio de janeiro",
        "buenos aires",
        "berlin",
        "madrid",
        "barcelona",
        "rome",
        "milan",
        "amsterdam",
        "brussels",
        "vienna",
        "warsaw",
        "moscow",
        "istanbul",
        "cairo",
        "lagos",
        "johannesburg",
        "dubai",
        "tel aviv",
        "tel aviv-yafo",
        "dublin",
        "manchester",
        "birmingham",
        "glasgow",
        "edinburgh",
    }
)


class EnvironmentServiceError(RuntimeError):
    """Missing API key or upstream weather failure."""


def _humidity_type(humidity_pct: float) -> str:
    if humidity_pct < 42.0:
        return "dry"
    if humidity_pct > 68.0:
        return "damp"
    return "balanced"


def _habitat_from_city_name(city_name: str | None) -> str:
    if not city_name or not str(city_name).strip():
        return "Rural"
    key = str(city_name).strip().lower()
    if key in _MAJOR_URBAN_NAMES:
        return "Urban"
    # Short names often indicate towns; long unknown names still treated as less dense.
    if len(key.split()) >= 2 and any(w in key for w in ("town", "village", "rural")):
        return "Rural"
    return "Rural"


def _parse_weather_payload(data: dict[str, Any]) -> dict[str, str]:
    main = data.get("main") or {}
    weather_list = data.get("weather") or []
    w0 = weather_list[0] if weather_list else {}
    desc = str(w0.get("description", "unknown conditions")).strip() or "unknown conditions"
    temp = main.get("temp")
    humidity = main.get("humidity")
    try:
        temp_f = float(temp) if temp is not None else 0.0
    except (TypeError, ValueError):
        temp_f = 0.0
    try:
        hum_f = float(humidity) if humidity is not None else 50.0
    except (TypeError, ValueError):
        hum_f = 50.0

    city = data.get("name")
    if isinstance(city, str):
        city_name = city
    else:
        city_name = None

    weather_line = f"{temp_f:.0f}°C, {desc}" if temp is not None else desc
    return {
        "weather": weather_line,
        "humidity_type": _humidity_type(hum_f),
        "habitat": _habitat_from_city_name(city_name),
    }


async def get_environment_context(lat: float, lon: float) -> dict[str, str]:
    """
    Return a compact context dict for prompts and caching:
    - weather: human-readable temperature + conditions
    - humidity_type: dry | damp | balanced
    - habitat: Urban | Rural (approximate from city name)
    """
    key = (settings.openweather_api_key or "").strip()
    if not key:
        raise EnvironmentServiceError(
            "OPENWEATHER_API_KEY is not set. Add it to backend/.env for environment features."
        )

    params = {
        "lat": lat,
        "lon": lon,
        "appid": key,
        "units": "metric",
    }
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(12.0)) as client:
            resp = await client.get(OWM_WEATHER_URL, params=params)
            resp.raise_for_status()
            data = resp.json()
    except httpx.HTTPStatusError as exc:
        logger.warning("OpenWeather HTTP error: %s", exc)
        raise EnvironmentServiceError("Weather service returned an error.") from exc
    except httpx.RequestError as exc:
        logger.warning("OpenWeather request failed: %s", exc)
        raise EnvironmentServiceError("Could not reach weather service.") from exc

    if not isinstance(data, dict):
        raise EnvironmentServiceError("Invalid weather response.")

    return _parse_weather_payload(data)
