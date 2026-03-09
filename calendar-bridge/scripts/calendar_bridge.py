#!/usr/bin/env python3
"""Calendar Bridge CLI.

Normalize date conversions through a canonical Gregorian bridge.
"""

from __future__ import annotations

import argparse
import datetime as dt
import importlib
import json
import sys
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple
from zoneinfo import ZoneInfo


class CalendarError(ValueError):
    """Raised for invalid calendar payloads."""


@dataclass(frozen=True)
class DateParts:
    year: int
    month: int
    day: int

    def as_dict(self) -> Dict[str, int]:
        return {"year": self.year, "month": self.month, "day": self.day}

    def to_date(self) -> dt.date:
        try:
            return dt.date(self.year, self.month, self.day)
        except ValueError as exc:
            raise CalendarError(f"Invalid Gregorian date: {self.as_dict()}") from exc


class CalendarAdapter:
    name: str
    description: str
    payload_example: Dict[str, Any]
    bidirectional: bool = True
    approximate: bool = False

    def to_gregorian(self, payload: Dict[str, Any]) -> DateParts:
        raise NotImplementedError

    def from_gregorian(self, date_parts: DateParts) -> Dict[str, Any]:
        raise NotImplementedError


def require_keys(payload: Dict[str, Any], required: List[str], calendar_name: str) -> None:
    missing = [key for key in required if key not in payload]
    if missing:
        raise CalendarError(f"{calendar_name} payload missing keys: {missing}")


def to_int(value: Any, key: str) -> int:
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise CalendarError(f"Field '{key}' must be an integer") from exc


def to_float(value: Any, key: str) -> float:
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise CalendarError(f"Field '{key}' must be a number") from exc


