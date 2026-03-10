#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://127.0.0.1:8000}"

echo "[1/7] GET /health"
curl -sS "${BASE_URL}/health" | python3 -m json.tool
echo

echo "[2/7] GET /capabilities"
curl -sS "${BASE_URL}/capabilities" | python3 -m json.tool
echo

echo "[3/7] POST /convert"
curl -sS -X POST "${BASE_URL}/convert" \
  -H "Content-Type: application/json" \
  -d '{
    "source": "gregorian",
    "targets": ["julian", "iso_week", "minguo"],
    "source_payload": {"year": 2026, "month": 3, "day": 9}
  }' | python3 -m json.tool
echo

echo "[4/7] POST /timeline"
curl -sS -X POST "${BASE_URL}/timeline" \
  -H "Content-Type: application/json" \
  -d '{
    "input_payload": {"timestamp": 1773014400},
    "timezone": "Asia/Taipei",
    "date_basis": "local",
    "targets": ["minguo", "japanese_era", "sexagenary", "solar_term_24"]
  }' | python3 -m json.tool
echo

echo "[5/7] POST /astro"
curl -sS -X POST "${BASE_URL}/astro" \
  -H "Content-Type: application/json" \
  -d '{
    "input_payload": {"timestamp": 1773014400},
    "timezone": "Asia/Taipei",
    "zodiac_system": "tropical"
  }' | python3 -m json.tool
echo

echo "[6/7] POST /day-profile"
curl -sS -X POST "${BASE_URL}/day-profile" \
  -H "Content-Type: application/json" \
  -d '{
    "input_payload": {"timestamp": 1773014400},
    "timezone": "Asia/Taipei",
    "date_basis": "local",
    "include_astro": true
  }' | python3 -m json.tool
echo

echo "[7/7] POST /calendar-month (minguo example)"
curl -sS -X POST "${BASE_URL}/calendar-month" \
  -H "Content-Type: application/json" \
  -d '{
    "source": "minguo",
    "month_payload": {"year": 115, "month": 3}
  }' | python3 -m json.tool
