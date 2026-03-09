#!/usr/bin/env python3
"""Calendar Bridge CLI.

Thin CLI wrapper — core logic lives in clawlender.bridge.
"""

from __future__ import annotations

import argparse
import json
import sys

from clawlender.bridge import (
    CalendarError,
    make_registry,
    normalize_targets,
    run_capabilities,
    run_convert,
    run_timeline,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Calendar Bridge")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("capabilities", help="List available calendars and payload schemas")

    convert = sub.add_parser("convert", help="Convert one source calendar payload into target calendars")
    convert.add_argument("--source", required=True, help="Source calendar name")
    convert.add_argument(
        "--targets",
        required=True,
        help="Comma-separated target calendars (example: gregorian,julian,iso_week)",
    )
    convert.add_argument(
        "--date-json",
        required=True,
        help="JSON object for source payload",
    )

    timeline = sub.add_parser(
        "timeline",
        help="Timestamp-first timeline normalization and calendar projection",
    )
    timeline.add_argument(
        "--input-json",
        required=True,
        help="JSON object with timestamp/timestamp_ms/iso_datetime/local_datetime",
    )
    timeline.add_argument(
        "--timezone",
        default="UTC",
        help="IANA timezone for local interpretation and output (default: UTC)",
    )
    timeline.add_argument(
        "--date-basis",
        choices=["local", "utc"],
        default="local",
        help="Choose local or UTC date as the calendar projection date",
    )
    timeline.add_argument(
        "--targets",
        required=False,
        help="Optional comma-separated target calendars. Default projects to all date calendars except gregorian/unix_epoch.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    registry, warnings = make_registry()

    try:
        if args.command == "capabilities":
            output = run_capabilities(registry, warnings)
        elif args.command == "convert":
            targets = normalize_targets(args.targets)
            try:
                payload = json.loads(args.date_json)
                if not isinstance(payload, dict):
                    raise CalendarError("--date-json must be a JSON object")
            except json.JSONDecodeError as exc:
                raise CalendarError(f"Invalid JSON in --date-json: {exc}") from exc
            output = run_convert(registry, warnings, args.source, targets, payload)
        elif args.command == "timeline":
            try:
                input_payload = json.loads(args.input_json)
                if not isinstance(input_payload, dict):
                    raise CalendarError("--input-json must be a JSON object")
            except json.JSONDecodeError as exc:
                raise CalendarError(f"Invalid JSON in --input-json: {exc}") from exc
            targets = normalize_targets(args.targets) if args.targets else None
            output = run_timeline(
                registry=registry,
                warnings=warnings,
                input_payload=input_payload,
                timezone_name=args.timezone,
                date_basis=args.date_basis,
                targets=targets,
            )
        else:
            raise CalendarError(f"Unsupported command: {args.command}")
    except CalendarError as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=True, indent=2))
        return 1

    print(json.dumps(output, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
