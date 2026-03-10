"""Calendar Bridge core engine.

Normalize date conversions through a canonical Gregorian bridge.
"""

from __future__ import annotations

import datetime as dt
import importlib
import json
import math
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

HEAVENLY_STEM_ZH_LABELS = {
    "jia": "甲",
    "yi": "乙",
    "bing": "丙",
    "ding": "丁",
    "wu": "戊",
    "ji": "己",
    "geng": "庚",
    "xin": "辛",
    "ren": "壬",
    "gui": "癸",
}

EARTHLY_BRANCH_ZH_LABELS = {
    "zi": "子",
    "chou": "丑",
    "yin": "寅",
    "mao": "卯",
    "chen": "辰",
    "si": "巳",
    "wu": "午",
    "wei": "未",
    "shen": "申",
    "you": "酉",
    "xu": "戌",
    "hai": "亥",
}

SOLAR_TERM_ZH_HANS_LABELS = {
    "minor_cold": "小寒",
    "major_cold": "大寒",
    "start_of_spring": "立春",
    "rain_water": "雨水",
    "awakening_of_insects": "惊蛰",
    "spring_equinox": "春分",
    "clear_and_bright": "清明",
    "grain_rain": "谷雨",
    "start_of_summer": "立夏",
    "grain_full": "小满",
    "grain_in_ear": "芒种",
    "summer_solstice": "夏至",
    "minor_heat": "小暑",
    "major_heat": "大暑",
    "start_of_autumn": "立秋",
    "end_of_heat": "处暑",
    "white_dew": "白露",
    "autumn_equinox": "秋分",
    "cold_dew": "寒露",
    "frost_descent": "霜降",
    "start_of_winter": "立冬",
    "minor_snow": "小雪",
    "major_snow": "大雪",
    "winter_solstice": "冬至",
}

SOLAR_TERM_ZH_HANT_LABELS = {
    "minor_cold": "小寒",
    "major_cold": "大寒",
    "start_of_spring": "立春",
    "rain_water": "雨水",
    "awakening_of_insects": "驚蟄",
    "spring_equinox": "春分",
    "clear_and_bright": "清明",
    "grain_rain": "穀雨",
    "start_of_summer": "立夏",
    "grain_full": "小滿",
    "grain_in_ear": "芒種",
    "summer_solstice": "夏至",
    "minor_heat": "小暑",
    "major_heat": "大暑",
    "start_of_autumn": "立秋",
    "end_of_heat": "處暑",
    "white_dew": "白露",
    "autumn_equinox": "秋分",
    "cold_dew": "寒露",
    "frost_descent": "霜降",
    "start_of_winter": "立冬",
    "minor_snow": "小雪",
    "major_snow": "大雪",
    "winter_solstice": "冬至",
}


def normalize_locale_tag(locale: Optional[str]) -> str:
    if locale is None:
        return "en"
    normalized = str(locale).strip().replace("_", "-").lower()
    if normalized == "":
        return "en"
    if normalized.startswith("zh"):
        parts = normalized.split("-")
        if "hant" in parts or any(tag in parts for tag in ("tw", "hk", "mo")):
            return "zh-Hant"
        if "hans" in parts or any(tag in parts for tag in ("cn", "sg")):
            return "zh-Hans"
        return "zh-Hans"
    return "en"


def localize_sexagenary_payload(payload: Dict[str, Any], locale_tag: str) -> Dict[str, Any]:
    stem = str(payload.get("stem", ""))
    branch = str(payload.get("branch", ""))
    localized = dict(payload)

    if locale_tag in {"zh-Hans", "zh-Hant"}:
        stem_label = HEAVENLY_STEM_ZH_LABELS.get(stem, stem)
        branch_label = EARTHLY_BRANCH_ZH_LABELS.get(branch, branch)
    else:
        stem_label = stem
        branch_label = branch

    localized["stem_label"] = stem_label
    localized["branch_label"] = branch_label
    localized["display"] = f"{stem_label}{branch_label}" if locale_tag.startswith("zh") else f"{stem}-{branch}"
    localized["locale"] = locale_tag
    return localized


def solar_term_label(term_key: str, locale_tag: str) -> str:
    if locale_tag == "zh-Hant":
        return SOLAR_TERM_ZH_HANT_LABELS.get(term_key, term_key)
    if locale_tag == "zh-Hans":
        return SOLAR_TERM_ZH_HANS_LABELS.get(term_key, term_key)
    return term_key


def localize_solar_term_payload(payload: Dict[str, Any], locale_tag: str) -> Dict[str, Any]:
    current_key = str(payload.get("current_term", ""))
    next_key = str(payload.get("next_term", ""))
    localized = dict(payload)
    current_label = solar_term_label(current_key, locale_tag)
    next_label = solar_term_label(next_key, locale_tag)
    localized["current_term_label"] = current_label
    localized["next_term_label"] = next_label
    localized["display"] = f"{current_label} -> {next_label}"
    localized["locale"] = locale_tag
    return localized


def localize_calendar_payload(target: str, payload: Dict[str, Any], locale_tag: str) -> Dict[str, Any]:
    if target == "sexagenary":
        return localize_sexagenary_payload(payload, locale_tag)
    if target == "solar_term_24":
        return localize_solar_term_payload(payload, locale_tag)
    return payload


ZH_STEM_TO_KEY = {value: key for key, value in HEAVENLY_STEM_ZH_LABELS.items()}
ZH_BRANCH_TO_KEY = {value: key for key, value in EARTHLY_BRANCH_ZH_LABELS.items()}

