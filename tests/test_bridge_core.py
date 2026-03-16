from pathlib import Path
import sys
from typing import Any, Dict

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import clawlendar.bridge as bridge_module  # noqa: E402
from clawlendar.bridge import (  # noqa: E402
    CalendarError,
    make_registry,
    run_astro_snapshot,
    run_calendar_month,
    run_capabilities,
    run_convert,
    run_day_profile,
    run_historical_resolve,
    run_historical_spacetime_snapshot,
    run_life_context,
    run_spacetime_snapshot,
    run_timeline,
    run_weather_at_time,
    run_weather_now,
)


def test_capabilities_exposes_life_context_and_i18n() -> None:
    registry, warnings = make_registry()
    result = run_capabilities(registry, warnings)

    assert result["command"] == "capabilities"
    assert result["commands"]["life_context"] is True
    assert result["commands"]["weather_now"] is True
    assert result["commands"]["weather_at_time"] is True
    assert result["commands"]["spacetime_snapshot"] is True
    assert result["commands"]["historical_resolve"] is True
    assert result["commands"]["historical_spacetime_snapshot"] is True
    assert "zh-CN" in result["i18n"]["supported_locales"]


def test_convert_localizes_sexagenary_for_zh_tw() -> None:
    registry, warnings = make_registry()
    result = run_convert(
        registry=registry,
        warnings=warnings,
        source="gregorian",
        targets=["sexagenary"],
        payload={"year": 2026, "month": 3, "day": 9},
        locale="zh-TW",
    )

    payload = result["results"]["sexagenary"]["payload"]
    assert payload["locale"] == "zh-Hant"
    assert payload["display"]
    assert payload["stem_label"]
    assert payload["branch_label"]


def test_day_profile_includes_huangli_fields() -> None:
    registry, warnings = make_registry()
    result = run_day_profile(
        registry=registry,
        warnings=warnings,
        input_payload={"timestamp": 1773014400},
        timezone_name="Asia/Taipei",
        date_basis="local",
        include_astro=False,
        include_metaphysics=True,
        locale="zh-CN",
    )

    assert result["command"] == "day_profile"
    eastern = result["metaphysics"]["eastern"]
    huangli = eastern["huangli"]
    assert isinstance(huangli["yi"], list) and len(huangli["yi"]) > 0
    assert isinstance(huangli["ji"], list) and len(huangli["ji"]) > 0
    assert "clash" in huangli
    assert "sha_direction" in huangli


def test_timeline_projects_multiple_targets() -> None:
    registry, warnings = make_registry()
    result = run_timeline(
        registry=registry,
        warnings=warnings,
        input_payload={"timestamp": 1773014400},
        timezone_name="Asia/Taipei",
        date_basis="local",
        targets=["minguo", "japanese_era", "sexagenary", "solar_term_24"],
        locale="zh-TW",
    )

    assert result["command"] == "timeline"
    assert result["locale"] == "zh-Hant"
    assert "minguo" in result["calendar_projection"]["results"]
    assert "japanese_era" in result["calendar_projection"]["results"]
    assert "sexagenary" in result["calendar_projection"]["results"]
    assert "solar_term_24" in result["calendar_projection"]["results"]


def test_astro_snapshot_shape() -> None:
    _, warnings = make_registry()
    result = run_astro_snapshot(
        warnings=warnings,
        input_payload={"timestamp": 1773014400},
        timezone_name="Asia/Taipei",
        zodiac_system="tropical",
        bodies=None,
    )

    assert result["command"] == "astro_snapshot"
    assert len(result["seven_governors"]) == 7
    assert len(result["four_remainders"]) == 4
    assert isinstance(result["major_aspects"], list)


