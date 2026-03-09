# Calendar Bridge MVP Release Notes (v0.1.0)

## Summary

Calendar Bridge v0.1.0 delivers a timestamp-first calendar interoperability API and CLI for multi-agent integration.

## Included in v0.1.0

- Timestamp-first timeline normalization (`timeline`)
- Date conversion across core calendars (`convert`)
- Runtime capability discovery (`capabilities`)
- FastAPI service layer:
  - `GET /health`
  - `GET /capabilities`
  - `POST /convert`
  - `POST /timeline`
- Optional provider auto-detection:
  - `chinese_lunar` via `lunardate`
  - `islamic`, `hebrew`, `persian` via `convertdate`

## Core calendar support

- `gregorian`
- `julian`
- `iso_week`
- `unix_epoch`
- `minguo`
- `buddhist`
- `japanese_era`
- `sexagenary` (approximate)
- `solar_term_24` (approximate)

## Known limitations

- `sexagenary` uses approximate annual boundary near Li Chun.
- `solar_term_24` uses fixed-date approximation, not astronomical ephemeris.
- Optional calendars depend on local installation of provider packages.

## Quick run

```bash
pip install -r requirements.txt
./scripts/run_api.sh
./scripts/curl_examples.sh
```

## Docker run

```bash
docker build -t calendar-bridge:mvp .
docker run --rm -p 8000:8000 calendar-bridge:mvp
```

## Planned next milestones

- Replace approximate solar terms with astronomy-backed provider.
- Add regression test suite with pinned date fixtures.
- Publish OpenAPI-based client examples for common claw runtimes.
