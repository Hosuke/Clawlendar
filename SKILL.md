---
name: clawlendar
version: 0.4.0
description: Timestamp-first perpetual calendar interop for AI agents. Use when agents need cross-calendar conversion (Gregorian/Julian/ISO/ROC/Buddhist/Japanese era/sexagenary/solar terms plus optional lunar-Islamic-Hebrew-Persian), timeline normalization from timestamps, true month boundaries, day-level Bazi-Huangli-Western almanac payloads, and life-context modeling (birth-now age/birthday/place/weather/identity anchors).
author: Huang Geyang
metadata:
  openclaw:
    homepage: https://github.com/Hosuke/Clawlender
    requires:
      bins:
        - python3
        - pip
---

# Clawlendar

## Overview

Provide a single, agent-friendly bridge layer so different tools can ask calendar questions in a common schema and receive normalized JSON. Treat this skill as the date interoperability baseline for multi-agent ecosystems.

## Workflow

1. Call `capabilities` first to discover supported calendars, optional providers, and locale support.
2. For calendar conversion, parse source payload in declared calendar and bridge through Gregorian.
3. For instant-based workflows, use `timeline` (timestamp-first) instead of direct date conversion.
4. Use `calendar_month` when UI needs true month boundaries in non-Gregorian systems.
5. Use `day_profile` for one-call details (`sexagenary`, `solar_term_24`, `chinese_lunar`, optional `astro`, optional metaphysics).
6. Always pass `locale` (`en`, `zh-CN`, `zh-TW`) when user-facing text is required.
7. Use `life_context` when agents need birth->now continuity context with subject and location anchors.

## Quick Start (MCP Server)

Install and run as an MCP server for Claude Desktop / Claude Code:

```bash
python3 -m pip install -U "clawlendar[all]"
clawlendar
```

One-line registration in Claude Code:

```bash
python3 -m pip install -U "clawlendar[all]" && claude mcp add clawlendar -- clawlendar
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
  --timezone 'Asia/Taipei' \
  --locale 'zh-TW'
```

Include full metaphysics block (Bazi/Huangli + Western almanac):

```bash
python3 scripts/calendar_bridge.py day-profile \
  --input-json '{"timestamp": 1773014400}' \
  --timezone 'Asia/Taipei' \
  --locale 'zh-CN'
```

Build life context with birthday/age/place/weather anchors:

```bash
python3 scripts/calendar_bridge.py life-context \
  --birth-input-json '{"iso_datetime":"2026-03-01T09:00:00+08:00"}' \
  --now-input-json '{"iso_datetime":"2026-03-09T18:30:00+08:00"}' \
  --timezone 'Asia/Taipei' \
  --space-json '{"location_name":"南京·秦淮河","latitude":32.0366,"longitude":118.7895,"climate":"humid subtropical"}' \
  --subject-json '{"entity_id":"lobster-001","role":"18岁女儿","soul":"温柔且主动问候"}' \
  --locale 'zh-CN'
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

## Tool Mapping

- MCP tools: `capabilities`, `convert`, `timeline`, `astro_snapshot`, `calendar_month`, `day_profile`, `life_context`
- CLI commands: `capabilities`, `convert`, `timeline`, `astro`, `calendar-month`, `day-profile`, `life-context`
- FastAPI endpoints: `GET /capabilities`, `POST /convert`, `POST /timeline`, `POST /astro`, `POST /calendar-month`, `POST /day-profile`, `POST /life-context`

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
- `chinese_lunar` conversion payload is numeric; Chinese textual month/day labels are exposed via `day_profile.metaphysics.eastern.lunar_date` when `lunar_python` is available.
