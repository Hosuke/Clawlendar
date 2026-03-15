# Vercel Agent Gateway Guide

This guide explains how agents can use the deployed web entrypoint:

- Frontend URL: https://clawlendar-web.vercel.app/

## Recommended Architecture

1. Keep `clawlendar-web` as the public human-facing entry.
2. Expose backend JSON tools via HTTP API (`/capabilities`, `/life-context`, etc.).
3. In Vercel, add API proxy routes (for example `/api/life-context`) that forward to your Clawlendar backend.
4. Let agents call the JSON API, then render or summarize in frontend/assistant layer.

## Why this split

- Stable machine contract for agents.
- Flexible UX for humans.
- Easy to add future providers (weather/geocode/scenery model) without breaking existing clients.

## Minimum Agent Flow (Life Bootstrap)

1. Call `GET /capabilities`.
2. Call `POST /life-context` with birth/now/space/subject.
3. Persist `life.life_id` + `life.continuity.tick_timestamp` as memory index keys.
4. On each new interaction, call `life_context` again and append context delta to memory.

## JSON Example

```json
{
  "birth_input_payload": {"iso_datetime": "2026-03-01T09:00:00+08:00"},
  "now_input_payload": {"iso_datetime": "2026-03-09T18:30:00+08:00"},
  "timezone": "Asia/Taipei",
  "space_payload": {
    "location_name": "Nanjing Qinhuai",
    "latitude": 32.0366,
    "longitude": 118.7895,
    "climate": "humid subtropical",
    "scenery_note": "night river lights"
  },
  "subject_payload": {
    "entity_id": "lobster-001",
    "role": "young daughter",
    "soul": "gentle and proactive"
  },
  "auto_weather": true,
  "locale": "en"
}
```

## Core Fields Agents Should Read

- `life.age` (how long alive)
- `life.birthday` (birthday and countdown)
- `environment.place` (where now)
- `environment.weather` (current weather snapshot, best effort)
- `world_context.scene_prompt` (ready-to-use context seed)

