# Tool Reference

Clawlendar is JSON-first by design. MCP tools return structured JSON that agents can parse deterministically.

## capabilities

- Purpose: discover calendars, commands, locale support, and optional provider status.
- Input: none.
- Output highlights:
  - `calendars[]`
  - `commands`
  - `metaphysics`
  - `i18n.supported_locales`

## convert

- Purpose: convert one source date payload into target calendars.
- Input:
  - `source` (string)
  - `targets` (string[])
  - `source_payload` (object)
  - `locale` (optional string)
- Output highlights:
  - `bridge_date_gregorian`
  - `results.<target>.payload`
  - `unavailable_targets`
  - `warnings`

## timeline

- Purpose: normalize one instant, then project date to target calendars.
- Input:
  - `input_payload` (`timestamp` | `timestamp_ms` | `iso_datetime` | `local_datetime`)
  - `timezone`
  - `date_basis` (`local` | `utc`)
  - `targets` (optional)
  - `locale` (optional)
- Output highlights:
  - `instant`
  - `bridge_date_gregorian`
  - `calendar_projection.results`

## astro_snapshot

- Purpose: seven governors, four remainders, and major aspects (analytical approximation).
- Input:
  - `input_payload`
  - `timezone`
  - `zodiac_system` (currently `tropical`)
  - `bodies` (optional)
- Output highlights:
  - `seven_governors[]`
  - `seven_governors[].symbol` (e.g. ☉☽☿♀♂♃♄)
  - `four_remainders[]`
  - `four_remainders[].symbol` (e.g. ☊☋⚸)
  - `major_aspects[]`
  - `major_aspects[].aspect_symbol` (e.g. ☌⚹□△☍)

## calendar_month

- Purpose: resolve true month boundaries and day list in selected source calendar.
- Input:
  - `source`
  - `month_payload`
- Output highlights:
  - `month_payload`
  - `days[]`
  - `previous_month_payload`
  - `next_month_payload`

## day_profile

- Purpose: one-call daily payload for calendar details + optional metaphysics and astro.
- Input:
  - `input_payload`
  - `timezone`
  - `date_basis`
  - `include_astro` (bool)
  - `include_metaphysics` (bool)
  - `locale`
- Output highlights:
  - `calendar_details`
  - `metaphysics.eastern.bazi`
  - `metaphysics.eastern.huangli.yi/ji`
  - `metaphysics.eastern.lunar_date.month_name/day_name` (when `lunar_python` available)
  - `metaphysics.western`

## life_context

- Purpose: generate continuity-safe world context for one lifeform from birth instant to now.
- Input:
  - `birth_input_payload` (required instant payload)
  - `now_input_payload` (optional instant payload; defaults to current UTC)
  - `timezone`
  - `date_basis`
  - `space_payload` (optional: location/country/region/city/latitude/longitude/elevation/background/climate/weather_note/scenery_note/environment_tags)
  - `subject_payload` (optional: entity_id/name/role/soul/traits/memory_anchor)
  - `targets` (optional projection calendars)
  - `locale`
  - `auto_weather` (bool, default true; best-effort weather enrichment from Open-Meteo when latitude/longitude are provided)
- Output highlights:
  - `life.age` (`seconds`, `days`, `readable`, `stage`)
  - `life.birthday` (`month`, `day`, `years_elapsed`, `days_until_next_birthday`)
  - `temporal_context` (local date/time, weekday, weekend flag, hemisphere season)
  - `environment.place` + `environment.weather`
  - `environment.weather.requested_time_local` + `time_delta_minutes` (nearest-hour match to timeline anchor)
  - `calendar_context.birth` and `calendar_context.now`
  - `world_context.scene_prompt`
  - `world_context.continuity_rules`

## Stability Notes

- Stable machine keys are preferred; localized display fields are additive.
- Approximate outputs are explicitly marked via `warnings` and adapter metadata.
