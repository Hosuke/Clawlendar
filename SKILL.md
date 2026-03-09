---
name: calendar-bridge
description: Cross-calendar conversion and interoperability skill for Gregorian, Julian, ISO week, ROC (Minguo), Buddhist Era, Japanese era, and optional Chinese lunar/Islamic/Hebrew/Persian calendars. Use when Codex needs to normalize dates across systems, answer calendar questions (including East Asian context like lunisolar and solar terms), or provide a stable JSON contract that many agents/tools can integrate.
---

# Calendar Bridge

## Overview

Provide a single, agent-friendly bridge layer so different tools can ask calendar questions in a common schema and receive normalized JSON. Treat this skill as the date interoperability baseline for multi-agent ecosystems.

## Workflow

1. Discover capabilities first.
2. Parse source date payload in the declared source calendar.
3. Convert source to canonical Gregorian date.
4. Project canonical date into each target calendar.
5. Return JSON with conversion results, warnings, and unconvertible targets.

## Quick Start

List supported calendars and optional backends:

```bash
python3 scripts/calendar_bridge.py capabilities
```

Convert one date into multiple targets:

```bash
python3 scripts/calendar_bridge.py convert \
  --source gregorian \
  --targets julian,iso_week,minguo,buddhist,japanese_era,sexagenary,solar_term_24 \
  --date-json '{"year": 2026, "month": 3, "day": 9}'
```

Convert from Chinese lunar (when `lunardate` is available):

```bash
python3 scripts/calendar_bridge.py convert \
  --source chinese_lunar \
  --targets gregorian,iso_week \
  --date-json '{"lunar_year": 2026, "lunar_month": 1, "lunar_day": 1, "is_leap_month": false}'
```

Normalize one instant with timestamp-first model (external time wheel):

```bash
python3 scripts/calendar_bridge.py timeline \
  --input-json '{"timestamp": 1773014400}' \
  --timezone 'Asia/Taipei' \
  --date-basis local \
  --targets minguo,japanese_era,sexagenary,solar_term_24
```

Run HTTP API for multi-claw integration:

```bash
pip install -r requirements.txt
./scripts/run_api.sh
```

Smoke test the HTTP API with curl:

```bash
./scripts/curl_examples.sh
```

Run with Docker:

```bash
docker build -t calendar-bridge:mvp .
docker run --rm -p 8000:8000 calendar-bridge:mvp
```

## Contract

Use the JSON contract in `references/integration-contract.md` for tool-to-tool integration. Keep payload keys calendar-specific and avoid ambiguous fields.

## References

- Use `references/integration-contract.md` for request/response schema and compatibility guidance.
- Use `references/calendar-landscape.md` for East/West major calendar systems and rollout priorities.
- Use `references/time-wheel-model.md` for timestamp-first design and instant/date projection rules.
- Use `references/mvp-release-notes.md` as GitHub release draft baseline.

## Notes

- Treat Gregorian as the canonical bridge format.
- Return warnings instead of hard-failing for optional providers that are not installed.
- Mark approximate outputs explicitly (for example, sexagenary year boundaries and fixed-date solar-term approximation).
- Treat `timeline` as the default bridge for multi-agent scheduling and event processing.
