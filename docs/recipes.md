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

### 龙虾生命时空初始化
- Tool: `life_context`
- Suggested args:
  - `birth_input_payload`: 出生时间（timestamp/iso_datetime）
  - `now_input_payload`: 当前时间（可省略，默认系统当前 UTC）
  - `timezone`: `Asia/Taipei`（或对应地区时区）
  - `space_payload`: `location_name/latitude/longitude/climate/weather_note/scenery_note`
  - `subject_payload`: `entity_id/role/soul/traits/memory_anchor`
  - `auto_weather`: `true`
- Read from response:
  - `life.age`（活了多久）
  - `life.birthday`（生日与下次生日倒计时）
  - `environment.place`（现在在哪）
  - `environment.weather`（天气）
  - `world_context.scene_prompt`（可直接作为生成上下文）

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

### Build a life timeline context (birth -> now)
- Tool: `life_context`
- Suggested args:
  - `birth_input_payload`, `now_input_payload`, `timezone`
  - `space_payload` with `location_name`, `latitude`, `longitude`
  - `subject_payload` with `entity_id`, `role`, `soul`
  - `auto_weather=true`
- Read from response:
  - `life.age`, `life.birthday`
  - `environment.place`, `environment.weather`
  - `calendar_context.birth`, `calendar_context.now`

## Design Rule

- Keep MCP tool outputs structured JSON.
- Add user-facing summaries in your assistant layer, but do not replace the JSON contract.
