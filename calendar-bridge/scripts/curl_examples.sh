#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://127.0.0.1:8000}"

echo "[1/4] GET /health"
curl -sS "${BASE_URL}/health" | python3 -m json.tool
echo

echo "[2/4] GET /capabilities"
curl -sS "${BASE_URL}/capabilities" | python3 -m json.tool
echo

echo "[3/4] POST /convert"
curl -sS -X POST "${BASE_URL}/convert" \
  -H "Content-Type: application/json" \
  -d '{
    "source": "gregorian",
    "targets": ["julian", "iso_week", "minguo"],
    "source_payload": {"year": 2026, "month": 3, "day": 9}
  }' | python3 -m json.tool
echo

echo "[4/4] POST /timeline"
curl -sS -X POST "${BASE_URL}/timeline" \
  -H "Content-Type: application/json" \
  -d '{
    "input_payload": {"timestamp": 1773014400},
    "timezone": "Asia/Taipei",
    "date_basis": "local",
    "targets": ["minguo", "japanese_era", "sexagenary", "solar_term_24"]
  }' | python3 -m json.tool
