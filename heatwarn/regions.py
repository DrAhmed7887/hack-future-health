"""Regions chosen on 7 Nov 2026 from 2015-2021 OSHA heat-report counts only (see docs/backtest_protocol.md).

Centres are city-centre coordinates. Weather is taken at the centre only (a stated limitation).
"""
from __future__ import annotations

import math
from typing import NamedTuple


class Region(NamedTuple):
    key: str
    name: str
    lat: float
    lon: float
    tz: str


REGIONS: tuple[Region, ...] = (
    Region("dfw", "Dallas-Fort Worth, TX", 32.78, -96.80, "America/Chicago"),
    Region("hou", "Houston, TX", 29.76, -95.37, "America/Chicago"),
    Region("sat", "San Antonio, TX", 29.42, -98.49, "America/Chicago"),
    Region("okc", "Oklahoma City, OK", 35.47, -97.52, "America/Chicago"),
    Region("mkc", "Kansas City, MO", 39.10, -94.58, "America/Chicago"),
    Region("orl", "Orlando, FL", 28.54, -81.38, "America/New_York"),
    Region("tpa", "Tampa, FL", 27.95, -82.46, "America/New_York"),
    Region("jax", "Jacksonville, FL", 30.33, -81.66, "America/New_York"),
)

MAX_KM = 100.0  # signed S6 / protocol: nearest centre within 100 km


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0088
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def assign_region(lat: float, lon: float, regions=REGIONS, max_km: float = MAX_KM) -> str | None:
    """Nearest region centre within max_km, else None. Ties go to the first region in list order (deterministic)."""
    best_key, best_d = None, math.inf
    for reg in regions:
        d = haversine_km(lat, lon, reg.lat, reg.lon)
        if d < best_d:
            best_key, best_d = reg.key, d
    return best_key if best_d <= max_km else None
