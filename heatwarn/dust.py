"""Dust / PM10 signal (v4). Rules D1-D3 in docs/evidence_v3_signals.md, signed by Dr Zayed on 18 Nov 2026 (docs/signoff.md S8).

Not tested on outcomes. Thresholds come from regulation and public-health sources:
- Elevated: daily mean PM10 > 150 ug/m3 (UAE Cabinet Decree 12/2006, Annex 8, 24-hour standard; = WHO 2021 IT-1).
- High: daily mean PM10 > 250 ug/m3 (UAE NCM air quality index 2023, start of the "Unhealthy" band).
- A day needs at least 18 valid hourly values (NCM 2023, 24-hour average validity rule).
"""
from __future__ import annotations

import math

import numpy as np
import pandas as pd

ELEVATED_PM10 = 150
HIGH_PM10 = 250
MIN_VALID_HOURS = 18


def daily_pm10(hourly: pd.Series) -> pd.Series:
    """Mean of the hourly PM10 values of each local day; NaN when fewer than 18 hours are valid. Infinite values count as missing."""
    hourly = hourly.where(np.isfinite(hourly))
    g = hourly.groupby(hourly.index.normalize())
    mean, n = g.mean(), g.count()
    return mean.where(n >= MIN_VALID_HOURS)


def dust_level(pm10_mean: float | None) -> str:
    if pm10_mean is None or not math.isfinite(pm10_mean):
        return "Insufficient data"
    if pm10_mean > HIGH_PM10:
        return "High"
    if pm10_mean > ELEVATED_PM10:
        return "Elevated"
    return "None"
