# East-West Calendar Landscape (Practical Integration View)

This reference prioritizes practical adoption and interop needs for multi-agent systems.

## 1) Western and global defaults

- Gregorian: global civil standard (ISO 8601 date strings are Gregorian-based).
- Julian: historical and liturgical use in parts of Eastern Orthodox practice.
- ISO week date: common in logistics, manufacturing, and reporting (`YYYY-Www-D`).
- Unix epoch: machine-native time representation for APIs and event streams.

## 2) East Asian calendars commonly encountered

- Chinese lunisolar (Nongli): month/day naming, leap month handling, traditional festivals.
- 24 solar terms (Jieqi): season markers used in agriculture/culture.
- Sexagenary cycle (Ganzhi): 60-year cyclical labels.
- ROC/Minguo: Taiwan government/legal/business forms.
- Japanese era calendar: official forms and public-sector records in Japan.
- Korean Dangi and other local systems: niche but still present in cultural contexts.

## 3) Middle East and South Asia calendars

- Islamic (Hijri): religious observances; tabular vs observational variants matter.
- Persian (Jalali/Solar Hijri): civil use in Iran/Afghanistan.
- Hebrew: religious and cultural usage, especially holiday calculation.
- Hindu calendar families: many regional variants; treat as provider-specific.

## 4) Recommended rollout order for broad adoption

1. Gregorian + ISO week + Unix epoch (machine baseline)
2. Julian + ROC + Japanese era + Buddhist Era (high-impact regional support)
3. Chinese lunar + sexagenary + solar terms (East Asian cultural workflows)
4. Islamic + Hebrew + Persian (cross-region religious/civil workflows)
5. Variant-heavy systems (provider plugin model, not hardcoded assumptions)

## 5) Design cautions

- Do not assume one "true" Islamic or Hindu mapping; track algorithm variant.
- Distinguish civil date conversion from astronomical event computation.
- Mark approximation boundaries explicitly:
  - Sexagenary year boundary (Li Chun vs Lunar New Year conventions)
  - Solar-term precision (astronomical vs approximate tables)
- Keep source payload schema calendar-specific to avoid ambiguous keys.

## 6) Suggested provider strategy

- Core bridge: deterministic, dependency-light calendars.
- Optional providers: loaded dynamically, surfaced through `capabilities`.
- Per-provider metadata:
  - `provider_name`
  - `algorithm_variant`
  - `valid_year_range`
  - `approximation_notes`
