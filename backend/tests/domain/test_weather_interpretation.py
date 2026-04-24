from __future__ import annotations

from app.domain.services.weather_interpretation import (
    habitat_from_city_name,
    humidity_band,
    interpret_openweather_payload,
)
from app.domain.value_objects import Habitat, HumidityBand


def test_humidity_band_dry_threshold() -> None:
    assert humidity_band(30.0) is HumidityBand.DRY
    assert humidity_band(41.9) is HumidityBand.DRY


def test_humidity_band_balanced_range() -> None:
    assert humidity_band(42.0) is HumidityBand.BALANCED
    assert humidity_band(55.0) is HumidityBand.BALANCED
    assert humidity_band(68.0) is HumidityBand.BALANCED


def test_humidity_band_damp_threshold() -> None:
    assert humidity_band(68.1) is HumidityBand.DAMP
    assert humidity_band(95.0) is HumidityBand.DAMP


def test_habitat_known_urban_city() -> None:
    assert habitat_from_city_name("Tokyo") is Habitat.URBAN
    assert habitat_from_city_name("  NEW YORK  ") is Habitat.URBAN


def test_habitat_unknown_city_is_rural() -> None:
    assert habitat_from_city_name("Smalltownsville") is Habitat.RURAL


def test_habitat_empty_returns_rural() -> None:
    assert habitat_from_city_name("") is Habitat.RURAL
    assert habitat_from_city_name(None) is Habitat.RURAL


def test_interpret_openweather_payload_happy_path() -> None:
    out = interpret_openweather_payload(
        {
            "main": {"temp": 22.4, "humidity": 75},
            "weather": [{"description": "light rain"}],
            "name": "London",
        }
    )
    assert out == {
        "weather": "22°C, light rain",
        "humidity_type": HumidityBand.DAMP.value,
        "habitat": Habitat.URBAN.value,
    }


def test_interpret_openweather_payload_missing_fields() -> None:
    out = interpret_openweather_payload({})
    assert out["habitat"] == Habitat.RURAL.value
    assert out["humidity_type"] == HumidityBand.BALANCED.value
    assert "unknown" in out["weather"].lower()
