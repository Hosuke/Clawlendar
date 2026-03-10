# Clawlendar

**Timestamp-first perpetual calendar interop for AI agents.**

> Clawlendar = **Claw** (AI agent) + **Calendar**

Clawlendar helps agents speak the same time language across systems, regions, and calendar traditions.
It normalizes an instant first (Unix timestamp), then projects to multiple calendars with a stable JSON contract.

Available as an **MCP server** (for Claude Desktop / Claude Code), a **FastAPI HTTP service**, and a **CLI tool**.

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

## MCP Tools

Once connected, Claude has access to six tools:

| Tool | Description |
|------|-------------|
| `capabilities` | List all supported calendars, payload schemas, and optional provider status |
| `convert` | Convert a date from one calendar to one or more target calendars |
| `timeline` | Normalize an instant (timestamp-first) and project into multiple calendar systems |
| `astro_snapshot` | Return seven governors, four remainders, and major aspects (approximate) |
| `calendar_month` | Resolve true month boundaries and day list for non-Gregorian month mode |
| `day_profile` | One-call day details: calendar profile + solar term + sexagenary + optional astro |

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
```

- `chinese_lunar` — via `lunardate`
- `islamic` / `hebrew` / `persian` — via `convertdate`

## CLI Usage

```bash
pip install -e .

# List calendars
python3 scripts/calendar_bridge.py capabilities

# Convert a date
python3 scripts/calendar_bridge.py convert \
  --source gregorian \
  --targets julian,iso_week,minguo,buddhist,japanese_era,sexagenary,solar_term_24 \
  --date-json '{"year": 2026, "month": 3, "day": 9}'

# Timeline projection
python3 scripts/calendar_bridge.py timeline \
  --input-json '{"timestamp": 1773014400}' \
  --timezone 'Asia/Taipei' \
  --date-basis local \
  --targets minguo,japanese_era,sexagenary,solar_term_24

# Astro snapshot (seven governors + four remainders)
python3 scripts/calendar_bridge.py astro \
  --input-json '{"timestamp": 1773014400}' \
  --timezone 'Asia/Taipei'

# Day profile (calendar details + optional astro)
python3 scripts/calendar_bridge.py day-profile \
  --input-json '{"timestamp": 1773014400}' \
  --timezone 'Asia/Taipei'

# True month boundary mode (example: Minguo 115/03)
python3 scripts/calendar_bridge.py calendar-month \
  --source minguo \
  --month-json '{"year":115,"month":3}'
```

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
    "source_payload": {"year": 2026, "month": 3, "day": 9}
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
- Some calendars are available only when optional dependencies are installed.

## Roadmap

- Astronomical solar-term provider.
- Higher-precision Chinese lunar provider with regression fixtures.
- Publish to PyPI and MCP server directory.

---

## 中文说明

Clawlendar 是一个给 AI agents 用的「时间与历法互通层」，同时也是一个 **MCP Server**（可直接接入 Claude Desktop / Claude Code）。

核心做法是先用时间戳统一「绝对时间」，再投影到不同时区与历法，输出稳定 JSON，方便多工具接入。

### 安装

```bash
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
- 可选：农历（`lunardate`）、伊斯兰历、希伯来历、波斯历（`convertdate`）
