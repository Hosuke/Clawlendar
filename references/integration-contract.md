# Calendar Bridge Integration Contract

Use this contract when integrating multiple agents/tools into one date pipeline.

## 1) Canonical principle

- Use Unix timestamp as the canonical instant model whenever time-of-day exists.
- Convert instant -> projection date (local or UTC basis) -> target calendars.
- For date-only input, convert source calendar to canonical Gregorian date first.
- Return JSON, never mixed free-form text, when tool-to-tool integration is expected.

## 2) Commands

- `capabilities`: return available calendars, payload examples, and optional-provider warnings.
- `convert`: convert one source payload into many target calendar payloads.
- `timeline`: normalize one instant with timezone and project into target calendars.
- `astro_snapshot`: return seven governors, four remainders, and major aspects.
- `calendar_month`: resolve true month boundaries for a selected source calendar.
- `day_profile`: return one-call daily profile with calendar details and optional astro.

## 3) HTTP endpoints (FastAPI)

- `GET /health`
- `GET /capabilities`
- `POST /convert`
- `POST /timeline`
- `POST /astro`
- `POST /calendar-month`
- `POST /day-profile`

Local startup:

```bash
pip install -r requirements.txt
./scripts/run_api.sh
```

HTTP smoke test:

```bash
./scripts/curl_examples.sh
```

## 4) Convert request schema

```json
{
  "source": "gregorian",
  "targets": ["julian", "iso_week", "minguo"],
  "locale": "zh-CN",
  "source_payload": {
    "year": 2026,
    "month": 3,
    "day": 9
  }
}
```

## 5) Convert response schema

```json
{
  "command": "convert",
  "source": "gregorian",
  "locale": "zh-Hans",
  "source_payload": {
    "year": 2026,
    "month": 3,
    "day": 9
  },
  "canonical_gregorian": {
    "year": 2026,
    "month": 3,
    "day": 9
  },
  "results": {
    "julian": {
      "payload": {
        "year": 2026,
        "month": 2,
        "day": 24
      },
      "approximate": false
    },
    "sexagenary": {
      "payload": {
        "stem": "bing",
        "branch": "wu",
        "cycle_index": 43,
        "stem_label": "丙",
        "branch_label": "午",
        "display": "丙午",
        "locale": "zh-Hans"
      },
      "approximate": true
    }
  },
  "unavailable_targets": [],
  "warnings": []
}
```

## 6) Timeline request schema

```json
{
  "input_payload": {
    "timestamp": 1773014400
  },
  "timezone": "Asia/Taipei",
  "date_basis": "local",
  "locale": "zh-TW",
  "targets": ["minguo", "japanese_era", "sexagenary", "solar_term_24"]
}
```

`input_payload` accepts one of:
- `timestamp` (seconds)
- `timestamp_ms` (milliseconds)
- `iso_datetime` (ISO 8601 string, optional offset)
- `local_datetime` (`YYYY-MM-DDTHH:MM:SS`, interpreted in selected timezone)

## 7) Timeline response schema

```json
{
  "command": "timeline",
  "time_model": "timestamp_first",
  "timezone": "Asia/Taipei",
  "date_basis": "local",
  "locale": "zh-Hant",
  "instant": {
    "timestamp": 1773014400.0,
    "timestamp_ms": 1773014400000,
    "iso_utc": "2026-03-08T16:00:00+00:00",
    "iso_local": "2026-03-09T00:00:00+08:00",
    "utc_offset_seconds": 28800
  },
  "bridge_date_gregorian": {
    "year": 2026,
    "month": 3,
    "day": 9
  },
  "calendar_projection": {
    "targets": ["minguo", "japanese_era"],
    "results": {},
    "unavailable_targets": []
  },
  "warnings": []
}
```

## 8) Payload keys by calendar

- `gregorian`: `year`, `month`, `day`
- `julian`: `year`, `month`, `day`
- `iso_week`: `iso_year`, `iso_week`, `iso_weekday` (1=Mon ... 7=Sun)
- `unix_epoch`: `epoch_seconds` or `epoch_days`
- `minguo`: `year`, `month`, `day` where year 1 = 1912 CE
- `buddhist`: `year`, `month`, `day` where BE = CE + 543
- `japanese_era`: `era`, `era_year`, `month`, `day`
- `sexagenary` (derived only): `stem`, `branch`, `cycle_index`
- `solar_term_24` (derived only): `current_term`, `current_term_date`, `next_term`, `next_term_date`, `days_to_next`
- `sexagenary` and `solar_term_24` add localized display fields when `locale` is provided (`stem_label`, `branch_label`, `current_term_label`, `next_term_label`, `display`, `locale`)
- `chinese_lunar` (optional): `lunar_year`, `lunar_month`, `lunar_day`, `is_leap_month`
- `islamic`/`hebrew`/`persian` (optional): `year`, `month`, `day`

## 9) Astro request schema

```json
{
  "input_payload": {
    "timestamp": 1773014400
  },
  "timezone": "Asia/Taipei",
  "zodiac_system": "tropical",
  "bodies": ["sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn"]
}
```

## 10) Astro response schema

```json
{
  "command": "astro_snapshot",
  "time_model": "timestamp_first",
  "zodiac_system": "tropical",
  "seven_governors": [],
  "four_remainders": [],
  "major_aspects": [],
  "raw_positions": {},
  "warnings": []
}
```

## 11) Calendar month request schema

```json
{
  "source": "minguo",
  "month_payload": {
    "year": 115,
    "month": 3
  }
}
```

## 12) Calendar month response schema

```json
{
  "command": "calendar_month",
  "source": "minguo",
  "month_payload": {
    "year": 115,
    "month": 3
  },
  "range_gregorian": {
    "start": {
      "year": 2026,
      "month": 3,
      "day": 1
    },
    "end": {
      "year": 2026,
      "month": 3,
      "day": 31
    },
    "day_count": 31
  },
  "previous_month_payload": {},
  "next_month_payload": {},
  "days": [],
  "warnings": []
}
```

## 13) Day profile request schema

```json
{
  "input_payload": {
    "timestamp": 1773014400
  },
  "timezone": "Asia/Taipei",
  "date_basis": "local",
  "include_astro": true,
  "locale": "zh-CN"
}
```

## 14) Day profile response schema

```json
{
  "command": "day_profile",
  "time_model": "timestamp_first",
  "bridge_date_gregorian": {
    "year": 2026,
    "month": 3,
    "day": 9
  },
  "calendar_details": {},
  "astro": {},
  "warnings": []
}
```

## 15) Compatibility and versioning

- Prefer additive changes only: new calendars, new optional fields, new warnings.
- Do not rename existing keys in-place.
- Include `approximate=true` for outputs based on heuristic boundaries.

## 16) Dependency policy

- Core calendars require only Python standard library.
- Optional calendars activate only when dependencies are present:
  - `lunardate` for Chinese lunar
  - `convertdate` for Islamic/Hebrew/Persian
- Integrators should call `capabilities` at startup and cache availability.