CHINESE_ZODIAC_ANIMAL_BY_BRANCH = {
    "zi": {"en": "rat", "zh_hans": "鼠", "zh_hant": "鼠"},
    "chou": {"en": "ox", "zh_hans": "牛", "zh_hant": "牛"},
    "yin": {"en": "tiger", "zh_hans": "虎", "zh_hant": "虎"},
    "mao": {"en": "rabbit", "zh_hans": "兔", "zh_hant": "兔"},
    "chen": {"en": "dragon", "zh_hans": "龙", "zh_hant": "龍"},
    "si": {"en": "snake", "zh_hans": "蛇", "zh_hant": "蛇"},
    "wu": {"en": "horse", "zh_hans": "马", "zh_hant": "馬"},
    "wei": {"en": "goat", "zh_hans": "羊", "zh_hant": "羊"},
    "shen": {"en": "monkey", "zh_hans": "猴", "zh_hant": "猴"},
    "you": {"en": "rooster", "zh_hans": "鸡", "zh_hant": "雞"},
    "xu": {"en": "dog", "zh_hans": "狗", "zh_hant": "狗"},
    "hai": {"en": "pig", "zh_hans": "猪", "zh_hant": "豬"},
}

MONTH_BOUNDARY_TERMS = [
    ("minor_cold", 1, 5, 11, 1),  # chou
    ("start_of_spring", 2, 4, 0, 2),  # yin
    ("awakening_of_insects", 3, 6, 1, 3),  # mao
    ("clear_and_bright", 4, 5, 2, 4),  # chen
    ("start_of_summer", 5, 6, 3, 5),  # si
    ("grain_in_ear", 6, 6, 4, 6),  # wu
    ("minor_heat", 7, 7, 5, 7),  # wei
    ("start_of_autumn", 8, 8, 6, 8),  # shen
    ("white_dew", 9, 8, 7, 9),  # you
    ("cold_dew", 10, 8, 8, 10),  # xu
    ("start_of_winter", 11, 7, 9, 11),  # hai
    ("major_snow", 12, 7, 10, 0),  # zi
]

SHA_DIRECTION_BY_BRANCH = {
    "zi": "south",
    "chen": "south",
    "shen": "south",
    "yin": "north",
    "wu": "north",
    "xu": "north",
    "hai": "west",
    "mao": "west",
    "wei": "west",
    "si": "east",
    "you": "east",
    "chou": "east",
}

SHA_DIRECTION_ZH = {"east": "东", "west": "西", "south": "南", "north": "北"}

WESTERN_WEEKDAY_RULERS = {
    0: {"planet": "moon", "label_en": "Monday", "label_zh": "周一"},
    1: {"planet": "mars", "label_en": "Tuesday", "label_zh": "周二"},
    2: {"planet": "mercury", "label_en": "Wednesday", "label_zh": "周三"},
    3: {"planet": "jupiter", "label_en": "Thursday", "label_zh": "周四"},
    4: {"planet": "venus", "label_en": "Friday", "label_zh": "周五"},
    5: {"planet": "saturn", "label_en": "Saturday", "label_zh": "周六"},
    6: {"planet": "sun", "label_en": "Sunday", "label_zh": "周日"},
}

WESTERN_SEASONS = [
    ((3, 20), "spring"),
    ((6, 21), "summer"),
    ((9, 23), "autumn"),
    ((12, 21), "winter"),
]

WESTERN_SEASON_ZH = {
    "spring": "春分季",
    "summer": "夏至季",
    "autumn": "秋分季",
    "winter": "冬至季",
}


def is_chinese_locale(locale_tag: str) -> bool:
    return locale_tag in {"zh-Hans", "zh-Hant"}


def pillar_display(stem: str, branch: str, locale_tag: str) -> str:
    if is_chinese_locale(locale_tag):
        return f"{HEAVENLY_STEM_ZH_LABELS.get(stem, stem)}{EARTHLY_BRANCH_ZH_LABELS.get(branch, branch)}"
    return f"{stem}-{branch}"


def animal_label(branch: str, locale_tag: str) -> str:
    info = CHINESE_ZODIAC_ANIMAL_BY_BRANCH.get(
        branch, {"en": branch, "zh_hans": branch, "zh_hant": branch}
    )
    if locale_tag == "zh-Hant":
        return str(info["zh_hant"])
    if locale_tag == "zh-Hans":
        return str(info["zh_hans"])
    return str(info["en"])


def branch_opposite(branch_index: int) -> str:
    return EARTHLY_BRANCHES[(branch_index + 6) % 12]


def resolve_month_boundary(date_obj: dt.date) -> Dict[str, Any]:
    events: List[Tuple[dt.date, str, int, int]] = []
    for year in (date_obj.year - 1, date_obj.year, date_obj.year + 1):
        for term_key, month, day, month_order, branch_index in MONTH_BOUNDARY_TERMS:
            events.append((dt.date(year, month, day), term_key, month_order, branch_index))
    events.sort(key=lambda item: item[0])

    selected = events[0]
    for event in events:
        if event[0] <= date_obj:
            selected = event
        else:
            break

    return {
        "boundary_date": selected[0],
        "term_key": selected[1],
        "month_order": selected[2],
        "branch_index": selected[3],
    }


def parse_ganzhi_text(value: str, locale_tag: str) -> Dict[str, Any]:
    text = str(value).strip()
    if len(text) >= 2 and text[0] in ZH_STEM_TO_KEY and text[1] in ZH_BRANCH_TO_KEY:
        stem = ZH_STEM_TO_KEY[text[0]]
        branch = ZH_BRANCH_TO_KEY[text[1]]
        return {
            "stem": stem,
            "branch": branch,
            "stem_label": HEAVENLY_STEM_ZH_LABELS.get(stem, stem),
            "branch_label": EARTHLY_BRANCH_ZH_LABELS.get(branch, branch),
            "display": text if is_chinese_locale(locale_tag) else f"{stem}-{branch}",
        }

    if "-" in text:
        left, right = text.split("-", 1)
        stem = left.strip().lower()
        branch = right.strip().lower()
        return {
            "stem": stem,
            "branch": branch,
            "stem_label": HEAVENLY_STEM_ZH_LABELS.get(stem, stem),
            "branch_label": EARTHLY_BRANCH_ZH_LABELS.get(branch, branch),
            "display": pillar_display(stem, branch, locale_tag),
        }

    return {"display": text}


def signed_angular_delta(left: float, right: float) -> float:
    return ((right - left + 540.0) % 360.0) - 180.0


