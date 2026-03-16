from pathlib import Path
import sys

import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

import scripts.api_server as api_module  # noqa: E402
from scripts.api_server import app  # noqa: E402


client = TestClient(app)


def test_health_endpoint() -> None:
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_capabilities_endpoint_includes_life_context() -> None:
    resp = client.get("/capabilities")
    assert resp.status_code == 200
    data = resp.json()
    assert data["command"] == "capabilities"
    assert data["commands"]["life_context"] is True
    assert data["commands"]["weather_now"] is True
    assert data["commands"]["weather_at_time"] is True
    assert data["commands"]["spacetime_snapshot"] is True
    assert data["commands"]["historical_resolve"] is True
    assert data["commands"]["historical_spacetime_snapshot"] is True


def test_convert_endpoint_basic() -> None:
    resp = client.post(
        "/convert",
        json={
            "source": "gregorian",
            "targets": ["minguo", "iso_week"],
            "source_payload": {"year": 2026, "month": 3, "day": 9},
            "locale": "en",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["command"] == "convert"
    assert "minguo" in data["results"]
    assert "iso_week" in data["results"]


def test_calendar_month_endpoint_minguo() -> None:
    resp = client.post(
        "/calendar-month",
        json={"source": "minguo", "month_payload": {"year": 115, "month": 3}},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["command"] == "calendar_month"
    assert data["source"] == "minguo"
    assert len(data["days"]) >= 28


def test_day_profile_endpoint_huangli() -> None:
    resp = client.post(
        "/day-profile",
        json={
            "input_payload": {"timestamp": 1773014400},
            "timezone": "Asia/Taipei",
            "date_basis": "local",
            "include_astro": False,
            "include_metaphysics": True,
            "locale": "zh-CN",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["command"] == "day_profile"
    huangli = data["metaphysics"]["eastern"]["huangli"]
    assert isinstance(huangli.get("yi"), list)
    assert isinstance(huangli.get("ji"), list)


def test_life_context_endpoint_with_space_subject() -> None:
    resp = client.post(
        "/life-context",
        json={
            "birth_input_payload": {"iso_datetime": "2026-03-01T09:00:00+08:00"},
            "now_input_payload": {"iso_datetime": "2026-03-09T18:30:00+08:00"},
            "timezone": "Asia/Taipei",
            "date_basis": "local",
            "space_payload": {
                "location_name": "南京·秦淮河",
                "background": "春季夜游",
                "environment_tags": ["city", "river"],
            },
            "subject_payload": {
                "entity_id": "lobster-001",
                "role": "18岁女儿",
                "soul": "温柔且主动问候",
            },
            "locale": "zh-CN",
            "auto_weather": False,
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["command"] == "life_context"
    assert data["life"]["life_id"] == "lobster-001"
    assert data["life"]["birthday"]["month"] == 3
    assert data["space"]["location_name"] == "南京·秦淮河"
    assert data["subject"]["role"] == "18岁女儿"


def test_life_context_endpoint_rejects_reverse_time() -> None:
    resp = client.post(
        "/life-context",
        json={
            "birth_input_payload": {"iso_datetime": "2026-03-10T00:00:00+08:00"},
            "now_input_payload": {"iso_datetime": "2026-03-09T00:00:00+08:00"},
            "timezone": "Asia/Taipei",
        },
    )
    assert resp.status_code == 400
    assert "must be >=" in resp.json()["detail"]


def test_weather_now_endpoint(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_run_weather_now(*args, **kwargs):  # type: ignore[no-untyped-def]
        return {
            "command": "weather_now",
            "weather": {"provider": "open_meteo", "temperature_c": 22.3},
            "location": {"location_name": "Taipei"},
            "warnings": [],
        }

    monkeypatch.setattr(api_module.bridge, "run_weather_now", fake_run_weather_now)
    resp = client.post(
        "/weather-now",
        json={
            "location_payload": {"location_name": "Taipei", "latitude": 25.033, "longitude": 121.5654},
            "timezone": "Asia/Taipei",
            "locale": "en",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["command"] == "weather_now"
    assert data["weather"]["temperature_c"] == 22.3


def test_weather_at_time_endpoint(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_run_weather_at_time(*args, **kwargs):  # type: ignore[no-untyped-def]
        return {
            "command": "weather_at_time",
            "weather": {"provider": "open_meteo", "time_delta_minutes": 15},
            "warnings": [],
        }

    monkeypatch.setattr(api_module.bridge, "run_weather_at_time", fake_run_weather_at_time)
    resp = client.post(
        "/weather-at-time",
        json={
            "input_payload": {"iso_datetime": "2026-03-09T18:30:00+08:00"},
            "location_payload": {"location_name": "Taipei", "latitude": 25.033, "longitude": 121.5654},
            "timezone": "Asia/Taipei",
            "locale": "en",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["command"] == "weather_at_time"
    assert data["weather"]["time_delta_minutes"] == 15


def test_spacetime_snapshot_endpoint(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_run_spacetime_snapshot(*args, **kwargs):  # type: ignore[no-untyped-def]
        return {
            "command": "spacetime_snapshot",
            "instant": {"iso_local": "2026-03-09T18:30:00+08:00"},
            "weather_context": {"weather": {"weather_label": "partly_cloudy", "temperature_c": 21.2}},
            "world_context": {"scene_prompt": "demo"},
            "warnings": [],
        }

    monkeypatch.setattr(api_module.bridge, "run_spacetime_snapshot", fake_run_spacetime_snapshot)
    resp = client.post(
        "/spacetime-snapshot",
        json={
            "input_payload": {"iso_datetime": "2026-03-09T18:30:00+08:00"},
            "timezone": "Asia/Taipei",
            "date_basis": "local",
            "location_payload": {"location_name": "Taipei", "latitude": 25.033, "longitude": 121.5654},
            "subject_payload": {"entity_id": "lobster-001", "role": "time traveler"},
            "locale": "en",
            "include_astro": True,
            "include_metaphysics": True,
            "include_weather": True,
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["command"] == "spacetime_snapshot"
    assert data["weather_context"]["weather"]["weather_label"] == "partly_cloudy"


def test_historical_resolve_endpoint(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_run_historical_resolve(*args, **kwargs):  # type: ignore[no-untyped-def]
        return {
            "command": "historical_resolve",
            "time_anchor": {"input_mode": "julian_day"},
            "place_anchor": {"resolved_name": "Rome"},
            "warnings": [],
        }

    monkeypatch.setattr(api_module.bridge, "run_historical_resolve", fake_run_historical_resolve)
    resp = client.post(
        "/historical-resolve",
        json={
            "historical_input_payload": {"julian_day": 2461115.5},
            "timezone": "UTC",
            "location_payload": {"historical_name": "Rome"},
            "locale": "en",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["command"] == "historical_resolve"
    assert data["place_anchor"]["resolved_name"] == "Rome"


def test_historical_spacetime_snapshot_endpoint(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_run_historical_snapshot(*args, **kwargs):  # type: ignore[no-untyped-def]
        return {
            "command": "historical_spacetime_snapshot",
            "environment_context": {"environment_mode": "historical_proxy"},
            "provenance": [{"field": "time_anchor"}],
            "warnings": [],
        }

    monkeypatch.setattr(
        api_module.bridge,
        "run_historical_spacetime_snapshot",
        fake_run_historical_snapshot,
    )
    resp = client.post(
        "/historical-spacetime-snapshot",
        json={
            "historical_input_payload": {
                "source_calendar": "julian",
                "source_payload": {"year": 1400, "month": 3, "day": 10},
            },
            "timezone": "Europe/Rome",
            "location_payload": {"historical_name": "Florence"},
            "subject_payload": {"role": "scribe"},
            "targets": ["gregorian", "julian"],
            "locale": "en",
            "include_astro": False,
            "include_metaphysics": False,
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["command"] == "historical_spacetime_snapshot"
    assert data["environment_context"]["environment_mode"] == "historical_proxy"
