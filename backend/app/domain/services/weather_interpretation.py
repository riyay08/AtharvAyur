"""Pure classifiers that turn raw weather numbers / city names into domain buckets."""

from __future__ import annotations

from typing import Any

from app.domain.value_objects import Habitat, HumidityBand

_DRY_THRESHOLD_PCT = 42.0
_DAMP_THRESHOLD_PCT = 68.0

# Coarse signal for dense urban context. OWM returns English city names.
_MAJOR_URBAN_NAMES: frozenset[str] = frozenset(
    {
        "london", "paris", "tokyo", "new york", "los angeles", "chicago", "houston",
        "phoenix", "philadelphia", "san antonio", "san diego", "dallas", "san jose",
        "austin", "jacksonville", "san francisco", "columbus", "indianapolis", "seattle",
        "denver", "boston", "detroit", "nashville", "portland", "las vegas", "miami",
        "atlanta", "toronto", "vancouver", "montreal", "sydney", "melbourne", "brisbane",
        "perth", "delhi", "mumbai", "bengaluru", "bangalore", "kolkata", "chennai",
        "hyderabad", "singapore", "hong kong", "shanghai", "beijing", "guangzhou",
        "shenzhen", "seoul", "mexico city", "são paulo", "sao paulo", "rio de janeiro",
        "buenos aires", "berlin", "madrid", "barcelona", "rome", "milan", "amsterdam",
        "brussels", "vienna", "warsaw", "moscow", "istanbul", "cairo", "lagos",
        "johannesburg", "dubai", "tel aviv", "tel aviv-yafo", "dublin", "manchester",
        "birmingham", "glasgow", "edinburgh",
    }
)


def humidity_band(humidity_pct: float) -> HumidityBand:
    if humidity_pct < _DRY_THRESHOLD_PCT:
        return HumidityBand.DRY
    if humidity_pct > _DAMP_THRESHOLD_PCT:
        return HumidityBand.DAMP
    return HumidityBand.BALANCED


def habitat_from_city_name(city_name: str | None) -> Habitat:
    if not city_name or not str(city_name).strip():
        return Habitat.RURAL
    key = str(city_name).strip().lower()
    if key in _MAJOR_URBAN_NAMES:
        return Habitat.URBAN
    return Habitat.RURAL


def interpret_openweather_payload(data: dict[str, Any]) -> dict[str, str]:
    """Turn the raw OpenWeatherMap /weather response into a compact context dict.

    Accepts the data shape as-is (`main.temp`, `main.humidity`, `weather[0].description`,
    `name`) and returns a dict safe to feed to LLM prompts and to cache.
    """
    main = data.get("main") or {}
    weather_list = data.get("weather") or []
    w0 = weather_list[0] if weather_list else {}
    desc = str(w0.get("description", "unknown conditions")).strip() or "unknown conditions"

    temp = main.get("temp")
    try:
        temp_c = float(temp) if temp is not None else 0.0
    except (TypeError, ValueError):
        temp_c = 0.0

    humidity = main.get("humidity")
    try:
        hum_f = float(humidity) if humidity is not None else 50.0
    except (TypeError, ValueError):
        hum_f = 50.0

    city = data.get("name")
    city_name = city if isinstance(city, str) else None

    weather_line = f"{temp_c:.0f}°C, {desc}" if temp is not None else desc
    return {
        "weather": weather_line,
        "humidity_type": humidity_band(hum_f).value,
        "habitat": habitat_from_city_name(city_name).value,
    }