def test_astro_snapshot_includes_symbols() -> None:
    _, warnings = make_registry()
    result = run_astro_snapshot(
        warnings=warnings,
        input_payload={"timestamp": 1773014400},
        timezone_name="Asia/Taipei",
    )

    sun = next(item for item in result["seven_governors"] if item["name"] == "sun")
    assert sun["symbol"] == "☉"
    ascending_node = next(item for item in result["four_remainders"] if item["name"] == "ascending_node")
    assert ascending_node["symbol"] == "☊"
    if result["major_aspects"]:
        aspect = result["major_aspects"][0]
        assert "aspect_symbol" in aspect


def test_optional_calendars_convert_when_available() -> None:
    registry, warnings = make_registry()
    optional_targets = [name for name in ("chinese_lunar", "islamic", "hebrew", "persian") if name in registry]
    if not optional_targets:
        pytest.skip("Optional calendars are not installed in this environment")

    result = run_convert(
        registry=registry,
        warnings=warnings,
        source="gregorian",
        targets=optional_targets,
        payload={"year": 2026, "month": 3, "day": 9},
        locale="en",
    )
    assert result["command"] == "convert"
    for target in optional_targets:
        assert target in result["results"]


def test_life_context_contains_time_space_subject_anchors() -> None:
    registry, warnings = make_registry()
    result = run_life_context(
        registry=registry,
        warnings=warnings,
        birth_input_payload={"iso_datetime": "2026-03-01T09:00:00+08:00"},
        now_input_payload={"iso_datetime": "2026-03-09T18:30:00+08:00"},
        timezone_name="Asia/Taipei",
        date_basis="local",
        space_payload={
            "location_name": "南京·秦淮河",
            "background": "春季夜游",
            "environment_tags": ["city", "river"],
        },
        subject_payload={
            "entity_id": "lobster-001",
            "role": "18岁女儿",
            "soul": "温柔且主动问候",
            "traits": ["warm", "curious"],
        },
        locale="zh-CN",
    )

    assert result["command"] == "life_context"
    assert result["life"]["life_id"] == "lobster-001"
    assert result["life"]["age"]["seconds"] > 0
    assert result["life"]["birthday"]["month"] == 3
    assert result["life"]["birthday"]["day"] == 1
    assert result["space"]["location_name"] == "南京·秦淮河"
    assert result["space"]["background"] == "春季夜游"
    assert result["subject"]["role"] == "18岁女儿"
    assert result["environment"]["place"]["location_name"] == "南京·秦淮河"
    assert "南京·秦淮河" in result["world_context"]["scene_prompt"]


def test_life_context_rejects_now_before_birth() -> None:
    registry, warnings = make_registry()

    with pytest.raises(CalendarError):
        run_life_context(
            registry=registry,
            warnings=warnings,
            birth_input_payload={"iso_datetime": "2026-03-10T00:00:00+08:00"},
            now_input_payload={"iso_datetime": "2026-03-09T00:00:00+08:00"},
            timezone_name="Asia/Taipei",
        )


def test_life_context_can_disable_auto_weather() -> None:
    registry, warnings = make_registry()
    result = run_life_context(
        registry=registry,
        warnings=warnings,
        birth_input_payload={"iso_datetime": "2026-03-01T09:00:00+08:00"},
        now_input_payload={"iso_datetime": "2026-03-09T18:30:00+08:00"},
        timezone_name="Asia/Taipei",
        space_payload={
            "location_name": "台北",
            "latitude": 25.033,
            "longitude": 121.5654,
            "weather_note": "多云",
            "scenery_note": "城市夜景",
        },
        auto_weather=False,
    )

    environment = result["environment"]
    assert environment["weather"] is None
    assert environment["weather_note"] == "多云"
    assert environment["scenery_note"] == "城市夜景"


