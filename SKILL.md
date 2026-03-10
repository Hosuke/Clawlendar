---
name: clawlendar
description: Timestamp-first perpetual calendar interop for AI agents. Cross-calendar conversion for Gregorian, Julian, ISO week, ROC (Minguo), Buddhist Era, Japanese era, sexagenary, solar terms, and optional Chinese lunar/Islamic/Hebrew/Persian calendars, plus approximate celestial snapshot output for seven governors and four remainders. Use when agents need to normalize dates across systems, answer calendar questions (including East Asian context), or provide a stable JSON contract for multi-tool integration.
---

# Clawlendar

## Overview

Provide a single, agent-friendly bridge layer so different tools can ask calendar questions in a common schema and receive normalized JSON. Treat this skill as the date interoperability baseline for multi-agent ecosystems.

## Workflow

1. Discover capabilities first.
2. Parse source date payload in the declared source calendar.
3. Convert source to canonical Gregorian date.
4. Project canonical date into each target calendar.
5. Return JSON with conversion results, warnings, and unconvertible targets.
6. Use `calendar-month` when UI needs real month boundaries in non-Gregorian systems.
7. Use `day-profile` for one-call daily detail payloads (solar term, sexagenary, lunar, optional astro).

## Quick Start (MCP Server)

Install and run as an MCP server for Claude Desktop / Claude Code:

```bash
pip install clawlendar
clawlendar
```

Or run directly from source:

```bash
pip install -e .
python -m clawlendar.server
```

## CLI Usage

List supported calendars and optional backends:

```bash
pip install -e .
python3 scripts/calendar_bridge.py capabilities
```

Convert one date into multiple targets:

```bash
python3 scripts/calendar_bridge.py convert \
  --source gregorian \
  --targets julian,iso_week,minguo,buddhist,japanese_era,sexagenary,solar_term_24 \
  --date-json '{"year": 2026, "month": 3, "day": 9}'
```

Normalize one instant with timestamp-first model (external time wheel):

```bash
python3 scripts/calendar_bridge.py timeline \
  --input-json '{"timestamp": 1773014400}' \
  --timezone 'Asia/Taipei' \
  --date-basis local \
  --targets minguo,japanese_era,sexagenary,solar_term_24
```

Generate an astro snapshot for zodiac wheel rendering:

```bash
python3 scripts/calendar_bridge.py astro \
  --input-json '{"timestamp": 1773014400}' \
  --timezone 'Asia/Taipei'
```

Get true month boundaries for non-Gregorian month mode:

```bash
python3 scripts/calendar_bridge.py calendar-month \
  --source minguo \
  --month-json '{"year":115,"month":3}'
```

Get unified daily profile payload:

```bash
python3 scripts/calendar_bridge.py day-profile \
  --input-json '{"timestamp": 1773014400}' \
  --timezone 'Asia/Taipei'
```

## HTTP API

Run HTTP API for multi-claw integration:

```bash
pip install -e ".[api]"
./scripts/run_api.sh
```

Run with Docker:

```bash
docker build -t clawlendar:mvp .
docker run --rm -p 8000:8000 clawlendar:mvp
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
