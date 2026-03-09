#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

cd "${SKILL_ROOT}"
exec uvicorn scripts.api_server:app --host 0.0.0.0 --port "${PORT:-8000}"