def test_life_context_weather_uses_now_anchor_and_temporal_context(monkeypatch: pytest.MonkeyPatch) -> None:
    registry, warnings = make_registry()
    captured: Dict[str, Any] = {}

    def fake_weather_for_instant(
        latitude: float,
        longitude: float,
        timezone_name: str,
        anchor_local,
    ) -> Dict[str, Any]:
        captured["latitude"] = latitude
        captured["longitude"] = longitude
        captured["timezone_name"] = timezone_name
        captured["anchor_local"] = anchor_local
        return {
            "provider": "open_meteo",
            "data_mode": "archive_reanalysis",
            "time": "2026-03-09T18:00",
            "requested_time_local": anchor_local.isoformat(),
            "time_delta_minutes": 30,
            "temperature_c": 20.5,
            "apparent_temperature_c": 20.0,
            "relative_humidity_pct": 70,
            "precipitation_mm": 0.0,
            "wind_speed_kmh": 5.0,
            "weather_code": 1,
            "weather_label": "mainly_clear",
            "timezone": timezone_name,
        }

    monkeypatch.setattr(bridge_module, "fetch_open_meteo_weather_for_instant", fake_weather_for_instant)
    result = run_life_context(
        registry=registry,
        warnings=warnings,
        birth_input_payload={"iso_datetime": "2026-03-01T09:00:00+08:00"},
        now_input_payload={"iso_datetime": "2026-03-09T18:30:00+08:00"},
        timezone_name="Asia/Taipei",
        space_payload={
            "location_name": "台北",
            "latitude": 25.033,
            "longitude": 121.5654,
        },
        auto_weather=True,
    )

    assert captured["latitude"] == 25.033
    assert captured["longitude"] == 121.5654
    assert captured["timezone_name"] == "Asia/Taipei"
    assert captured["anchor_local"].isoformat().startswith("2026-03-09T18:30:00")
    assert result["environment"]["weather"]["requested_time_local"].startswith("2026-03-09T18:30:00")
    assert result["temporal_context"]["local_date"] == "2026-03-09"
    assert result["temporal_context"]["season_meteorological"] in {"spring", "summer", "autumn", "winter"}


def test_weather_at_time_returns_time_anchored_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    _, warnings = make_registry()

    def fake_weather_for_instant(
        latitude: float,
        longitude: float,
        timezone_name: str,
        anchor_local,
    ) -> Dict[str, Any]:
        assert latitude == 25.033
        assert longitude == 121.5654
        assert timezone_name == "Asia/Taipei"
        assert anchor_local.isoformat().startswith("2026-03-09T18:30:00")
        return {
            "provider": "open_meteo",
            "data_mode": "archive_reanalysis",
            "time": "2026-03-09T18:00",
            "requested_time_local": anchor_local.isoformat(),
            "time_delta_minutes": 30,
            "temperature_c": 20.5,
            "apparent_temperature_c": 20.0,
            "relative_humidity_pct": 70,
            "precipitation_mm": 0.0,
            "wind_speed_kmh": 5.0,
            "weather_code": 1,
            "weather_label": "mainly_clear",
            "timezone": timezone_name,
        }

    monkeypatch.setattr(bridge_module, "fetch_open_meteo_weather_for_instant", fake_weather_for_instant)
    result = run_weather_at_time(
        warnings=warnings,
        input_payload={"iso_datetime": "2026-03-09T18:30:00+08:00"},
        location_payload={"location_name": "Taipei", "latitude": 25.033, "longitude": 121.5654},
        timezone_name="Asia/Taipei",
        locale="en",
    )

    assert result["command"] == "weather_at_time"
    assert result["weather"]["data_mode"] == "archive_reanalysis"
    assert result["weather"]["time_delta_minutes"] == 30
    assert result["temporal_context"]["local_date"] == "2026-03-09"


def test_weather_now_requires_lat_lon() -> None:
    _, warnings = make_registry()
    with pytest.raises(CalendarError):
        run_weather_now(
            warnings=warnings,
            location_payload={"location_name": "unknown"},
            timezone_name="Asia/Taipei",
        )


def test_calendar_month_mode_still_works_for_minguo() -> None:
    registry, warnings = make_registry()
    result = run_calendar_month(
        registry=registry,
        warnings=warnings,
        source="minguo",
        month_payload={"year": 115, "month": 3},
    )

    assert result["command"] == "calendar_month"
    assert result["month_payload"]["month"] == 3
    assert len(result["days"]) >= 28


