#!/usr/bin/env python3
"""FastAPI service layer for Calendar Bridge."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from clawlendar import bridge


app = FastAPI(
    title="Clawlendar API",
    version="0.2.1",
    description="Timestamp-first calendar and celestial interoperability service",
)

# MVP default: permissive CORS for easy multi-claw integration.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


REGISTRY, WARNINGS = bridge.make_registry()


class ConvertRequest(BaseModel):
    source: str = Field(..., description="Source calendar name")
    targets: List[str] = Field(..., min_length=1, description="Target calendar names")
    source_payload: Dict[str, Any] = Field(..., description="Calendar-specific source payload")
    locale: str = Field(default="en", description="Locale tag for localized labels (e.g. zh-CN, zh-TW)")


class TimelineRequest(BaseModel):
    input_payload: Dict[str, Any] = Field(
        ...,
        description="One of timestamp/timestamp_ms/iso_datetime/local_datetime",
    )
    timezone: str = Field(default="UTC", description="IANA timezone")
    date_basis: str = Field(default="local", description="'local' or 'utc'")
    targets: Optional[List[str]] = Field(
        default=None,
        description="Optional targets. Default projects all date calendars except gregorian/unix_epoch.",
    )
    locale: str = Field(default="en", description="Locale tag for localized labels (e.g. zh-CN, zh-TW)")


class AstroRequest(BaseModel):
    input_payload: Dict[str, Any] = Field(
        ...,
        description="One of timestamp/timestamp_ms/iso_datetime/local_datetime",
    )
    timezone: str = Field(default="UTC", description="IANA timezone")
    zodiac_system: str = Field(default="tropical", description="Currently only 'tropical'")
    bodies: Optional[List[str]] = Field(
        default=None,
        description="Optional subset of seven governors",
    )


class CalendarMonthRequest(BaseModel):
    source: str = Field(..., description="Source calendar for month mode")
    month_payload: Dict[str, Any] = Field(..., description="Calendar-specific month identity payload")


class DayProfileRequest(BaseModel):
    input_payload: Dict[str, Any] = Field(
        ...,
        description="One of timestamp/timestamp_ms/iso_datetime/local_datetime",
    )
    timezone: str = Field(default="UTC", description="IANA timezone")
    date_basis: str = Field(default="local", description="'local' or 'utc'")
    include_astro: bool = Field(default=True, description="Include astro snapshot in the profile")
    locale: str = Field(default="en", description="Locale tag for localized labels (e.g. zh-CN, zh-TW)")


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/capabilities")
def capabilities() -> Dict[str, Any]:
    return bridge.run_capabilities(REGISTRY, WARNINGS)


@app.post("/convert")
def convert(payload: ConvertRequest) -> Dict[str, Any]:
    try:
        return bridge.run_convert(
            registry=REGISTRY,
            warnings=WARNINGS,
            source=payload.source,
            targets=payload.targets,
            payload=payload.source_payload,
            locale=payload.locale,
        )
    except bridge.CalendarError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/timeline")
def timeline(payload: TimelineRequest) -> Dict[str, Any]:
    if payload.date_basis not in {"local", "utc"}:
        raise HTTPException(status_code=400, detail="date_basis must be 'local' or 'utc'")
    try:
        return bridge.run_timeline(
            registry=REGISTRY,
            warnings=WARNINGS,
            input_payload=payload.input_payload,
            timezone_name=payload.timezone,
            date_basis=payload.date_basis,
            targets=payload.targets,
            locale=payload.locale,
        )
    except bridge.CalendarError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/astro")
def astro(payload: AstroRequest) -> Dict[str, Any]:
    try:
        return bridge.run_astro_snapshot(
            warnings=WARNINGS,
            input_payload=payload.input_payload,
            timezone_name=payload.timezone,
            zodiac_system=payload.zodiac_system,
            bodies=payload.bodies,
        )
    except bridge.CalendarError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/calendar-month")
def calendar_month(payload: CalendarMonthRequest) -> Dict[str, Any]:
    try:
        return bridge.run_calendar_month(
            registry=REGISTRY,
            warnings=WARNINGS,
            source=payload.source,
            month_payload=payload.month_payload,
        )
    except bridge.CalendarError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/day-profile")
def day_profile(payload: DayProfileRequest) -> Dict[str, Any]:
    if payload.date_basis not in {"local", "utc"}:
        raise HTTPException(status_code=400, detail="date_basis must be 'local' or 'utc'")
    try:
        return bridge.run_day_profile(
            registry=REGISTRY,
            warnings=WARNINGS,
            input_payload=payload.input_payload,
            timezone_name=payload.timezone,
            date_basis=payload.date_basis,
            include_astro=payload.include_astro,
            locale=payload.locale,
        )
    except bridge.CalendarError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
