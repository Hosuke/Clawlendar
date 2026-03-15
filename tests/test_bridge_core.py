from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from clawlendar.bridge import (  # noqa: E402
    CalendarError,
    make_registry,
    run_astro_snapshot,
    run_calendar_month,
    run_capabilities,
    run_convert,
    run_day_profile,
    run_life_context,
    run_timeline,
)


def test_capabilities_exposes_life_context_and_i18n() -> None:
    registry, warnings = make_registry()
    result = run_capabilities(registry, warnings)

    assert result["command"] == "capabilities"
    assert result["commands"]["life_context"] is True
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