def test_spacetime_snapshot_aggregates_day_weather_and_scene(monkeypatch: pytest.MonkeyPatch) -> None:
    registry, warnings = make_registry()

    def fake_weather_at_time(*args, **kwargs):  # type: ignore[no-untyped-def]
        return {
            "command": "weather_at_time",
            "weather": {
                "provider": "open_meteo",
                "data_mode": "archive_reanalysis",
                "weather_label": "partly_cloudy",
                "temperature_c": 21.2,
            },
            "warnings": [],
        }

    monkeypatch.setattr(bridge_module, "run_weather_at_time", fake_weather_at_time)
    result = run_spacetime_snapshot(
        registry=registry,
        warnings=warnings,
        input_payload={"iso_datetime": "2026-03-09T18:30:00+08:00"},
        timezone_name="Asia/Taipei",
        date_basis="local",
        location_payload={
            "location_name": "Taipei",
            "latitude": 25.033,
            "longitude": 121.5654,
            "background": "night city lights",
        },
        subject_payload={"entity_id": "lobster-001", "role": "time traveler"},
        locale="zh-CN",
        include_weather=True,
    )

    assert result["command"] == "spacetime_snapshot"
    assert result["subject"]["entity_id"] == "lobster-001"
    assert result["weather_context"]["weather"]["weather_label"] == "partly_cloudy"
    assert result["timeline"]["calendar_projection"]["results"]
    assert result["day_profile"]["calendar_details"]["chinese_lunar"] is not None
    assert "scene_prompt" in result["world_context"]


def test_historical_resolve_supports_julian_day() -> None:
    registry, warnings = make_registry()
    result = run_historical_resolve(
        registry=registry,
        warnings=warnings,
        historical_input_payload={"julian_day": 2461115.5},
        timezone_name="UTC",
        location_payload={"historical_name": "Rome", "present_day_reference": "Rome"},
        locale="en",
    )

    assert result["command"] == "historical_resolve"
    assert result["time_anchor"]["input_mode"] == "julian_day"
    assert result["time_anchor"]["bridge_date_gregorian"] == {"year": 2026, "month": 3, "day": 16}
    assert result["place_anchor"]["resolved_name"] == "Rome"


def test_historical_spacetime_snapshot_supports_source_calendar() -> None:
    registry, warnings = make_registry()
    result = run_historical_spacetime_snapshot(
        registry=registry,
        warnings=warnings,
        historical_input_payload={
            "source_calendar": "julian",
            "source_payload": {"year": 1400, "month": 3, "day": 10},
        },
        timezone_name="Europe/Rome",
        location_payload={
            "historical_name": "Florence",
            "present_day_reference": "Firenze",
            "historical_admin": {"polity": "Republic of Florence"},
            "latitude": 43.7696,
            "longitude": 11.2558,
            "background": "merchant republic city center",
        },
        subject_payload={"role": "scribe"},
        targets=["gregorian", "julian", "sexagenary", "chinese_lunar"],
        locale="en",
        include_astro=False,
        include_metaphysics=False,
    )

    assert result["command"] == "historical_spacetime_snapshot"
    assert result["time_anchor"]["source_calendar"] == "julian"
    assert result["environment_context"]["environment_mode"] == "historical_proxy"
    assert result["place_anchor"]["historical_admin"]["details"]["polity"] == "Republic of Florence"
    assert isinstance(result["provenance"], list) and len(result["provenance"]) >= 3
    assert "calendar_projection" in result["timeline"]
    assert "chinese_lunar" not in result["timeline"]["calendar_projection"]["results"]


def test_historical_spacetime_snapshot_rejects_bce_range() -> None:
    registry, warnings = make_registry()
    with pytest.raises(CalendarError):
        run_historical_spacetime_snapshot(
            registry=registry,
            warnings=warnings,
            historical_input_payload={"proleptic_gregorian": {"year": 0, "month": 1, "day": 1}},
            timezone_name="UTC",
        )
