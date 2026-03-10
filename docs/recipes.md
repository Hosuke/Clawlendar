# Prompt Recipes (Intent -> Tool Calls)

Use natural-language intents at the assistant layer, then map to deterministic JSON tool calls.

## Chinese intents

### 今日吉凶
- Tool: `day_profile`
- Suggested args:
  - `timezone`: `Asia/Taipei`
  - `date_basis`: `local`
  - `include_metaphysics`: `true`
  - `include_astro`: `false`
  - `locale`: `zh-CN` or `zh-TW`
- Read from response:
  - `metaphysics.eastern.huangli.yi`
  - `metaphysics.eastern.huangli.ji`
  - `metaphysics.eastern.huangli.clash`
  - `metaphysics.eastern.huangli.sha_direction`

### 今日八字
- Tool: `day_profile`
- Suggested args: same as above + `include_astro` optional
- Read from response:
  - `metaphysics.eastern.bazi.year/month/day/hour`

### 农历今天是几月几日（中文）
- Tool: `day_profile`
- Read from response:
  - `metaphysics.eastern.lunar_date.month_name`
  - `metaphysics.eastern.lunar_date.day_name`

## English intents

### Today's astrology
- Tool: `day_profile`
- Suggested args:
  - `include_astro`: `true`
  - `include_metaphysics`: `false` (or true if both systems are needed)
  - `locale`: `en`
- Read from response:
  - `metaphysics.western.sun_sign`
  - `metaphysics.western.moon_sign`
  - `metaphysics.western.moon_phase`
  - `metaphysics.western.planetary_states`

### Convert this date to multiple systems
- Tool: `convert`
- Suggested args:
  - source date payload + list of target calendars

### Show month grid in lunar mode
- Tool: `calendar_month`
- Suggested args:
  - `source=chinese_lunar`
  - `month_payload={"lunar_year":...,"lunar_month":...,"is_leap_month":false}`

## Design Rule

- Keep MCP tool outputs structured JSON.
- Add user-facing summaries in your assistant layer, but do not replace the JSON contract.