def moon_phase_payload(instant_utc: dt.datetime, locale_tag: str) -> Dict[str, Any]:
    # Known new moon reference near J2000 epoch.
    reference = dt.datetime(2000, 1, 6, 18, 14, tzinfo=dt.timezone.utc)
    synodic_month = 29.53058867
    days = (instant_utc - reference).total_seconds() / 86400.0
    phase_age = days % synodic_month
    phase_fraction = phase_age / synodic_month
    illumination = 0.5 * (1.0 - math.cos(2.0 * math.pi * phase_fraction))

    phase_names_en = [
        "new_moon",
        "waxing_crescent",
        "first_quarter",
        "waxing_gibbous",
        "full_moon",
        "waning_gibbous",
        "last_quarter",
        "waning_crescent",
    ]
    phase_names_zh = ["新月", "娥眉月", "上弦", "盈凸", "满月", "亏凸", "下弦", "残月"]
    phase_index = int(((phase_fraction + 0.0625) % 1.0) * 8.0) % 8

    label = phase_names_zh[phase_index] if is_chinese_locale(locale_tag) else phase_names_en[phase_index]
    return {
        "phase_fraction": round(phase_fraction, 6),
        "phase_age_days": round(phase_age, 6),
        "illumination_ratio": round(illumination, 6),
        "label": label,
    }


def geocentric_longitude_for_body(body: str, instant_utc: dt.datetime) -> float:
    julian_day = julian_day_from_datetime(instant_utc)
    days_since_epoch = julian_day - 2451543.5

    earth_position = orbital_position(orbital_elements("earth", days_since_epoch))
    if body == "sun":
        return normalize_degrees(math.degrees(math.atan2(-earth_position["y"], -earth_position["x"])))
    if body == "moon":
        moon_position = orbital_position(orbital_elements("moon", days_since_epoch))
        return normalize_degrees(moon_position["longitude"])

    helio = orbital_position(orbital_elements(body, days_since_epoch))
    geo_x = helio["x"] - earth_position["x"]
    geo_y = helio["y"] - earth_position["y"]
    return normalize_degrees(math.degrees(math.atan2(geo_y, geo_x)))


def western_season(date_obj: dt.date, locale_tag: str) -> str:
    marker = (date_obj.month, date_obj.day)
    season = "winter"
    for boundary, name in WESTERN_SEASONS:
        if marker >= boundary:
            season = name
    if is_chinese_locale(locale_tag):
        return WESTERN_SEASON_ZH.get(season, season)
    return season


def build_western_almanac(
    instant_local: dt.datetime,
    instant_utc: dt.datetime,
    astro_snapshot: Dict[str, Any],
    locale_tag: str,
) -> Dict[str, Any]:
    governors = {
        str(item.get("name")): item for item in astro_snapshot.get("seven_governors", []) if item.get("name")
    }

    planetary_states: Dict[str, Dict[str, Any]] = {}
    for body in ("mercury", "venus", "mars", "jupiter", "saturn"):
        current = geocentric_longitude_for_body(body, instant_utc)
        previous = geocentric_longitude_for_body(body, instant_utc - dt.timedelta(days=1))
        nxt = geocentric_longitude_for_body(body, instant_utc + dt.timedelta(days=1))
        speed = signed_angular_delta(previous, nxt) / 2.0
        planetary_states[body] = {
            "longitude_deg": round(current, 6),
            "retrograde": speed < 0.0,
            "daily_motion_deg": round(speed, 6),
        }

    weekday_info = WESTERN_WEEKDAY_RULERS[instant_local.weekday()]
    return {
        "provider": "clawlendar_astro",
        "sun_sign": governors.get("sun", {}).get("zodiac_sign"),
        "moon_sign": governors.get("moon", {}).get("zodiac_sign"),
        "moon_phase": moon_phase_payload(instant_utc, locale_tag),
        "weekday_ruler": {
            "planet": weekday_info["planet"],
            "label": weekday_info["label_zh"] if is_chinese_locale(locale_tag) else weekday_info["label_en"],
        },
        "season": western_season(instant_local.date(), locale_tag),
        "planetary_states": planetary_states,
        "chart_points": {
            "seven_governors": astro_snapshot.get("seven_governors", []),
            "four_remainders": astro_snapshot.get("four_remainders", []),
            "major_aspects": astro_snapshot.get("major_aspects", []),
        },
    }


