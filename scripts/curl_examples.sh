#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://127.0.0.1:8000}"

echo "[1/11] GET /health"
curl -sS "${BASE_URL}/health" | python3 -m json.tool
echo

echo "[2/11] GET /capabilities"
curl -sS "${BASE_URL}/capabilities" | python3 -m json.tool
echo

echo "[3/11] POST /convert"
curl -sS -X POST "${BASE_URL}/convert" \
  -H "Content-Type: application/json" \
  -d '{
    "source": "gregorian",
    "targets": ["julian", "iso_week", "minguo"],
    "source_payload": {"year": 2026, "month": 3, "day": 9},
    "locale": "zh-CN"
  }' | python3 -m json.tool
echo

echo "[4/11] POST /timeline"
curl -sS -X POST "${BASE_URL}/timeline" \
  -H "Content-Type: application/json" \
  -d '{
    "input_payload": {"timestamp": 1773014400},
    "timezone": "Asia/Taipei",
    "date_basis": "local",
    "targets": ["minguo", "japanese_era", "sexagenary", "solar_term_24"],
    "locale": "zh-TW"
  }' | python3 -m json.tool
echo

echo "[5/11] POST /astro"
curl -sS -X POST "${BASE_URL}/astro" \
  -H "Content-Type: application/json" \
  -d '{
    "input_payload": {"timestamp": 1773014400},
    "timezone": "Asia/Taipei",
    "zodiac_system": "tropical"
  }' | python3 -m json.tool
echo

echo "[6/11] POST /day-profile"
curl -sS -X POST "${BASE_URL}/day-profile" \
  -H "Content-Type: application/json" \
  -d '{
    "input_payload": {"timestamp": 1773014400},
    "timezone": "Asia/Taipei",
    "date_basis": "local",
    "include_astro": true,
    "include_metaphysics": true,
    "locale": "zh-CN"
  }' | python3 -m json.tool
echo

echo "[7/11] POST /calendar-month (minguo example)"
curl -sS -X POST "${BASE_URL}/calendar-month" \
  -H "Content-Type: application/json" \
  -d '{
    "source": "minguo",
    "month_payload": {"year": 115, "month": 3}
  }' | python3 -m json.tool
echo

echo "[8/11] POST /life-context"
curl -sS -X POST "${BASE_URL}/life-context" \
  -H "Content-Type: application/json" \
  -d '{
    "birth_input_payload": {"iso_datetime": "2026-03-01T09:00:00+08:00"},
    "now_input_payload": {"iso_datetime": "2026-03-09T18:30:00+08:00"},
    "timezone": "Asia/Taipei",
    "space_payload": {
      "location_name": "南京·秦淮河",
      "latitude": 32.0366,
      "longitude": 118.7895,
      "background": "春季夜游",
      "climate": "humid subtropical",
      "scenery_note": "夜色与河道灯影"
    },
    "subject_payload": {
      "entity_id": "lobster-001",
      "role": "18岁女儿",
      "soul": "温柔且主动问候"
    },
    "locale": "zh-CN",
    "auto_weather": true
  }' | python3 -m json.tool
echo

echo "[9/11] POST /weather-now"
curl -sS -X POST "${BASE_URL}/weather-now" \
  -H "Content-Type: application/json" \
  -d '{
    "location_payload": {
      "location_name": "Taipei",
      "latitude": 25.033,
      "longitude": 121.5654
    },
    "timezone": "Asia/Taipei",
    "locale": "en"
  }' | python3 -m json.tool
echo

echo "[10/11] POST /weather-at-time"
curl -sS -X POST "${BASE_URL}/weather-at-time" \
  -H "Content-Type: application/json" \
  -d '{
    "input_payload": {"iso_datetime": "2026-03-09T18:30:00+08:00"},
    "location_payload": {
      "location_name": "Taipei",
      "latitude": 25.033,
      "longitude": 121.5654
    },
    "timezone": "Asia/Taipei",
    "locale": "en"
  }' | python3 -m json.tool
echo

echo "[11/11] POST /spacetime-snapshot"
curl -sS -X POST "${BASE_URL}/spacetime-snapshot" \
  -H "Content-Type: application/json" \
  -d '{
    "input_payload": {"iso_datetime": "2026-03-09T18:30:00+08:00"},
    "timezone": "Asia/Taipei",
    "date_basis": "local",
    "location_payload": {
      "location_name": "Taipei",
      "latitude": 25.033,
      "longitude": 121.5654,
      "background": "neon city night"
    },
    "subject_payload": {
      "entity_id": "lobster-001",
      "role": "time traveler",
      "soul": "continuity-first"
    },
    "locale": "en",
    "include_astro": true,
    "include_metaphysics": true,
    "include_weather": true
  }' | python3 -m json.tool
