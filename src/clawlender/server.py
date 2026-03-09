"""Clawlender MCP Server.

Exposes calendar conversion, timeline projection, and capability discovery
as MCP tools for Claude Desktop, Claude Code, and other MCP clients.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from mcp.server.fastmcp import FastMCP

from .bridge import (
    CalendarError,
    make_registry,
    run_capabilities,
    run_convert,
    run_timeline,
)

mcp = FastMCP(
    "Clawlender",
    json_response=True,
)

REGISTRY, WARNINGS = make_registry()


@mcp.tool()
def capabilities() -> str:
    """List all supported calendars, their payload schemas, and optional provider status.

    Use this tool first to discover which calendars are available and what
    payload format each calendar expects.
    """
    result = run_capabilities(REGISTRY, WARNINGS)
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool()
def convert(
    source: str,
    targets: List[str],
    source_payload: Dict[str, Any],
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
        )
        return json.dumps(result, ensure_ascii=False, indent=2)
    except CalendarError as exc:
        return json.dumps({"error": str(exc)}, ensure_ascii=False, indent=2)


@mcp.tool()
def timeline(
    input_payload: Dict[str, Any],
    timezone: str = "UTC",
    date_basis: str = "local",
    targets: Optional[List[str]] = None,
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
        )
        return json.dumps(result, ensure_ascii=False, indent=2)
    except CalendarError as exc:
        return json.dumps({"error": str(exc)}, ensure_ascii=False, indent=2)


def main():
    """Entry point for the Clawlender MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