def build_eastern_metaphysics_fallback(
    registry: Dict[str, CalendarAdapter],
    date_parts: DateParts,
    instant_local: dt.datetime,
    locale_tag: str,
) -> Dict[str, Any]:
    date_obj = date_parts.to_date()
    cycle_year = date_obj.year if (date_obj.month, date_obj.day) >= (2, 4) else date_obj.year - 1
    year_cycle_index = (cycle_year - 4) % 60
    year_stem_index = year_cycle_index % 10
    year_branch_index = year_cycle_index % 12

    month_info = resolve_month_boundary(date_obj)
    first_month_stem_index = ((year_stem_index % 5) * 2 + 2) % 10
    month_stem_index = (first_month_stem_index + month_info["month_order"]) % 10
    month_branch_index = month_info["branch_index"]

    day_anchor = dt.date(1984, 2, 2)  # widely used JiaZi anchor in many perpetual-calendar implementations
    day_cycle_index = (date_obj.toordinal() - day_anchor.toordinal()) % 60
    day_stem_index = day_cycle_index % 10
    day_branch_index = day_cycle_index % 12

    hour_branch_index = ((instant_local.hour + 1) // 2) % 12
    hour_stem_index = ((day_stem_index % 5) * 2 + hour_branch_index) % 10

    year_stem = HEAVENLY_STEMS[year_stem_index]
    year_branch = EARTHLY_BRANCHES[year_branch_index]
    month_stem = HEAVENLY_STEMS[month_stem_index]
    month_branch = EARTHLY_BRANCHES[month_branch_index]
    day_stem = HEAVENLY_STEMS[day_stem_index]
    day_branch = EARTHLY_BRANCHES[day_branch_index]
    hour_stem = HEAVENLY_STEMS[hour_stem_index]
    hour_branch = EARTHLY_BRANCHES[hour_branch_index]

    lunar_payload = None
    lunar_adapter = registry.get("chinese_lunar")
    if lunar_adapter is not None:
        try:
            lunar_payload = lunar_adapter.from_gregorian(date_parts)
        except Exception:
            lunar_payload = None

    clash_branch = branch_opposite(day_branch_index)
    sha_direction_en = SHA_DIRECTION_BY_BRANCH.get(day_branch, "south")
    sha_direction = SHA_DIRECTION_ZH.get(sha_direction_en, sha_direction_en) if is_chinese_locale(locale_tag) else sha_direction_en

    yi = ["祭祀", "读书", "静修", "纳福"] if is_chinese_locale(locale_tag) else [
        "ritual",
        "study",
        "self-cultivation",
        "blessing",
    ]
    ji = ["动土", "远行", "大额签约"] if is_chinese_locale(locale_tag) else [
        "groundbreaking",
        "long-distance travel",
        "large contracts",
    ]

    return {
        "provider": "internal_approx",
        "approximate": True,
        "bazi": {
            "year": {
                "stem": year_stem,
                "branch": year_branch,
                "display": pillar_display(year_stem, year_branch, locale_tag),
            },
            "month": {
                "stem": month_stem,
                "branch": month_branch,
                "display": pillar_display(month_stem, month_branch, locale_tag),
            },
            "day": {
                "stem": day_stem,
                "branch": day_branch,
                "display": pillar_display(day_stem, day_branch, locale_tag),
            },
            "hour": {
                "stem": hour_stem,
                "branch": hour_branch,
                "display": pillar_display(hour_stem, hour_branch, locale_tag),
            },
            "year_animal": animal_label(year_branch, locale_tag),
        },
        "lunar_date": lunar_payload,
        "solar_term_context": {
            "boundary_term_key": month_info["term_key"],
            "boundary_term_label": solar_term_label(month_info["term_key"], locale_tag),
            "boundary_date": month_info["boundary_date"].isoformat(),
        },
        "huangli": {
            "yi": yi,
            "ji": ji,
            "clash": {
                "day_branch": day_branch,
                "day_branch_label": EARTHLY_BRANCH_ZH_LABELS.get(day_branch, day_branch),
                "opposite_branch": clash_branch,
                "opposite_branch_label": EARTHLY_BRANCH_ZH_LABELS.get(clash_branch, clash_branch),
            },
            "sha_direction": sha_direction,
            "notes": "Fallback approximation. Install 'lunar-python' for richer and more canonical almanac fields.",
        },
    }


def build_eastern_metaphysics_with_lunar_python(
    date_parts: DateParts,
    instant_local: dt.datetime,
    locale_tag: str,
) -> Dict[str, Any]:
    lunar_python = importlib.import_module("lunar_python")
    solar = lunar_python.Solar.fromYmdHms(
        instant_local.year,
        instant_local.month,
        instant_local.day,
        instant_local.hour,
        instant_local.minute,
        instant_local.second,
    )
    lunar = solar.getLunar()
    eight_char = lunar.getEightChar()

    year_pillar = parse_ganzhi_text(eight_char.getYear(), locale_tag)
    month_pillar = parse_ganzhi_text(eight_char.getMonth(), locale_tag)
    day_pillar = parse_ganzhi_text(eight_char.getDay(), locale_tag)
    hour_pillar = parse_ganzhi_text(eight_char.getTime(), locale_tag)

    year_branch = year_pillar.get("branch")
    year_animal = animal_label(year_branch, locale_tag) if year_branch else (
        lunar.getYearShengXiao() if is_chinese_locale(locale_tag) else str(lunar.getYearShengXiao())
    )

    return {
        "provider": "lunar_python",
        "approximate": False,
        "bazi": {
            "year": year_pillar,
            "month": month_pillar,
            "day": day_pillar,
            "hour": hour_pillar,
            "year_animal": year_animal,
            "wuxing": {
                "year": eight_char.getYearWuXing(),
                "month": eight_char.getMonthWuXing(),
                "day": eight_char.getDayWuXing(),
                "hour": eight_char.getTimeWuXing(),
            },
            "tai_yuan": eight_char.getTaiYuan(),
            "ming_gong": eight_char.getMingGong(),
            "shen_gong": eight_char.getShenGong(),
        },
        "lunar_date": {
            "lunar_year": lunar.getYear(),
            "lunar_month": lunar.getMonth(),
            "lunar_day": lunar.getDay(),
            "is_leap_month": bool(lunar.getMonth() < 0),
            "month_name": lunar.getMonthInChinese(),
            "day_name": lunar.getDayInChinese(),
            "year_ganzhi_exact": lunar.getYearInGanZhiExact(),
            "month_ganzhi_exact": lunar.getMonthInGanZhiExact(),
            "day_ganzhi_exact": lunar.getDayInGanZhiExact(),
            "hour_ganzhi": lunar.getTimeInGanZhi(),
        },
        "huangli": {
            "yi": list(lunar.getDayYi() or []),
            "ji": list(lunar.getDayJi() or []),
            "pengzu": {
                "gan": lunar.getPengZuGan(),
                "zhi": lunar.getPengZuZhi(),
            },
            "clash": lunar.getDayChongDesc(),
            "sha_direction": lunar.getDaySha(),
            "xiu": lunar.getXiu(),
            "zheng": lunar.getZheng(),
            "moon_phase_name": lunar.getYueXiang(),
            "day_shengxiao": lunar.getDayShengXiao(),
            "jieqi": lunar.getJieQi(),
            "festivals": list(lunar.getFestivals() or []),
            "other_festivals": list(lunar.getOtherFestivals() or []),
        },
    }


def build_eastern_metaphysics(
    registry: Dict[str, CalendarAdapter],
    date_parts: DateParts,
    instant_local: dt.datetime,
    locale_tag: str,
) -> Tuple[Dict[str, Any], List[str]]:
    try:
        data = build_eastern_metaphysics_with_lunar_python(date_parts, instant_local, locale_tag)
        warnings: List[str] = []
        if not is_chinese_locale(locale_tag):
            warnings.append("Eastern almanac textual fields are currently Chinese-first when using lunar_python.")
        return data, warnings
    except Exception:
        fallback = build_eastern_metaphysics_fallback(
            registry=registry,
            date_parts=date_parts,
            instant_local=instant_local,
            locale_tag=locale_tag,
        )
        return fallback, [
            "Optional provider 'lunar_python' unavailable. Using internal approximate Bazi/Huangli model."
        ]


def build_metaphysics_profile(
    registry: Dict[str, CalendarAdapter],
    date_parts: DateParts,
    instant_local: dt.datetime,
    instant_utc: dt.datetime,
    astro_snapshot: Dict[str, Any],
    locale_tag: str,
) -> Tuple[Dict[str, Any], List[str]]:
    eastern, eastern_warnings = build_eastern_metaphysics(
        registry=registry,
        date_parts=date_parts,
        instant_local=instant_local,
        locale_tag=locale_tag,
    )
    western = build_western_almanac(
        instant_local=instant_local,
        instant_utc=instant_utc,
        astro_snapshot=astro_snapshot,
        locale_tag=locale_tag,
    )
    return {"eastern": eastern, "western": western}, eastern_warnings

ZODIAC_SIGNS = [
    "aries",
    "taurus",
    "gemini",
    "cancer",
    "leo",
    "virgo",
    "libra",
    "scorpio",
    "sagittarius",
    "capricorn",
    "aquarius",
    "pisces",
]

SEVEN_GOVERNORS = ["sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn"]


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

    try:
        importlib.import_module("lunar_python")
    except Exception:
        warnings.append(
            "Optional provider 'lunar_python' unavailable. Eastern Bazi/Huangli will use internal approximation."
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
    return {
        "command": "capabilities",
        "calendars": calendars,
        "commands": {
            "convert": True,
            "timeline": True,
            "astro_snapshot": True,
            "calendar_month": True,
            "day_profile": True,
        },
        "metaphysics": {
            "supported": True,
            "eastern": {
                "bazi": True,
                "huangli": True,
                "provider_priority": ["lunar_python", "internal_approx"],
            },
            "western": {
                "chart": True,
                "moon_phase": True,
                "weekday_ruler": True,
                "planetary_states": True,
            },
        },
        "month_mode_sources": [
            name
            for name in sorted(registry.keys())
            if name
            in {
                "gregorian",
                "julian",
                "minguo",
                "buddhist",
                "japanese_era",
                "chinese_lunar",
                "islamic",
                "hebrew",
                "persian",
            }
        ],
        "astro": {
            "supported": True,
            "zodiac_systems": ["tropical"],
            "seven_governors": SEVEN_GOVERNORS,
            "four_remainders": [
                "ascending_node",
                "descending_node",
                "lunar_apogee_mean",
                "earth_perihelion",
            ],
            "approximate": True,
        },
        "i18n": {
            "supported_locales": ["en", "zh", "zh-CN", "zh-TW", "zh-Hans", "zh-Hant"],
            "localizable_targets": ["sexagenary", "solar_term_24"],
        },
        "warnings": warnings,
    }


def run_convert(
    registry: Dict[str, CalendarAdapter],
    warnings: List[str],
    source: str,
    targets: List[str],
    payload: Dict[str, Any],
    locale: Optional[str] = None,
) -> Dict[str, Any]:
    if source not in registry:
        raise CalendarError(f"Unknown source calendar '{source}'")

    source_adapter = registry[source]
    canonical = source_adapter.to_gregorian(payload)
    locale_tag = normalize_locale_tag(locale)
    result = {
        "command": "convert",
        "source": source,
        "source_payload": payload,
        "locale": locale_tag,
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
            target_payload = localize_calendar_payload(target, target_payload, locale_tag)
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


def normalize_degrees(value: float) -> float:
    result = value % 360.0
    if result < 0:
        return result + 360.0
    return result


def zodiac_sign_from_longitude(longitude_deg: float) -> str:
    index = int(normalize_degrees(longitude_deg) // 30.0) % 12
    return ZODIAC_SIGNS[index]


def julian_day_from_datetime(instant_utc: dt.datetime) -> float:
    return instant_utc.timestamp() / 86400.0 + 2440587.5


def solve_kepler(mean_anomaly_rad: float, eccentricity: float) -> float:
    estimate = mean_anomaly_rad + eccentricity * math.sin(mean_anomaly_rad) * (
        1.0 + eccentricity * math.cos(mean_anomaly_rad)
    )
    for _ in range(10):
        delta = (estimate - eccentricity * math.sin(estimate) - mean_anomaly_rad) / (
            1.0 - eccentricity * math.cos(estimate)
        )
        estimate -= delta
        if abs(delta) < 1e-9:
            break
    return estimate


def orbital_elements(body: str, days_since_epoch: float) -> Dict[str, float]:
    d = days_since_epoch
    if body == "earth":
        return {
            "N": 0.0,
            "i": 0.0,
            "w": 282.9404 + 4.70935e-5 * d,
            "a": 1.0,
            "e": 0.016709 - 1.151e-9 * d,
            "M": 356.0470 + 0.9856002585 * d,
        }
    if body == "moon":
        return {
            "N": 125.1228 - 0.0529538083 * d,
            "i": 5.1454,
            "w": 318.0634 + 0.1643573223 * d,
            "a": 60.2666,
            "e": 0.054900,
            "M": 115.3654 + 13.0649929509 * d,
        }
    if body == "mercury":
        return {
            "N": 48.3313 + 3.24587e-5 * d,
            "i": 7.0047 + 5.0e-8 * d,
            "w": 29.1241 + 1.01444e-5 * d,
            "a": 0.387098,
            "e": 0.205635 + 5.59e-10 * d,
            "M": 168.6562 + 4.0923344368 * d,
        }
    if body == "venus":
        return {
            "N": 76.6799 + 2.4659e-5 * d,
            "i": 3.3946 + 2.75e-8 * d,
            "w": 54.8910 + 1.38374e-5 * d,
            "a": 0.723330,
            "e": 0.006773 - 1.302e-9 * d,
            "M": 48.0052 + 1.6021302244 * d,
        }
    if body == "mars":
        return {
            "N": 49.5574 + 2.11081e-5 * d,
            "i": 1.8497 - 1.78e-8 * d,
            "w": 286.5016 + 2.92961e-5 * d,
            "a": 1.523688,
            "e": 0.093405 + 2.516e-9 * d,
            "M": 18.6021 + 0.5240207766 * d,
        }
    if body == "jupiter":
        return {
            "N": 100.4542 + 2.76854e-5 * d,
            "i": 1.3030 - 1.557e-7 * d,
            "w": 273.8777 + 1.64505e-5 * d,
            "a": 5.20256,
            "e": 0.048498 + 4.469e-9 * d,
            "M": 19.8950 + 0.0830853001 * d,
        }
    if body == "saturn":
        return {
            "N": 113.6634 + 2.3898e-5 * d,
            "i": 2.4886 - 1.081e-7 * d,
            "w": 339.3939 + 2.97661e-5 * d,
            "a": 9.55475,
            "e": 0.055546 - 9.499e-9 * d,
            "M": 316.9670 + 0.0334442282 * d,
        }
    raise CalendarError(f"Unsupported orbital body '{body}'")


def orbital_position(elements: Dict[str, float]) -> Dict[str, float]:
    N = math.radians(elements["N"])
    i = math.radians(elements["i"])
    w = math.radians(elements["w"])
    a = elements["a"]
    e = elements["e"]
    M = math.radians(normalize_degrees(elements["M"]))

    E = solve_kepler(M, e)
    xv = a * (math.cos(E) - e)
    yv = a * (math.sqrt(1.0 - e * e) * math.sin(E))
    v = math.atan2(yv, xv)
    r = math.sqrt(xv * xv + yv * yv)

    xh = r * (math.cos(N) * math.cos(v + w) - math.sin(N) * math.sin(v + w) * math.cos(i))
    yh = r * (math.sin(N) * math.cos(v + w) + math.cos(N) * math.sin(v + w) * math.cos(i))
    zh = r * (math.sin(v + w) * math.sin(i))

    longitude = normalize_degrees(math.degrees(math.atan2(yh, xh)))
    return {"x": xh, "y": yh, "z": zh, "r": r, "longitude": longitude}


def angular_separation(long_a: float, long_b: float) -> float:
    diff = abs(normalize_degrees(long_a) - normalize_degrees(long_b))
    return diff if diff <= 180.0 else 360.0 - diff


def major_aspects(points: Dict[str, float]) -> List[Dict[str, Any]]:
    aspect_defs = [
        ("conjunction", 0.0, 8.0),
        ("sextile", 60.0, 5.0),
        ("square", 90.0, 6.0),
        ("trine", 120.0, 6.0),
        ("opposition", 180.0, 8.0),
    ]
    names = list(points.keys())
    aspects: List[Dict[str, Any]] = []

    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            left = names[i]
            right = names[j]
            separation = angular_separation(points[left], points[right])
            best_match = None
            best_orb = None
            for aspect_name, target, orb in aspect_defs:
                current_orb = abs(separation - target)
                if current_orb <= orb and (best_orb is None or current_orb < best_orb):
                    best_match = (aspect_name, target, current_orb)
                    best_orb = current_orb
            if best_match is None:
                continue
            aspects.append(
                {
                    "left": left,
                    "right": right,
                    "aspect": best_match[0],
                    "exact_angle_deg": best_match[1],
                    "separation_deg": round(separation, 6),
                    "orb_deg": round(best_match[2], 6),
                }
            )
    aspects.sort(key=lambda item: item["orb_deg"])
    return aspects


def run_astro_snapshot(
    warnings: List[str],
    input_payload: Dict[str, Any],
    timezone_name: str = "UTC",
    zodiac_system: str = "tropical",
    bodies: Optional[List[str]] = None,
) -> Dict[str, Any]:
    if zodiac_system != "tropical":
        raise CalendarError("Only 'tropical' zodiac_system is supported in this version")

    timezone = get_timezone(timezone_name)
    instant_utc = parse_instant_payload(input_payload, timezone)
    instant_local = instant_utc.astimezone(timezone)

    # Orbital constants follow lightweight analytical approximations.
    julian_day = julian_day_from_datetime(instant_utc)
    days_since_epoch = julian_day - 2451543.5

    earth_elements = orbital_elements("earth", days_since_epoch)
    earth_position = orbital_position(earth_elements)

    sun_longitude = normalize_degrees(
        math.degrees(math.atan2(-earth_position["y"], -earth_position["x"]))
    )

    moon_elements = orbital_elements("moon", days_since_epoch)
    moon_position = orbital_position(moon_elements)

    results: Dict[str, Dict[str, Any]] = {
        "sun": {
            "longitude_deg": round(sun_longitude, 6),
            "zodiac_sign": zodiac_sign_from_longitude(sun_longitude),
            "distance_au": round(earth_position["r"], 6),
        },
        "moon": {
            "longitude_deg": round(moon_position["longitude"], 6),
            "zodiac_sign": zodiac_sign_from_longitude(moon_position["longitude"]),
            "distance_earth_radii": round(moon_position["r"], 6),
        },
    }

    for planet in ("mercury", "venus", "mars", "jupiter", "saturn"):
        helio = orbital_position(orbital_elements(planet, days_since_epoch))
        geo_x = helio["x"] - earth_position["x"]
        geo_y = helio["y"] - earth_position["y"]
        geo_z = helio["z"] - earth_position["z"]
        geo_r = math.sqrt(geo_x * geo_x + geo_y * geo_y + geo_z * geo_z)
        geo_longitude = normalize_degrees(math.degrees(math.atan2(geo_y, geo_x)))
        results[planet] = {
            "longitude_deg": round(geo_longitude, 6),
            "zodiac_sign": zodiac_sign_from_longitude(geo_longitude),
            "distance_au": round(geo_r, 6),
        }

    selected_bodies = SEVEN_GOVERNORS
    if bodies:
        normalized = [str(body).strip().lower() for body in bodies if str(body).strip()]
        invalid = [body for body in normalized if body not in SEVEN_GOVERNORS]
        if invalid:
            raise CalendarError(
                f"Unsupported bodies: {sorted(set(invalid))}. Allowed: {SEVEN_GOVERNORS}"
            )
        if normalized:
            selected_bodies = normalized

    seven_governors = [
        {
            "name": body,
            "longitude_deg": results[body]["longitude_deg"],
            "zodiac_sign": results[body]["zodiac_sign"],
        }
        for body in selected_bodies
    ]

    longitudes = {body: results[body]["longitude_deg"] for body in selected_bodies}
    aspects = major_aspects(longitudes)

    asc_node = normalize_degrees(moon_elements["N"])
    desc_node = normalize_degrees(asc_node + 180.0)
    lunar_perigee = normalize_degrees(moon_elements["N"] + moon_elements["w"])
    lunar_apogee = normalize_degrees(lunar_perigee + 180.0)
    earth_perihelion = normalize_degrees(earth_elements["N"] + earth_elements["w"])

    four_remainders = [
        {
            "name": "ascending_node",
            "longitude_deg": round(asc_node, 6),
            "zodiac_sign": zodiac_sign_from_longitude(asc_node),
        },
        {
            "name": "descending_node",
            "longitude_deg": round(desc_node, 6),
            "zodiac_sign": zodiac_sign_from_longitude(desc_node),
        },
        {
            "name": "lunar_apogee_mean",
            "longitude_deg": round(lunar_apogee, 6),
            "zodiac_sign": zodiac_sign_from_longitude(lunar_apogee),
        },
        {
            "name": "earth_perihelion",
            "longitude_deg": round(earth_perihelion, 6),
            "zodiac_sign": zodiac_sign_from_longitude(earth_perihelion),
        },
    ]

    utc_offset = instant_local.utcoffset()
    utc_offset_seconds = int(utc_offset.total_seconds()) if utc_offset is not None else 0

    astro_warnings = sorted(
        set(
            warnings
            + [
                "Astronomical outputs are analytical approximations and not ephemeris-grade precision.",
                "Zodiac system is tropical in this version.",
            ]
        )
    )

    return {
        "command": "astro_snapshot",
        "time_model": "timestamp_first",
        "timezone": timezone_name,
        "zodiac_system": zodiac_system,
        "input_payload": input_payload,
        "instant": {
            "timestamp": instant_utc.timestamp(),
            "timestamp_ms": int(round(instant_utc.timestamp() * 1000)),
            "iso_utc": instant_utc.isoformat(),
            "iso_local": instant_local.isoformat(),
            "utc_offset_seconds": utc_offset_seconds,
            "julian_day": round(julian_day, 6),
        },
        "seven_governors": seven_governors,
        "four_remainders": four_remainders,
        "major_aspects": aspects,
        "raw_positions": {body: results[body] for body in selected_bodies},
        "warnings": astro_warnings,
    }


def run_timeline(
    registry: Dict[str, CalendarAdapter],
    warnings: List[str],
    input_payload: Dict[str, Any],
    timezone_name: str,
    date_basis: str,
    targets: Optional[List[str]],
    locale: Optional[str] = None,
) -> Dict[str, Any]:
    timezone = get_timezone(timezone_name)
    instant_utc = parse_instant_payload(input_payload, timezone)
    instant_local = instant_utc.astimezone(timezone)
    locale_tag = normalize_locale_tag(locale)

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
        locale=locale_tag,
    )

    utc_offset = instant_local.utcoffset()
    utc_offset_seconds = int(utc_offset.total_seconds()) if utc_offset is not None else 0

    return {
        "command": "timeline",
        "time_model": "timestamp_first",
        "timezone": timezone_name,
        "date_basis": date_basis,
        "locale": locale_tag,
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


def month_identity_keys(source: str) -> List[str]:
    if source in {"gregorian", "julian", "minguo", "buddhist", "islamic", "hebrew", "persian"}:
        return ["year", "month"]
    if source == "japanese_era":
        return ["era", "era_year", "month"]
    if source == "chinese_lunar":
        return ["lunar_year", "lunar_month", "is_leap_month"]
    raise CalendarError(f"Calendar '{source}' does not support month boundary mode")


def day_key_for_source(source: str) -> str:
    if source == "chinese_lunar":
        return "lunar_day"
    if source in {
        "gregorian",
        "julian",
        "minguo",
        "buddhist",
        "islamic",
        "hebrew",
        "persian",
        "japanese_era",
    }:
        return "day"
    raise CalendarError(f"Calendar '{source}' does not support month boundary mode")


def normalize_month_identity(source: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    keys = month_identity_keys(source)
    identity: Dict[str, Any] = {}
    for key in keys:
        if key == "is_leap_month":
            identity[key] = bool(payload.get(key, False))
            continue
        if key not in payload:
            raise CalendarError(f"{source} month payload missing key '{key}'")
        value = payload[key]
        if key in {"year", "month", "era_year", "lunar_year", "lunar_month"}:
            identity[key] = to_int(value, key)
        else:
            identity[key] = str(value).strip().lower()
    return identity


def payload_month_identity(source: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    keys = month_identity_keys(source)
    identity: Dict[str, Any] = {}
    for key in keys:
        if key == "is_leap_month":
            identity[key] = bool(payload.get(key, False))
            continue
        if key not in payload:
            raise CalendarError(f"{source} payload missing identity key '{key}'")
        value = payload[key]
        if key in {"year", "month", "era_year", "lunar_year", "lunar_month"}:
            identity[key] = to_int(value, key)
        else:
            identity[key] = str(value).strip().lower()
    return identity


def month_identity_matches(source: str, payload: Dict[str, Any], month_identity: Dict[str, Any]) -> bool:
    try:
        extracted = payload_month_identity(source, payload)
    except CalendarError:
        return False
    for key, value in month_identity.items():
        if extracted.get(key) != value:
            return False
    return True


def build_first_day_payload(
    source: str,
    month_identity: Dict[str, Any],
    month_payload: Dict[str, Any],
) -> Dict[str, Any]:
    payload = dict(month_identity)
    day_key = day_key_for_source(source)
    payload[day_key] = 1
    # Preserve optional leap metadata for lunar calendars when provided.
    if source == "chinese_lunar":
        payload["is_leap_month"] = bool(month_payload.get("is_leap_month", False))
    return payload


def run_calendar_month(
    registry: Dict[str, CalendarAdapter],
    warnings: List[str],
    source: str,
    month_payload: Dict[str, Any],
) -> Dict[str, Any]:
    if source not in registry:
        raise CalendarError(f"Unknown source calendar '{source}'")
    adapter = registry[source]
    if not adapter.bidirectional:
        raise CalendarError(f"Calendar '{source}' is not bidirectional and cannot be used for month mode")

    month_identity = normalize_month_identity(source, month_payload)
    start_payload = build_first_day_payload(source, month_identity, month_payload)

    first_gregorian = adapter.to_gregorian(start_payload).to_date()
    days: List[Dict[str, Any]] = []
    started = False

    for offset in range(0, 66):
        current_date = first_gregorian + dt.timedelta(days=offset)
        current_parts = DateParts(current_date.year, current_date.month, current_date.day)
        source_view = adapter.from_gregorian(current_parts)
        day_key = day_key_for_source(source)
        if day_key not in source_view:
            raise CalendarError(f"{source} payload missing day key '{day_key}'")

        if month_identity_matches(source, source_view, month_identity):
            started = True
            days.append(
                {
                    "source_payload": source_view,
                    "gregorian": current_parts.as_dict(),
                    "weekday": current_date.isoweekday(),
                }
            )
        elif started:
            break

    if not days:
        raise CalendarError(
            f"Unable to resolve month boundary for {source} from payload {month_payload}. "
            "Check payload keys and optional calendar providers."
        )

    first_date = dt.date(
        days[0]["gregorian"]["year"],
        days[0]["gregorian"]["month"],
        days[0]["gregorian"]["day"],
    )
    last_date = dt.date(
        days[-1]["gregorian"]["year"],
        days[-1]["gregorian"]["month"],
        days[-1]["gregorian"]["day"],
    )
    prev_date = first_date - dt.timedelta(days=1)
    next_date = last_date + dt.timedelta(days=1)
    prev_payload_full = adapter.from_gregorian(DateParts(prev_date.year, prev_date.month, prev_date.day))
    next_payload_full = adapter.from_gregorian(DateParts(next_date.year, next_date.month, next_date.day))

    prev_month_payload = payload_month_identity(source, prev_payload_full)
    next_month_payload = payload_month_identity(source, next_payload_full)

    return {
        "command": "calendar_month",
        "source": source,
        "month_payload": month_identity,
        "range_gregorian": {
            "start": days[0]["gregorian"],
            "end": days[-1]["gregorian"],
            "day_count": len(days),
        },
        "previous_month_payload": prev_month_payload,
        "next_month_payload": next_month_payload,
        "days": days,
        "warnings": list(warnings),
    }


def run_day_profile(
    registry: Dict[str, CalendarAdapter],
    warnings: List[str],
    input_payload: Dict[str, Any],
    timezone_name: str,
    date_basis: str = "local",
    include_astro: bool = True,
    include_metaphysics: bool = True,
    locale: Optional[str] = None,
) -> Dict[str, Any]:
    detail_targets = [
        "iso_week",
        "minguo",
        "buddhist",
        "japanese_era",
        "sexagenary",
        "solar_term_24",
        "chinese_lunar",
    ]
    available_targets = [target for target in detail_targets if target in registry]

    timeline_result = run_timeline(
        registry=registry,
        warnings=warnings,
        input_payload=input_payload,
        timezone_name=timezone_name,
        date_basis=date_basis,
        targets=available_targets,
        locale=locale,
    )
    projection = timeline_result["calendar_projection"]["results"]

    profile: Dict[str, Any] = {
        "command": "day_profile",
        "time_model": timeline_result["time_model"],
        "timezone": timeline_result["timezone"],
        "date_basis": timeline_result["date_basis"],
        "locale": timeline_result["locale"],
        "input_payload": input_payload,
        "instant": timeline_result["instant"],
        "bridge_date_gregorian": timeline_result["bridge_date_gregorian"],
        "calendar_details": {
            "iso_week": projection.get("iso_week"),
            "minguo": projection.get("minguo"),
            "buddhist": projection.get("buddhist"),
            "japanese_era": projection.get("japanese_era"),
            "sexagenary": projection.get("sexagenary"),
            "solar_term_24": projection.get("solar_term_24"),
            "chinese_lunar": projection.get("chinese_lunar"),
        },
        "unavailable_targets": timeline_result["calendar_projection"]["unavailable_targets"],
        "warnings": list(timeline_result["warnings"]),
    }

    timezone = get_timezone(timezone_name)
    instant_utc = parse_instant_payload(input_payload, timezone)
    instant_local = instant_utc.astimezone(timezone)

    astro = None
    if include_astro or include_metaphysics:
        astro = run_astro_snapshot(
            warnings=warnings,
            input_payload=input_payload,
            timezone_name=timezone_name,
            zodiac_system="tropical",
            bodies=None,
        )

    if include_astro and astro is not None:
        profile["astro"] = {
            "seven_governors": astro["seven_governors"],
            "four_remainders": astro["four_remainders"],
            "major_aspects": astro["major_aspects"],
        }

    if include_metaphysics:
        locale_tag = timeline_result["locale"]
        metaphysics, meta_warnings = build_metaphysics_profile(
            registry=registry,
            date_parts=DateParts(
                timeline_result["bridge_date_gregorian"]["year"],
                timeline_result["bridge_date_gregorian"]["month"],
                timeline_result["bridge_date_gregorian"]["day"],
            ),
            instant_local=instant_local,
            instant_utc=instant_utc,
            astro_snapshot=astro if astro is not None else {"seven_governors": [], "four_remainders": [], "major_aspects": []},
            locale_tag=locale_tag,
        )
        profile["metaphysics"] = metaphysics
        profile["warnings"] = sorted(set(profile["warnings"] + meta_warnings))

    if astro is not None:
        profile["warnings"] = sorted(set(profile["warnings"] + astro["warnings"]))

    return profile
