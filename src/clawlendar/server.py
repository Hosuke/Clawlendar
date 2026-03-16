"""Clawlendar MCP Server.

Exposes calendar conversion, timeline projection, and capability discovery
as MCP tools for Claude Desktop, Claude Code, and other MCP clients.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from clawlendar.bridge import (
    CalendarError,
    make_registry,
    run_calendar_month,
    run_astro_snapshot,
    run_capabilities,
    run_convert,
    run_day_profile,
    run_life_context,
    run_timeline,
    run_weather_at_time,
    run_weather_now,
)

mcp = FastMCP(
    "Clawlendar",
    json_response=True,
)

REGISTRY, WARNINGS = make_registry()


READ_ONLY_TOOL = ToolAnnotations(
    readOnlyHint=True,
    destructiveHint=False,
    idempotentHint=True,
    openWorldHint=False,
)


@mcp.tool(title="Capabilities", annotations=READ_ONLY_TOOL)
def capabilities() -> str:
    """List all supported calendars, their payload schemas, and optional provider status.

    Use this tool first to discover which calendars are available and what
    payload format each calendar expects.
    """
    result = run_capabilities(REGISTRY, WARNINGS)
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool(title="Convert Calendar Date", annotations=READ_ONLY_TOOL)
def convert(
    source: str,
    targets: List[str],
    source_payload: Dict[str, Any],
    locale: str = "en",
) -> str:
    """Convert a date from one calendar system to one or more target calendars.

    Args:
        source: Source calendar name (e.g. "gregorian", "julian", "minguo", "chinese_lunar").
        targets: List of target calendar names to convert into (e.g. ["julian", "iso_week", "minguo"]).
        source_payload: Calendar-specific date payload. For gregorian: {"year": 2026, "month": 3, "day": 9}.
            Call the capabilities tool to see payload examples for each calendar.

    Returns:
        JSON with canonical Gregorian bridge date, conversion results per target, and any warnings.
    """
    try:
        result = run_convert(
            registry=REGISTRY,
            warnings=WARNINGS,
            source=source,
            targets=targets,
            payload=source_payload,
            locale=locale,
        )
        return json.dumps(result, ensure_ascii=False, indent=2)
    except CalendarError as exc:
        return json.dumps({"error": str(exc)}, ensure_ascii=False, indent=2)


@mcp.tool(title="Timeline Projection", annotations=READ_ONLY_TOOL)
def timeline(
    input_payload: Dict[str, Any],
    timezone: str = "UTC",
    date_basis: str = "local",
    targets: Optional[List[str]] = None,
    locale: str = "en",
) -> str:
    """Normalize an instant (timestamp-first) and project it into multiple calendar systems.

    This is the primary tool for multi-agent scheduling and event processing.
    It takes a single instant in time, resolves it to a local or UTC date,
    then projects that date into all requested calendar systems.

    Args:
        input_payload: One of:
            - {"timestamp": 1773014400} (Unix seconds)
            - {"timestamp_ms": 1773014400000} (Unix milliseconds)
            - {"iso_datetime": "2026-03-09T12:00:00+08:00"}
            - {"local_datetime": "2026-03-09T12:00:00"} (interpreted in the given timezone)
        timezone: IANA timezone name (e.g. "Asia/Taipei", "America/New_York", "UTC").
        date_basis: "local" to use the local date for calendar projection, or "utc" to use UTC date.
        targets: Optional list of target calendars. If omitted, projects to all available date calendars.

    Returns:
        JSON with the normalized instant, bridge Gregorian date, and calendar projections.
    """
    try:
        result = run_timeline(
            registry=REGISTRY,
            warnings=WARNINGS,
            input_payload=input_payload,
            timezone_name=timezone,
            date_basis=date_basis,
            targets=targets,
            locale=locale,
        )
        return json.dumps(result, ensure_ascii=False, indent=2)
    except CalendarError as exc:
        return json.dumps({"error": str(exc)}, ensure_ascii=False, indent=2)


@mcp.tool(title="Astro Snapshot", annotations=READ_ONLY_TOOL)
def astro_snapshot(
    input_payload: Dict[str, Any],
    timezone: str = "UTC",
    zodiac_system: str = "tropical",
    bodies: Optional[List[str]] = None,
) -> str:
    """Return a timestamp-first astrological/astronomical snapshot for seven governors and four remainders.

    Args:
        input_payload: One of timestamp/timestamp_ms/iso_datetime/local_datetime payloads.
        timezone: IANA timezone used when parsing local datetime payloads.
        zodiac_system: Currently supports only "tropical".
        bodies: Optional subset of seven governors to include.
    """
    try:
        result = run_astro_snapshot(
            warnings=WARNINGS,
            input_payload=input_payload,
            timezone_name=timezone,
            zodiac_system=zodiac_system,
            bodies=bodies,
        )
        return json.dumps(result, ensure_ascii=False, indent=2)
    except CalendarError as exc:
        return json.dumps({"error": str(exc)}, ensure_ascii=False, indent=2)


@mcp.tool(title="Calendar Month Boundaries", annotations=READ_ONLY_TOOL)
def calendar_month(
    source: str,
    month_payload: Dict[str, Any],
) -> str:
    """Return true month boundaries and day list for the selected source calendar."""
    try:
        result = run_calendar_month(
            registry=REGISTRY,
            warnings=WARNINGS,
            source=source,
            month_payload=month_payload,
        )
        return json.dumps(result, ensure_ascii=False, indent=2)
    except CalendarError as exc:
        return json.dumps({"error": str(exc)}, ensure_ascii=False, indent=2)


@mcp.tool(title="Day Profile", annotations=READ_ONLY_TOOL)
def day_profile(
    input_payload: Dict[str, Any],
    timezone: str = "UTC",
    date_basis: str = "local",
    include_astro: bool = True,
    include_metaphysics: bool = True,
    locale: str = "en",
) -> str:
    """Return day-level profile: calendar details + optional astro + optional metaphysics."""
    try:
        result = run_day_profile(
            registry=REGISTRY,
            warnings=WARNINGS,
            input_payload=input_payload,
            timezone_name=timezone,
            date_basis=date_basis,
            include_astro=include_astro,
            include_metaphysics=include_metaphysics,
            locale=locale,
        )
        return json.dumps(result, ensure_ascii=False, indent=2)
    except CalendarError as exc:
        return json.dumps({"error": str(exc)}, ensure_ascii=False, indent=2)


@mcp.tool(title="Life Context", annotations=READ_ONLY_TOOL)
def life_context(
    birth_input_payload: Dict[str, Any],
    now_input_payload: Optional[Dict[str, Any]] = None,
    timezone: str = "UTC",
    date_basis: str = "local",
    space_payload: Optional[Dict[str, Any]] = None,
    subject_payload: Optional[Dict[str, Any]] = None,
    targets: Optional[List[str]] = None,
    locale: str = "en",
    auto_weather: bool = True,
) -> str:
    """Build continuity-safe world context for one lifeform from birth->now with time+space+subject anchors."""
    try:
        result = run_life_context(
            registry=REGISTRY,
            warnings=WARNINGS,
            birth_input_payload=birth_input_payload,
            now_input_payload=now_input_payload,
            timezone_name=timezone,
            date_basis=date_basis,
            space_payload=space_payload,
            subject_payload=subject_payload,
            targets=targets,
            locale=locale,
            auto_weather=auto_weather,
        )
        return json.dumps(result, ensure_ascii=False, indent=2)
    except CalendarError as exc:
        return json.dumps({"error": str(exc)}, ensure_ascii=False, indent=2)


@mcp.tool(title="Weather Now", annotations=READ_ONLY_TOOL)
def weather_now(
    location_payload: Dict[str, Any],
    timezone: str = "UTC",
    locale: str = "en",
) -> str:
    """Return weather at current time for a location (latitude/longitude required)."""
    try:
        result = run_weather_now(
            warnings=WARNINGS,
            location_payload=location_payload,
            timezone_name=timezone,
            locale=locale,
        )
        return json.dumps(result, ensure_ascii=False, indent=2)
    except CalendarError as exc:
        return json.dumps({"error": str(exc)}, ensure_ascii=False, indent=2)


@mcp.tool(title="Weather At Time", annotations=READ_ONLY_TOOL)
def weather_at_time(
    input_payload: Dict[str, Any],
    location_payload: Dict[str, Any],
    timezone: str = "UTC",
    locale: str = "en",
) -> str:
    """Return weather nearest to a requested instant for a location (latitude/longitude required)."""
    try:
        result = run_weather_at_time(
            warnings=WARNINGS,
            input_payload=input_payload,
            location_payload=location_payload,
            timezone_name=timezone,
            locale=locale,
        )
        return json.dumps(result, ensure_ascii=False, indent=2)
    except CalendarError as exc:
        return json.dumps({"error": str(exc)}, ensure_ascii=False, indent=2)


def main():
    """Entry point for the Clawlendar MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
