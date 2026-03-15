from pathlib import Path
import sys

import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

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
