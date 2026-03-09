# Calendar Bridge

**A timestamp-first, professional perpetual-calendar interoperability service for AI agents.**

Calendar Bridge helps agents speak the same time language across systems, regions, and calendar traditions.
It normalizes an instant first (Unix timestamp), then projects to multiple calendars with a stable JSON contract.

## Project Description (GitHub short description)

Use this as your repository description:

`Timestamp-first perpetual calendar API for AI agents across East/West calendar systems.`

Alternative options:

- `Professional perpetual-calendar interoperability for multi-agent systems.`
- `A unified calendar intelligence API for AI agents and scheduling workflows.`

## Why Calendar Bridge

- Keep one canonical time model (`timestamp`) across all agents.
- Convert and project dates into multiple calendar systems.
- Return predictable JSON for tool-to-tool integration.
- Support East Asian workflows (Minguo, Japanese era, sexagenary, solar terms).

## MVP Features

- `GET /health`
- `GET /capabilities`
- `POST /convert`
- `POST /timeline` (timestamp-first external time wheel model)
- CLI tools for local usage and scripting
- Optional providers: `chinese_lunar` via `lunardate`; `islamic`/`hebrew`/`persian` via `convertdate`

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

## Quick Start

```bash
git clone git@github.com:Hosuke/Clawlender.git
cd Clawlender
pip install -r requirements.txt
./scripts/run_api.sh
```

In another terminal:

```bash
./scripts/curl_examples.sh
```

## Docker

```bash
docker build -t calendar-bridge:mvp .
docker run --rm -p 8000:8000 calendar-bridge:mvp
```

## API Examples

### 1) Capabilities

```bash
curl -sS http://127.0.0.1:8000/capabilities | python3 -m json.tool
```

### 2) Convert a date

```bash
curl -sS -X POST http://127.0.0.1:8000/convert \
  -H "Content-Type: application/json" \
  -d '{
    "source": "gregorian",
    "targets": ["julian", "iso_week", "minguo"],
    "source_payload": {"year": 2026, "month": 3, "day": 9}
  }' | python3 -m json.tool
```

### 3) Timeline projection (timestamp-first)

```bash
curl -sS -X POST http://127.0.0.1:8000/timeline \
  -H "Content-Type: application/json" \
  -d '{
    "input_payload": {"timestamp": 1773014400},
    "timezone": "Asia/Taipei",
    "date_basis": "local",
    "targets": ["minguo", "japanese_era", "sexagenary", "solar_term_24"]
  }' | python3 -m json.tool
```

## Architecture

1. Parse input as an instant (`timestamp`, `timestamp_ms`, `iso_datetime`, or `local_datetime` + timezone).
2. Normalize to UTC.
3. Choose projection date basis (`local` or `utc`).
4. Convert from canonical Gregorian bridge date to target calendars.
5. Return structured JSON plus warnings for optional/approximate providers.

## Known Limitations (MVP)

- `sexagenary` year boundary is approximate.
- `solar_term_24` is fixed-date approximation, not ephemeris-accurate astronomy.
- Some calendars are available only when optional dependencies are installed.

## Roadmap

- Astronomical solar-term provider.
- Higher-precision Chinese lunar provider with regression fixtures.
- OpenAPI client examples for common agent runtimes.

## Repository Structure

- `scripts/calendar_bridge.py`: core conversion and timeline engine
- `scripts/api_server.py`: FastAPI service layer
- `scripts/run_api.sh`: API launch helper
- `scripts/curl_examples.sh`: HTTP smoke examples
- `references/integration-contract.md`: request/response contract
- `references/time-wheel-model.md`: timestamp-first design model

---

## 中文说明（简版）

Calendar Bridge 是一个给 AI agents 用的“时间与历法互通层”。
核心做法是先用时间戳统一“绝对时间”，再投影到不同时区与历法，输出稳定 JSON，方便多工具接入。

### 仓库简介建议（中文）

- 面向 AI agents 的专业万年历与跨历法互通 API（时间戳优先）
- AI 多代理协作的历法智能中间层（支持中西历法转换）

### MVP 现状

- 已有 FastAPI 服务层：`/health`、`/capabilities`、`/convert`、`/timeline`
- 已支持公历、儒略历、ISO 周、民国纪年、日本年号、佛历、干支、二十四节气（近似）
- 可选接入农历、伊斯兰历、希伯来历、波斯历（依赖额外安装）
