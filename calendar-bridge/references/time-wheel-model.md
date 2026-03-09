# Time Wheel Model (Timestamp-First)

This model treats time as an absolute instant first, then as local calendar projections.

## 1) Core worldview

- Absolute layer: Unix timestamp (`seconds` / `milliseconds`) in UTC.
- Projection layer: timezone-local wall clock (`iso_local`).
- Calendar layer: date projection into Gregorian, lunisolar, era-based, and cyclical calendars.

## 2) Why this model works for agents

- Prevents timezone drift when multiple tools collaborate.
- Keeps event ordering stable across regions.
- Lets each agent project into its preferred calendar without changing the canonical instant.

## 3) Recommended processing order

1. Parse input instant (`timestamp`, `timestamp_ms`, `iso_datetime`, or `local_datetime + timezone`).
2. Normalize to UTC timestamp.
3. Project to local wall time with explicit timezone.
4. Select date basis (`local` or `utc`) for calendar conversions.
5. Convert bridge date to target calendars.
6. Return warnings for approximation/optional providers.

## 4) Rule of thumb

- Scheduling/event logs: use `timeline`.
- Pure date conversion with no time-of-day: use `convert`.

## 5) Precision notes

- `solar_term_24` and `sexagenary` are marked `approximate=true`.
- If astronomical precision is required, replace approximate adapters with ephemeris-backed providers.
