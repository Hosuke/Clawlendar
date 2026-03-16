# Clawlendar

[![ClawHub](https://img.shields.io/badge/ClawHub-clawlendar-blue?logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0Ij48cGF0aCBmaWxsPSJ3aGl0ZSIgZD0iTTEyIDJBMTAgMTAgMCAwIDAgMiAxMmExMCAxMCAwIDAgMCAxMCAxMCAxMCAxMCAwIDAgMCAxMC0xMEExMCAxMCAwIDAgMCAxMiAyeiIvPjwvc3ZnPg==)](https://clawhub.ai/Hosuke/clawlendar)
[![PyPI](https://img.shields.io/pypi/v/clawlendar)](https://pypi.org/project/clawlendar/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

**Timestamp-first perpetual calendar interop for AI agents.**

> Clawlendar = **Claw** (AI agent) + **Calendar**

Clawlendar helps agents speak the same time language across systems, regions, and calendar traditions.
It normalizes an instant first (Unix timestamp), then projects to multiple calendars with a stable JSON contract.

Available as an **MCP server** (for Claude Desktop / Claude Code), a **FastAPI HTTP service**, and a **CLI tool**.

## One-line Install

### Via ClawHub

```bash
clawhub install clawlendar
```

### Via pip + Claude Code

```bash
python3 -m pip install -U "clawlendar[all]" && claude mcp add clawlendar -- clawlendar
```

### Minimal install (pip only)

```bash
python3 -m pip install -U clawlendar
```

### Full local stack (HTTP + all optional providers)

```bash
python3 -m pip install -r requirements.txt
```

## Live Demo (Vercel)

- Frontend demo: https://clawlendar-web.vercel.app/

## Agent Access Pattern (Vercel + JSON API)

- Use Vercel frontend for human entry and discovery.
- Use JSON API (`/spacetime-snapshot`, `/life-context`, `/day-profile`, etc.) for agent-to-agent integration.
- Recommended: add `/api/*` proxy routes in `clawlendar-web` that forward to your Clawlendar backend.
- Guide: [`docs/vercel-agent-gateway.md`](docs/vercel-agent-gateway.md)

## GitHub Pages Showcase

This repo includes a showcase page at `docs/index.html` for GitHub Pages.

Enable it via:

1. GitHub repository **Settings** -> **Pages**
2. **Build and deployment** -> **Source** = `Deploy from a branch`
3. **Branch** = `main`, **Folder** = `/docs`
4. Save, then open: `https://hosuke.github.io/Clawlendar/`

## Install as MCP Server

### From PyPI

```bash
pip install clawlendar
```

### From source

```bash
git clone https://github.com/Hosuke/Clawlendar.git
cd Clawlendar
pip install -e .
```

### Claude Desktop configuration

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "clawlendar": {
      "command": "clawlendar"
    }
  }
}
```

Config file location:
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

### Claude Code

```bash
claude mcp add clawlendar -- clawlendar
```

## Prompt Examples

1. `Convert 2026-03-09 (Gregorian) into Minguo, Japanese era, and sexagenary.`
2. `Given timestamp 1773014400 in Asia/Taipei, return day profile with Bazi/Huangli and moon phase.`
3. `Show the true month boundary days for Chinese lunar month 2026-01 (non-leap).`
4. `Build life context from birth to now with location/weather and identity anchors.`
5. `Tell me what time it is now in Asia/Taipei and project it into East/West calendar systems.`
6. `Resolve 1400-03-10 (Julian) in Florence into a historical spacetime snapshot with provenance.`

## Documentation

- Live demo: https://clawlendar-web.vercel.app/
- Tool reference: [`docs/tool-reference.md`](docs/tool-reference.md)
- Intent recipes (CN/EN): [`docs/recipes.md`](docs/recipes.md)
- Locale and I18N notes: [`docs/i18n.md`](docs/i18n.md)
- Full JSON examples: [`docs/examples/`](docs/examples/)
- Vercel gateway design: [`docs/vercel-agent-gateway.md`](docs/vercel-agent-gateway.md)

## JSON Contract + Higher-level UX

Clawlendar keeps MCP outputs JSON-first for agent interoperability.

- Tool layer: deterministic structured JSON (`convert`, `timeline`, `day_profile`, etc.).
- Assistant layer: optional natural-language UX such as `/今日吉凶` or `today's astrology`, mapped to tool calls.

This separation keeps integrations stable while still supporting rich user-facing prompts.

## OpenClaw / Agent Usage

Recommended agent flow:

1. Call `now` to bootstrap the current instant for a visitor or newly initialized agent.
2. Call `timeline` for strict timestamp-first conversions.
3. Call `day_profile` when you need lunar/Bazi/Huangli or Western almanac context.
4. Call `spacetime_snapshot` for one-call modern context with subject/place continuity.
5. Call `historical_spacetime_snapshot` for pre-modern scenes with explicit `uncertainty` and `provenance`.

This keeps OpenClaw and other agent runtimes on a stable JSON contract while still allowing higher-level natural-language prompts.

## MCP Tools

Once connected, Claude has access to thirteen tools:

| Tool | Description |
|------|-------------|
| `now` | Return the current instant with local temporal context and calendar projections |
| `capabilities` | List all supported calendars, payload schemas, and optional provider status |
| `convert` | Convert a date from one calendar to one or more target calendars |
| `timeline` | Normalize an instant (timestamp-first) and project into multiple calendar systems |
| `astro_snapshot` | Return seven governors, four remainders, and major aspects (approximate) |
| `calendar_month` | Resolve true month boundaries and day list for non-Gregorian month mode |
| `day_profile` | One-call day details: calendar profile + optional astro + optional Eastern/Western metaphysics |
| `life_context` | Build continuity-safe world context from birth time + now + space + subject anchors, with birthday/age and optional weather enrichment |
| `weather_now` | Fetch current weather for a location (latitude/longitude), with temporal context |
| `weather_at_time` | Fetch nearest-hour weather for a requested instant and location |
| `spacetime_snapshot` | One-call agent context: timeline + day profile + optional weather + scene prompt |
| `historical_resolve` | Resolve historical input (`julian_day` / `proleptic_gregorian` / source calendar payload) into Gregorian bridge fields |
| `historical_spacetime_snapshot` | Historical one-call context with provenance, confidence, and environment reconstruction tiers |

## Historical Spacetime MVP

Clawlendar now includes a historical bridge layer for ancient and pre-modern queries.

- Supported input modes:
  - `julian_day`
  - `proleptic_gregorian`
  - `source_calendar + source_payload` (for example `julian`)
- Current bridge range: `CE 1..9999`
- Historical date-only inputs default to assumed local noon unless clock time is provided.
- Pre-modern environment output is returned as `climatology` or `historical_proxy`, not claimed as exact observed weather.
- Every historical snapshot includes `uncertainty` and `provenance`.

## Supported Calendars

- `gregorian`
- `julian`
- `iso_week`
- `unix_epoch`
- `minguo`
- `buddhist`
- `japanese_era`
- `sexagenary` (approximate)
- `solar_term_24` (approximate)

### Optional (install extras)

```bash
pip install clawlendar[all]       # all optional calendars
pip install clawlendar[lunar]     # Chinese lunar only
pip install clawlendar[extra-calendars]  # Islamic, Hebrew, Persian
pip install clawlendar[metaphysics]  # Bazi + Huangli provider (lunar_python)
```

- `chinese_lunar` — via `lunardate`
- `islamic` / `hebrew` / `persian` — via `convertdate`
- `bazi` / `huangli` (day profile metaphysics block) — via optional `lunar_python`, fallback to internal approximation
- Chinese lunar textual labels (e.g., `初一`, `十五`) are returned in `day_profile.metaphysics.eastern.lunar_date.month_name/day_name` when `lunar_python` is installed.

## CLI Usage

```bash
pip install -e .

# Current time bootstrap
python3 scripts/calendar_bridge.py now \
  --timezone 'Asia/Taipei' \
  --targets minguo,sexagenary,solar_term_24 \
  --locale zh-CN

# List calendars
python3 scripts/calendar_bridge.py capabilities

# Convert a date
python3 scripts/calendar_bridge.py convert \
  --source gregorian \
  --targets julian,iso_week,minguo,buddhist,japanese_era,sexagenary,solar_term_24 \
  --date-json '{"year": 2026, "month": 3, "day": 9}' \
  --locale zh-TW

# Timeline projection
python3 scripts/calendar_bridge.py timeline \
  --input-json '{"timestamp": 1773014400}' \
  --timezone 'Asia/Taipei' \
  --date-basis local \
  --targets minguo,japanese_era,sexagenary,solar_term_24 \
  --locale zh-CN

# Weather now for current location
python3 scripts/calendar_bridge.py weather-now \
  --location-json '{"location_name":"Taipei","latitude":25.033,"longitude":121.5654}' \
  --timezone 'Asia/Taipei'

# Weather at historical/future instant
python3 scripts/calendar_bridge.py weather-at-time \
  --input-json '{"iso_datetime":"2026-03-09T18:30:00+08:00"}' \
  --location-json '{"location_name":"Taipei","latitude":25.033,"longitude":121.5654}' \
  --timezone 'Asia/Taipei'

# One-call spacetime snapshot for agent context
python3 scripts/calendar_bridge.py spacetime-snapshot \
  --input-json '{"iso_datetime":"2026-03-09T18:30:00+08:00"}' \
  --timezone 'Asia/Taipei' \
  --location-json '{"location_name":"Taipei","latitude":25.033,"longitude":121.5654,"background":"neon city night"}' \
  --subject-json '{"entity_id":"lobster-001","role":"time traveler","soul":"continuity-first"}' \
  --locale en

# Historical resolve
python3 scripts/calendar_bridge.py historical-resolve \
  --historical-input-json '{"source_calendar":"julian","source_payload":{"year":1400,"month":3,"day":10}}' \
  --timezone 'Europe/Rome' \
  --location-json '{"historical_name":"Florence","present_day_reference":"Firenze"}'

# Historical spacetime snapshot
python3 scripts/calendar_bridge.py historical-spacetime-snapshot \
  --historical-input-json '{"source_calendar":"julian","source_payload":{"year":1400,"month":3,"day":10}}' \
  --timezone 'Europe/Rome' \
  --location-json '{"historical_name":"Florence","present_day_reference":"Firenze","historical_admin":{"polity":"Republic of Florence"},"latitude":43.7696,"longitude":11.2558}' \
  --subject-json '{"role":"scribe"}' \
  --targets gregorian,julian,sexagenary \
  --locale en \
  --no-astro \
  --no-metaphysics

# Astro snapshot (seven governors + four remainders)
python3 scripts/calendar_bridge.py astro \
  --input-json '{"timestamp": 1773014400}' \
  --timezone 'Asia/Taipei'

# Day profile (calendar details + optional astro + optional metaphysics)
python3 scripts/calendar_bridge.py day-profile \
  --input-json '{"timestamp": 1773014400}' \
  --timezone 'Asia/Taipei' \
  --locale zh-TW

# True month boundary mode (example: Minguo 115/03)
python3 scripts/calendar_bridge.py calendar-month \
  --source minguo \
  --month-json '{"year":115,"month":3}'

# Life context (birth -> now continuity context)
python3 scripts/calendar_bridge.py life-context \
  --birth-input-json '{"iso_datetime":"2026-03-01T09:00:00+08:00"}' \
  --now-input-json '{"iso_datetime":"2026-03-09T18:30:00+08:00"}' \
  --timezone 'Asia/Taipei' \
  --space-json '{"location_name":"南京·秦淮河","latitude":32.0366,"longitude":118.7895,"background":"春季夜游","climate":"humid subtropical","scenery_note":"夜色与河道灯影","environment_tags":["city","river"]}' \
  --subject-json '{"entity_id":"lobster-001","role":"18岁女儿","soul":"温柔且主动问候"}' \
  --locale zh-CN
```

## Sample Response (Life Context)

Run:

```bash
python3 scripts/calendar_bridge.py life-context \
  --birth-input-json '{"iso_datetime":"2026-03-01T09:00:00+08:00"}' \
  --now-input-json '{"iso_datetime":"2026-03-09T18:30:00+08:00"}' \
  --timezone 'Asia/Taipei' \
  --space-json '{"location_name":"南京·秦淮河","latitude":32.0366,"longitude":118.7895}' \
  --subject-json '{"entity_id":"lobster-001","role":"18岁女儿"}' \
  --locale zh-CN
```

Returned fields (excerpt):

```json
{
  "command": "life_context",
  "life": {
    "life_id": "lobster-001",
    "age": {"readable": "8d 9h 30m", "stage": "juvenile"},
    "birthday": {"month": 3, "day": 1, "days_until_next_birthday": 357}
  },
  "temporal_context": {
    "local_date": "2026-03-09",
    "weekday_name_en": "Monday",
    "season_meteorological": "spring"
  },
  "environment": {
    "place": {"location_name": "南京·秦淮河"},
    "weather": {
      "provider": "open_meteo",
      "data_mode": "archive_reanalysis|forecast_projection",
      "requested_time_local": "2026-03-09T18:30:00+08:00",
      "time_delta_minutes": "<nearest-hour offset>",
      "weather_label": "<dynamic>"
    }
  },
  "world_context": {
    "scene_prompt": "..."
  }
}
```

## Sample Response (Huangli / 吉凶)

Run:

```bash
python3 scripts/calendar_bridge.py day-profile \
  --input-json '{"timestamp": 1773014400}' \
  --timezone 'Asia/Taipei' \
  --locale zh-CN
```

Returned fields (excerpt):

```json
{
  "command": "day_profile",
  "locale": "zh-Hans",
  "bridge_date_gregorian": { "year": 2026, "month": 3, "day": 9 },
  "metaphysics": {
    "eastern": {
      "provider": "lunar_python",
      "lunar_date": { "month_name": "正", "day_name": "廿一" },
      "huangli": {
        "yi": ["祭祀", "嫁娶", "纳婿", "安葬"],
        "ji": ["栽种", "盖屋", "作灶", "入宅"],
        "clash": "(丙子)鼠",
        "sha_direction": "北"
      }
    }
  }
}
```

This confirms `day_profile` can directly return almanac-style good/bad actions (`yi`/`ji`) plus clash/sha details.

## Sample Response (Spacetime Snapshot)

Run:

```bash
python3 scripts/calendar_bridge.py spacetime-snapshot \
  --input-json '{"iso_datetime":"2026-03-09T18:30:00+08:00"}' \
  --timezone 'Asia/Taipei' \
  --location-json '{"location_name":"Taipei","latitude":25.033,"longitude":121.5654}' \
  --subject-json '{"entity_id":"lobster-001","role":"time traveler"}'
```

Returned fields (excerpt):

```json
{
  "command": "spacetime_snapshot",
  "instant": {"iso_local": "2026-03-09T18:30:00+08:00"},
  "timeline": {"calendar_projection": {"results": {"chinese_lunar": {"payload": {}}}}},
  "day_profile": {"metaphysics": {"western": {"moon_phase": {"label": "waxing_gibbous"}}}},
  "weather_context": {"weather": {"weather_label": "partly_cloudy", "temperature_c": 21.2}},
  "world_context": {"scene_prompt": "..."}
}
```

## HTTP API (FastAPI)

```bash
pip install -e ".[api]"
./scripts/run_api.sh
```

Endpoints: `GET /health` · `GET /capabilities` · `GET /now` · `POST /now` · `POST /convert` · `POST /timeline` · `POST /astro` · `POST /day-profile` · `POST /calendar-month` · `POST /life-context` · `POST /weather-now` · `POST /weather-at-time` · `POST /spacetime-snapshot` · `POST /historical-resolve` · `POST /historical-spacetime-snapshot`

```bash
# Smoke test
./scripts/curl_examples.sh

# Lightweight current-time bootstrap
curl -sS 'http://127.0.0.1:8000/now?timezone=Asia/Taipei&locale=zh-CN' | python3 -m json.tool

# Convert a date
curl -sS -X POST http://127.0.0.1:8000/convert \
  -H "Content-Type: application/json" \
  -d '{
    "source": "gregorian",
    "targets": ["julian", "iso_week", "minguo"],
    "source_payload": {"year": 2026, "month": 3, "day": 9},
    "locale": "zh-CN"
  }' | python3 -m json.tool
```

## Docker

```bash
docker build -t clawlendar:mvp .
docker run --rm -p 8000:8000 clawlendar:mvp
```

## Architecture

1. Parse input as an instant (`timestamp`, `timestamp_ms`, `iso_datetime`, or `local_datetime` + timezone).
2. Normalize to UTC.
3. Choose projection date basis (`local` or `utc`).
4. Convert from canonical Gregorian bridge date to target calendars.
5. Return structured JSON plus warnings for optional/approximate providers.

## Repository Structure

```
src/clawlendar/
  __init__.py            # package version
  bridge.py              # core calendar conversion engine
  server.py              # MCP server entry point
scripts/
  calendar_bridge.py     # CLI wrapper
  api_server.py          # FastAPI service layer
  run_api.sh             # API launch helper
  curl_examples.sh       # HTTP smoke examples
references/
  integration-contract.md
  time-wheel-model.md
  calendar-landscape.md
  mvp-release-notes.md
```

## Known Limitations (MVP)

- `sexagenary` year boundary is approximate.
- `solar_term_24` is fixed-date approximation, not ephemeris-accurate astronomy.
- Western chart values are lightweight analytical model (not ephemeris-grade precision).
- When `lunar_python` is unavailable, Bazi/Huangli uses internal approximation fallback.
- `sexagenary` and `solar_term_24` keep stable machine keys and add localized display fields via `locale` (`zh-CN`, `zh-TW`, etc.).
- Some calendars are available only when optional dependencies are installed.
- `life_context` weather enrichment is best effort (network/provider dependent) and should be treated as contextual reference, not a certified meteorological record.
- Weather is now time-anchored to `now_input_payload` (nearest-hour Open-Meteo point). Past instants use archive data; future/current instants use forecast/current data.

## Privacy Policy

Clawlendar is a local/self-hosted tool by default. It does not include built-in telemetry or remote data collection in core runtime.

- Local MCP mode: data is processed on user machine.
- Optional HTTP deployment: data handling depends on your own server setup and logs.

If you deploy Clawlendar as a remote service, you are responsible for publishing your own privacy policy for that deployment endpoint.

## Support

- ClawHub: https://clawhub.ai/Hosuke/clawlendar
- GitHub Issues: https://github.com/Hosuke/Clawlendar/issues
- Repository: https://github.com/Hosuke/Clawlendar

## Roadmap

- Astronomical solar-term provider.
- Higher-precision Chinese lunar provider with regression fixtures.
- Publish to PyPI and MCP server directory.

---

## 中文说明

Clawlendar 是一个给 AI agents 用的「时间与历法互通层」，同时也是一个 **MCP Server**（可直接接入 Claude Desktop / Claude Code）。

核心做法是先用时间戳统一「绝对时间」，再投影到不同时区与历法，输出稳定 JSON，方便多工具接入。

在线演示（Vercel）：
- https://clawlendar-web.vercel.app/

### 安装

```bash
clawhub install clawlendar
# 或
pip install clawlendar
```

在 Claude Desktop 的 `claude_desktop_config.json` 中加入：

```json
{
  "mcpServers": {
    "clawlendar": {
      "command": "clawlendar"
    }
  }
}
```

### 支持的历法

- 公历、儒略历、ISO 周、Unix 纪元
- 民国纪年、佛历、日本年号
- 干支（近似）、二十四节气（近似）
- 干支/节气支持本地化显示（可传 `locale=zh-CN` 或 `locale=zh-TW`，同时保留机器可读 key）
- `day_profile` 支持输出：八字、老黄历（宜忌/彭祖/冲煞）、西方日课（月相/行星状态/星座）
- `life_context` 支持输出：生命起始时间、当前时间、已存活时长、生日与下次生日倒计时、地点锚点、个体角色/性格锚点、可选天气增强（按 `now_input_payload` 时刻锚定，返回最近小时匹配偏差）
- 可选：农历（`lunardate`）、伊斯兰历、希伯来历、波斯历（`convertdate`）
