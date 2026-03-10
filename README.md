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

## Documentation

- Live demo: https://clawlendar-web.vercel.app/
- Tool reference: [`docs/tool-reference.md`](docs/tool-reference.md)
- Intent recipes (CN/EN): [`docs/recipes.md`](docs/recipes.md)
- Locale and I18N notes: [`docs/i18n.md`](docs/i18n.md)
- Full JSON examples: [`docs/examples/`](docs/examples/)

## JSON Contract + Higher-level UX

Clawlendar keeps MCP outputs JSON-first for agent interoperability.

- Tool layer: deterministic structured JSON (`convert`, `timeline`, `day_profile`, etc.).
- Assistant layer: optional natural-language UX such as `/今日吉凶` or `today's astrology`, mapped to tool calls.

This separation keeps integrations stable while still supporting rich user-facing prompts.

## MCP Tools

Once connected, Claude has access to six tools:

| Tool | Description |
|------|-------------|
| `capabilities` | List all supported calendars, payload schemas, and optional provider status |
| `convert` | Convert a date from one calendar to one or more target calendars |
| `timeline` | Normalize an instant (timestamp-first) and project into multiple calendar systems |
| `astro_snapshot` | Return seven governors, four remainders, and major aspects (approximate) |
| `calendar_month` | Resolve true month boundaries and day list for non-Gregorian month mode |
| `day_profile` | One-call day details: calendar profile + optional astro + optional Eastern/Western metaphysics |

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

## HTTP API (FastAPI)

```bash
pip install -e ".[api]"
./scripts/run_api.sh
```

Endpoints: `GET /health` · `GET /capabilities` · `POST /convert` · `POST /timeline` · `POST /astro` · `POST /day-profile` · `POST /calendar-month`

```bash
# Smoke test
./scripts/curl_examples.sh

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
- 可选：农历（`lunardate`）、伊斯兰历、希伯来历、波斯历（`convertdate`）