def gregorian_to_jdn(date_parts: DateParts) -> int:
    y = date_parts.year
    m = date_parts.month
    d = date_parts.day
    a = (14 - m) // 12
    y2 = y + 4800 - a
    m2 = m + 12 * a - 3
    return d + ((153 * m2 + 2) // 5) + 365 * y2 + (y2 // 4) - (y2 // 100) + (y2 // 400) - 32045


def julian_to_jdn(year: int, month: int, day: int) -> int:
    a = (14 - month) // 12
    y = year + 4800 - a
    m = month + 12 * a - 3
    return day + ((153 * m + 2) // 5) + 365 * y + (y // 4) - 32083


def jdn_to_gregorian(jdn: int) -> DateParts:
    a = jdn + 32044
    b = (4 * a + 3) // 146097
    c = a - (146097 * b) // 4
    d = (4 * c + 3) // 1461
    e = c - (1461 * d) // 4
    m = (5 * e + 2) // 153
    day = e - (153 * m + 2) // 5 + 1
    month = m + 3 - 12 * (m // 10)
    year = 100 * b + d - 4800 + (m // 10)
    return DateParts(year=year, month=month, day=day)


def jdn_to_julian(jdn: int) -> DateParts:
    c = jdn + 32082
    d = (4 * c + 3) // 1461
    e = c - (1461 * d) // 4
    m = (5 * e + 2) // 153
    day = e - (153 * m + 2) // 5 + 1
    month = m + 3 - 12 * (m // 10)
    year = d - 4800 + (m // 10)
    return DateParts(year=year, month=month, day=day)


class GregorianAdapter(CalendarAdapter):
    name = "gregorian"
    description = "Proleptic Gregorian calendar date."
    payload_example = {"year": 2026, "month": 3, "day": 9}

    def to_gregorian(self, payload: Dict[str, Any]) -> DateParts:
        require_keys(payload, ["year", "month", "day"], self.name)
        date_parts = DateParts(
            year=to_int(payload["year"], "year"),
            month=to_int(payload["month"], "month"),
            day=to_int(payload["day"], "day"),
        )
        date_parts.to_date()
        return date_parts

    def from_gregorian(self, date_parts: DateParts) -> Dict[str, Any]:
        return date_parts.as_dict()


class JulianAdapter(CalendarAdapter):
    name = "julian"
    description = "Julian calendar date, bridged via Julian Day Number."
    payload_example = {"year": 2026, "month": 2, "day": 24}

    def to_gregorian(self, payload: Dict[str, Any]) -> DateParts:
        require_keys(payload, ["year", "month", "day"], self.name)
        year = to_int(payload["year"], "year")
        month = to_int(payload["month"], "month")
        day = to_int(payload["day"], "day")
        jdn = julian_to_jdn(year, month, day)
        return jdn_to_gregorian(jdn)

    def from_gregorian(self, date_parts: DateParts) -> Dict[str, Any]:
        julian = jdn_to_julian(gregorian_to_jdn(date_parts))
        return julian.as_dict()


class IsoWeekAdapter(CalendarAdapter):
    name = "iso_week"
    description = "ISO week date using iso_year + iso_week + iso_weekday (1-7)."
    payload_example = {"iso_year": 2026, "iso_week": 11, "iso_weekday": 1}

    def to_gregorian(self, payload: Dict[str, Any]) -> DateParts:
        require_keys(payload, ["iso_year", "iso_week", "iso_weekday"], self.name)
        iso_year = to_int(payload["iso_year"], "iso_year")
        iso_week = to_int(payload["iso_week"], "iso_week")
        iso_weekday = to_int(payload["iso_weekday"], "iso_weekday")
        try:
            greg = dt.date.fromisocalendar(iso_year, iso_week, iso_weekday)
        except ValueError as exc:
            raise CalendarError("Invalid ISO week payload") from exc
        return DateParts(greg.year, greg.month, greg.day)

    def from_gregorian(self, date_parts: DateParts) -> Dict[str, Any]:
        iso = date_parts.to_date().isocalendar()
        return {"iso_year": iso.year, "iso_week": iso.week, "iso_weekday": iso.weekday}


class UnixEpochAdapter(CalendarAdapter):
    name = "unix_epoch"
    description = "Unix epoch time as seconds or days since 1970-01-01 UTC."
    payload_example = {"epoch_seconds": 1773014400}

    def to_gregorian(self, payload: Dict[str, Any]) -> DateParts:
        if "epoch_seconds" in payload:
            seconds = to_int(payload["epoch_seconds"], "epoch_seconds")
            date_obj = dt.datetime.fromtimestamp(seconds, tz=dt.timezone.utc).date()
            return DateParts(date_obj.year, date_obj.month, date_obj.day)
        if "epoch_days" in payload:
            days = to_int(payload["epoch_days"], "epoch_days")
            base = dt.date(1970, 1, 1)
            date_obj = base + dt.timedelta(days=days)
            return DateParts(date_obj.year, date_obj.month, date_obj.day)
        raise CalendarError("unix_epoch payload requires 'epoch_seconds' or 'epoch_days'")

    def from_gregorian(self, date_parts: DateParts) -> Dict[str, Any]:
        midnight = dt.datetime(
            date_parts.year,
            date_parts.month,
            date_parts.day,
            tzinfo=dt.timezone.utc,
        )
        epoch_seconds = int(midnight.timestamp())
        epoch_days = (midnight.date() - dt.date(1970, 1, 1)).days
        return {"epoch_seconds": epoch_seconds, "epoch_days": epoch_days}


class MinguoAdapter(CalendarAdapter):
    name = "minguo"
    description = "Republic of China calendar (ROC year = Gregorian year - 1911)."
    payload_example = {"year": 115, "month": 3, "day": 9}

    def to_gregorian(self, payload: Dict[str, Any]) -> DateParts:
        require_keys(payload, ["year", "month", "day"], self.name)
        roc_year = to_int(payload["year"], "year")
        return GregorianAdapter().to_gregorian(
            {"year": roc_year + 1911, "month": payload["month"], "day": payload["day"]}
        )

    def from_gregorian(self, date_parts: DateParts) -> Dict[str, Any]:
        return {"year": date_parts.year - 1911, "month": date_parts.month, "day": date_parts.day}


class BuddhistEraAdapter(CalendarAdapter):
    name = "buddhist"
    description = "Thai Buddhist Era (BE year = Gregorian year + 543)."
    payload_example = {"year": 2569, "month": 3, "day": 9}

    def to_gregorian(self, payload: Dict[str, Any]) -> DateParts:
        require_keys(payload, ["year", "month", "day"], self.name)
        be_year = to_int(payload["year"], "year")
        return GregorianAdapter().to_gregorian(
            {"year": be_year - 543, "month": payload["month"], "day": payload["day"]}
        )

    def from_gregorian(self, date_parts: DateParts) -> Dict[str, Any]:
        return {"year": date_parts.year + 543, "month": date_parts.month, "day": date_parts.day}


ERA_TABLE: List[Tuple[str, dt.date]] = [
    ("meiji", dt.date(1868, 9, 8)),
    ("taisho", dt.date(1912, 7, 30)),
    ("showa", dt.date(1926, 12, 25)),
    ("heisei", dt.date(1989, 1, 8)),
    ("reiwa", dt.date(2019, 5, 1)),
]


class JapaneseEraAdapter(CalendarAdapter):
    name = "japanese_era"
    description = "Japanese era date using era + era_year + month + day."
    payload_example = {"era": "reiwa", "era_year": 8, "month": 3, "day": 9}

    def to_gregorian(self, payload: Dict[str, Any]) -> DateParts:
        require_keys(payload, ["era", "era_year", "month", "day"], self.name)
        era = str(payload["era"]).strip().lower()
        era_year = to_int(payload["era_year"], "era_year")
        month = to_int(payload["month"], "month")
        day = to_int(payload["day"], "day")

        start_date = next((start for era_name, start in ERA_TABLE if era_name == era), None)
        if start_date is None:
            raise CalendarError(f"Unknown Japanese era '{era}'")
        gregorian_year = start_date.year + era_year - 1
        candidate = DateParts(gregorian_year, month, day)
        date_obj = candidate.to_date()
        if era_year == 1 and date_obj < start_date:
            raise CalendarError("Date precedes start of selected Japanese era")
        return candidate

    def from_gregorian(self, date_parts: DateParts) -> Dict[str, Any]:
        date_obj = date_parts.to_date()
        era_name = "meiji"
        era_start = ERA_TABLE[0][1]
        for name, start in ERA_TABLE:
            if date_obj >= start:
                era_name = name
                era_start = start
        era_year = date_obj.year - era_start.year + 1
        return {
            "era": era_name,
            "era_year": era_year,
            "month": date_obj.month,
            "day": date_obj.day,
        }


HEAVENLY_STEMS = ["jia", "yi", "bing", "ding", "wu", "ji", "geng", "xin", "ren", "gui"]
EARTHLY_BRANCHES = ["zi", "chou", "yin", "mao", "chen", "si", "wu", "wei", "shen", "you", "xu", "hai"]
SOLAR_TERM_APPROX: List[Tuple[str, int, int]] = [
    ("minor_cold", 1, 5),
    ("major_cold", 1, 20),
    ("start_of_spring", 2, 4),
    ("rain_water", 2, 19),
    ("awakening_of_insects", 3, 6),
    ("spring_equinox", 3, 21),
    ("clear_and_bright", 4, 5),
    ("grain_rain", 4, 20),
    ("start_of_summer", 5, 6),
    ("grain_full", 5, 21),
    ("grain_in_ear", 6, 6),
    ("summer_solstice", 6, 21),
    ("minor_heat", 7, 7),
    ("major_heat", 7, 23),
    ("start_of_autumn", 8, 8),
    ("end_of_heat", 8, 23),
    ("white_dew", 9, 8),
    ("autumn_equinox", 9, 23),
    ("cold_dew", 10, 8),
    ("frost_descent", 10, 23),
    ("start_of_winter", 11, 7),
    ("minor_snow", 11, 22),
    ("major_snow", 12, 7),
    ("winter_solstice", 12, 22),
]


class SexagenaryAdapter(CalendarAdapter):
    name = "sexagenary"
    description = "Sexagenary year label (approximate boundary at Feb 4)."
    payload_example = {"stem": "bing", "branch": "wu", "cycle_index": 43}
    bidirectional = False
    approximate = True

    def to_gregorian(self, payload: Dict[str, Any]) -> DateParts:
        raise CalendarError("sexagenary cannot be used as source; use a concrete calendar source")

    def from_gregorian(self, date_parts: DateParts) -> Dict[str, Any]:
        # Approximate yearly boundary using Li Chun (~Feb 4).
        cycle_year = date_parts.year if (date_parts.month, date_parts.day) >= (2, 4) else date_parts.year - 1
        index = (cycle_year - 4) % 60
        stem = HEAVENLY_STEMS[index % 10]
        branch = EARTHLY_BRANCHES[index % 12]
        return {"stem": stem, "branch": branch, "cycle_index": index + 1}


def build_solar_term_events(year: int) -> List[Tuple[str, dt.date]]:
    return [(name, dt.date(year, month, day)) for name, month, day in SOLAR_TERM_APPROX]


class SolarTermsAdapter(CalendarAdapter):
    name = "solar_term_24"
    description = "Approximate 24 solar terms from fixed date boundaries."
    payload_example = {
        "current_term": "start_of_spring",
        "next_term": "rain_water",
        "days_to_next": 15,
    }
    bidirectional = False
    approximate = True

    def to_gregorian(self, payload: Dict[str, Any]) -> DateParts:
        raise CalendarError("solar_term_24 cannot be used as source; use a concrete calendar source")

    def from_gregorian(self, date_parts: DateParts) -> Dict[str, Any]:
        date_obj = date_parts.to_date()
        events = (
            build_solar_term_events(date_obj.year - 1)
            + build_solar_term_events(date_obj.year)
            + build_solar_term_events(date_obj.year + 1)
        )
        events.sort(key=lambda item: item[1])

        current_idx = 0
        for idx, (_, event_date) in enumerate(events):
            if event_date <= date_obj:
                current_idx = idx
            else:
                break
        next_idx = min(current_idx + 1, len(events) - 1)
        current_name, current_date = events[current_idx]
        next_name, next_date = events[next_idx]
        return {
            "current_term": current_name,
            "current_term_date": current_date.isoformat(),
            "next_term": next_name,
            "next_term_date": next_date.isoformat(),
            "days_to_next": (next_date - date_obj).days,
        }


class ChineseLunarAdapter(CalendarAdapter):
    name = "chinese_lunar"
    description = "Chinese lunisolar calendar via optional 'lunardate' package."
    payload_example = {"lunar_year": 2026, "lunar_month": 1, "lunar_day": 1, "is_leap_month": False}

    def __init__(self) -> None:
        self._lunardate = importlib.import_module("lunardate")

    def to_gregorian(self, payload: Dict[str, Any]) -> DateParts:
        require_keys(payload, ["lunar_year", "lunar_month", "lunar_day"], self.name)
        lunar_year = to_int(payload["lunar_year"], "lunar_year")
        lunar_month = to_int(payload["lunar_month"], "lunar_month")
        lunar_day = to_int(payload["lunar_day"], "lunar_day")
        is_leap_month = bool(payload.get("is_leap_month", False))

        lunar = self._lunardate.LunarDate(lunar_year, lunar_month, lunar_day, is_leap_month)
        greg = lunar.toSolarDate()
        return DateParts(greg.year, greg.month, greg.day)

    def from_gregorian(self, date_parts: DateParts) -> Dict[str, Any]:
        lunar = self._lunardate.LunarDate.fromSolarDate(date_parts.year, date_parts.month, date_parts.day)
        return {
            "lunar_year": lunar.year,
            "lunar_month": lunar.month,
            "lunar_day": lunar.day,
            "is_leap_month": bool(getattr(lunar, "isLeapMonth", False)),
        }


class ConvertdateCalendarAdapter(CalendarAdapter):
    def __init__(self, name: str, description: str, module_name: str) -> None:
        self.name = name
        self.description = description
        self.payload_example = {"year": 1447, "month": 1, "day": 1}
        convertdate = importlib.import_module("convertdate")
        self._module = getattr(convertdate, module_name)

    def to_gregorian(self, payload: Dict[str, Any]) -> DateParts:
        require_keys(payload, ["year", "month", "day"], self.name)
        year = to_int(payload["year"], "year")
        month = to_int(payload["month"], "month")
        day = to_int(payload["day"], "day")
        greg = self._module.to_gregorian(year, month, day)
        return DateParts(to_int(greg[0], "year"), to_int(greg[1], "month"), to_int(greg[2], "day"))

    def from_gregorian(self, date_parts: DateParts) -> Dict[str, Any]:
        local = self._module.from_gregorian(date_parts.year, date_parts.month, date_parts.day)
        return {"year": to_int(local[0], "year"), "month": to_int(local[1], "month"), "day": to_int(local[2], "day")}


def make_registry() -> Tuple[Dict[str, CalendarAdapter], List[str]]:
    registry: Dict[str, CalendarAdapter] = {
        "gregorian": GregorianAdapter(),
        "julian": JulianAdapter(),
        "iso_week": IsoWeekAdapter(),
        "unix_epoch": UnixEpochAdapter(),
        "minguo": MinguoAdapter(),
        "buddhist": BuddhistEraAdapter(),
        "japanese_era": JapaneseEraAdapter(),
        "sexagenary": SexagenaryAdapter(),
        "solar_term_24": SolarTermsAdapter(),
    }
    warnings: List[str] = []

    for calendar_name, ctor in (
        ("chinese_lunar", ChineseLunarAdapter),
        (
            "islamic",
            lambda: ConvertdateCalendarAdapter(
                name="islamic",
                description="Islamic calendar (civil/tabular) via convertdate.",
                module_name="islamic",
            ),
        ),
        (
            "hebrew",
            lambda: ConvertdateCalendarAdapter(
                name="hebrew",
                description="Hebrew calendar via convertdate.",
                module_name="hebrew",
            ),
        ),
        (
            "persian",
            lambda: ConvertdateCalendarAdapter(
                name="persian",
                description="Persian (Jalali) calendar via convertdate.",
                module_name="persian",
            ),
        ),
    ):
        try:
            registry[calendar_name] = ctor()
        except Exception:
            warnings.append(
                f"Optional provider '{calendar_name}' unavailable. Install dependencies to enable it."
            )
    return registry, warnings


def normalize_targets(raw_targets: str) -> List[str]:
    items = [item.strip() for item in raw_targets.split(",") if item.strip()]
    if not items:
        raise CalendarError("At least one target calendar is required")
    return items


def run_capabilities(registry: Dict[str, CalendarAdapter], warnings: List[str]) -> Dict[str, Any]:
    calendars = []
    for name in sorted(registry):
        adapter = registry[name]
        calendars.append(
            {
                "name": adapter.name,
                "description": adapter.description,
                "bidirectional": adapter.bidirectional,
                "approximate": adapter.approximate,
                "payload_example": adapter.payload_example,
            }
        )
    return {"command": "capabilities", "calendars": calendars, "warnings": warnings}


def run_convert(
    registry: Dict[str, CalendarAdapter],
    warnings: List[str],
    source: str,
    targets: List[str],
    payload: Dict[str, Any],
) -> Dict[str, Any]:
    if source not in registry:
        raise CalendarError(f"Unknown source calendar '{source}'")

    source_adapter = registry[source]
    canonical = source_adapter.to_gregorian(payload)
    result = {
        "command": "convert",
        "source": source,
        "source_payload": payload,
        "canonical_gregorian": canonical.as_dict(),
        "results": {},
        "unavailable_targets": [],
        "warnings": list(warnings),
    }

    for target in targets:
        adapter = registry.get(target)
        if adapter is None:
            result["unavailable_targets"].append(target)
            continue
        try:
            target_payload = adapter.from_gregorian(canonical)
            result["results"][target] = {
                "payload": target_payload,
                "approximate": adapter.approximate,
            }
        except Exception as exc:
            result["results"][target] = {"error": str(exc)}

    return result


def get_timezone(tz_name: str) -> dt.tzinfo:
    if tz_name.upper() in {"UTC", "Z"}:
        return dt.timezone.utc
    try:
        return ZoneInfo(tz_name)
    except Exception as exc:
        raise CalendarError(f"Unknown or unsupported timezone '{tz_name}'") from exc


def parse_instant_payload(payload: Dict[str, Any], timezone: dt.tzinfo) -> dt.datetime:
    if "timestamp" in payload:
        timestamp = to_float(payload["timestamp"], "timestamp")
        try:
            return dt.datetime.fromtimestamp(timestamp, tz=dt.timezone.utc)
        except (OverflowError, OSError, ValueError) as exc:
            raise CalendarError("timestamp is out of supported range") from exc
    if "timestamp_ms" in payload:
        timestamp_ms = to_float(payload["timestamp_ms"], "timestamp_ms")
        try:
            return dt.datetime.fromtimestamp(timestamp_ms / 1000.0, tz=dt.timezone.utc)
        except (OverflowError, OSError, ValueError) as exc:
            raise CalendarError("timestamp_ms is out of supported range") from exc
    if "iso_datetime" in payload:
        value = str(payload["iso_datetime"]).strip()
        if value.endswith("Z"):
            value = f"{value[:-1]}+00:00"
        try:
            parsed = dt.datetime.fromisoformat(value)
        except ValueError as exc:
            raise CalendarError("iso_datetime must follow ISO 8601 format") from exc
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone)
        return parsed.astimezone(dt.timezone.utc)
    if "local_datetime" in payload:
        value = str(payload["local_datetime"]).strip()
        normalized = value.replace(" ", "T")
        try:
            parsed = dt.datetime.fromisoformat(normalized)
        except ValueError as exc:
            raise CalendarError("local_datetime must follow YYYY-MM-DDTHH:MM:SS format") from exc
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone)
        return parsed.astimezone(dt.timezone.utc)
    raise CalendarError(
        "input payload must include one of: timestamp, timestamp_ms, iso_datetime, local_datetime"
    )


def run_timeline(
    registry: Dict[str, CalendarAdapter],
    warnings: List[str],
    input_payload: Dict[str, Any],
    timezone_name: str,
    date_basis: str,
    targets: Optional[List[str]],
) -> Dict[str, Any]:
    timezone = get_timezone(timezone_name)
    instant_utc = parse_instant_payload(input_payload, timezone)
    instant_local = instant_utc.astimezone(timezone)

    if date_basis == "utc":
        basis_date = instant_utc.date()
    else:
        basis_date = instant_local.date()

    gregorian_payload = {"year": basis_date.year, "month": basis_date.month, "day": basis_date.day}
    timeline_warnings = list(warnings)

    if targets is None:
        projection_targets = sorted(
            name for name in registry.keys() if name not in {"gregorian", "unix_epoch"}
        )
    else:
        projection_targets = targets
        if "unix_epoch" in projection_targets:
            timeline_warnings.append(
                "timeline projection is date-based; unix_epoch target reflects midnight UTC of projected date."
            )

    conversion = run_convert(
        registry=registry,
        warnings=warnings,
        source="gregorian",
        targets=projection_targets,
        payload=gregorian_payload,
    )

    utc_offset = instant_local.utcoffset()
    utc_offset_seconds = int(utc_offset.total_seconds()) if utc_offset is not None else 0

    return {
        "command": "timeline",
        "time_model": "timestamp_first",
        "timezone": timezone_name,
        "date_basis": date_basis,
        "input_payload": input_payload,
        "instant": {
            "timestamp": instant_utc.timestamp(),
            "timestamp_ms": int(round(instant_utc.timestamp() * 1000)),
            "iso_utc": instant_utc.isoformat(),
            "iso_local": instant_local.isoformat(),
            "utc_offset_seconds": utc_offset_seconds,
        },
        "bridge_date_gregorian": gregorian_payload,
        "calendar_projection": {
            "targets": projection_targets,
            "results": conversion["results"],
            "unavailable_targets": conversion["unavailable_targets"],
        },
        "warnings": sorted(set(timeline_warnings + conversion["warnings"])),
    }


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
