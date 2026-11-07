"""Alert rules R0-R3 (protocol v2). Output is a pandas nullable boolean: NA = insufficient data, never 'no alert'."""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

FIXED_HI_F = 80.0  # OSHA NEP heat priority day (CPL 03-00-024, 2026)


@dataclass(frozen=True)
class Params:
    t_low: float
    t_high: float
    a: float


def _with_na(alert: pd.Series, h: pd.Series) -> pd.Series:
    out = alert.astype("boolean")
    out[h.isna()] = pd.NA
    return out


def r0_calendar(index: pd.DatetimeIndex) -> pd.Series:
    md = index.month * 100 + index.day
    return pd.Series((md >= 615) & (md <= 915), index=index, dtype="boolean")


def r1_fixed(h: pd.Series) -> pd.Series:
    return _with_na(h >= FIXED_HI_F, h)


def r2_weather(h: pd.Series, a: pd.Series, p: Params) -> pd.Series:
    alert = (h >= p.t_high) | ((h >= p.t_low) & (a.fillna(-1e9) >= p.a))
    return _with_na(alert, h)


def r3_weather_workplace(h: pd.Series, a: pd.Series, w: pd.Series, p: Params) -> pd.Series:
    alert = (h >= p.t_high) | ((h >= p.t_low) & (a.fillna(-1e9) >= p.a)) | ((h >= p.t_low) & (w >= 1))
    return _with_na(alert, h)
