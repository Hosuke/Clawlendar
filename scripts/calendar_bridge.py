#!/usr/bin/env python3
"""Calendar Bridge CLI.

Thin CLI wrapper — core logic lives in clawlendar.bridge.
"""

from __future__ import annotations

import argparse
import json
import sys

from clawlendar.bridge import (
    CalendarError,
    make_registry,
    normalize_targets,
    run_calendar_month,
    run_astro_snapshot,
    run_capabilities,
    run_convert,
    run_day_profile,
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
    convert.add_argument(
        "--locale",
        default="en",
        help="Locale tag for localized labels (example: zh-CN, zh-TW)",
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
    timeline.add_argument(
        "--locale",
        default="en",
        help="Locale tag for localized labels (example: zh-CN, zh-TW)",
    )

    astro = sub.add_parser(
        "astro",
        help="Timestamp-first astrological snapshot (seven governors and four remainders)",
    )
    astro.add_argument(
        "--input-json",
        required=True,
        help="JSON object with timestamp/timestamp_ms/iso_datetime/local_datetime",
    )
    astro.add_argument(
        "--timezone",
        default="UTC",
        help="IANA timezone for local interpretation and output (default: UTC)",
    )
    astro.add_argument(
        "--zodiac-system",
        default="tropical",
        help="Zodiac system (currently only 'tropical')",
    )
    astro.add_argument(
        "--bodies",
        required=False,
        help="Optional comma-separated body subset (sun,moon,mercury,venus,mars,jupiter,saturn)",
    )

    month_mode = sub.add_parser(
        "calendar-month",
        help="Resolve true month boundaries in the selected source calendar",
    )
    month_mode.add_argument("--source", required=True, help="Source calendar name for month mode")
    month_mode.add_argument(
        "--month-json",
        required=True,
        help="JSON object describing month identity (example: {'year':2026,'month':3})",
    )

    day_profile = sub.add_parser(
        "day-profile",
        help="Return day-level profile (calendar details + optional astro snapshot)",
    )
    day_profile.add_argument(
        "--input-json",
        required=True,
        help="JSON object with timestamp/timestamp_ms/iso_datetime/local_datetime",
    )
    day_profile.add_argument(
        "--timezone",
        default="UTC",
        help="IANA timezone for local interpretation and output (default: UTC)",
    )
    day_profile.add_argument(
        "--date-basis",
        choices=["local", "utc"],
        default="local",
        help="Choose local or UTC date basis for projection",
    )
    day_profile.add_argument(
        "--no-astro",
        action="store_true",
        help="Disable astro snapshot in day profile output",
    )
    day_profile.add_argument(
        "--no-metaphysics",
        action="store_true",
        help="Disable metaphysics profile output (Bazi/Huangli/Western day almanac)",
    )
    day_profile.add_argument(
        "--locale",
        default="en",
        help="Locale tag for localized labels (example: zh-CN, zh-TW)",
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
            output = run_convert(registry, warnings, args.source, targets, payload, locale=args.locale)
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
                locale=args.locale,
            )
        elif args.command == "astro":
            try:
                input_payload = json.loads(args.input_json)
                if not isinstance(input_payload, dict):
                    raise CalendarError("--input-json must be a JSON object")
            except json.JSONDecodeError as exc:
                raise CalendarError(f"Invalid JSON in --input-json: {exc}") from exc
            bodies = normalize_targets(args.bodies) if args.bodies else None
            output = run_astro_snapshot(
                warnings=warnings,
                input_payload=input_payload,
                timezone_name=args.timezone,
                zodiac_system=args.zodiac_system,
                bodies=bodies,
            )
        elif args.command == "calendar-month":
            try:
                month_payload = json.loads(args.month_json)
                if not isinstance(month_payload, dict):
                    raise CalendarError("--month-json must be a JSON object")
            except json.JSONDecodeError as exc:
                raise CalendarError(f"Invalid JSON in --month-json: {exc}") from exc
            output = run_calendar_month(
                registry=registry,
                warnings=warnings,
                source=args.source,
                month_payload=month_payload,
            )
        elif args.command == "day-profile":
            try:
                input_payload = json.loads(args.input_json)
                if not isinstance(input_payload, dict):
                    raise CalendarError("--input-json must be a JSON object")
            except json.JSONDecodeError as exc:
                raise CalendarError(f"Invalid JSON in --input-json: {exc}") from exc
            output = run_day_profile(
                registry=registry,
                warnings=warnings,
                input_payload=input_payload,
                timezone_name=args.timezone,
                date_basis=args.date_basis,
                include_astro=not bool(args.no_astro),
                include_metaphysics=not bool(args.no_metaphysics),
                locale=args.locale,
            )
        else:
            raise CalendarError(f"Unsupported command: {args.command}")
    except CalendarError as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False, indent=2))
        return 1

    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
