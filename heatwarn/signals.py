"""Daily signals. Every feature for day d uses only data available for that day or earlier days (see tests)."""
from __future__ import annotations

import numpy as np
import pandas as pd

from heatwarn.heat_index import c_to_f, heat_index_f

MIN_VALID_HOURS = 18      # fewer valid hours in a day -> "insufficient data"
BASELINE_DAYS = 14        # signed S2
BASELINE_MIN_DAYS = 10
WORKPLACE_DAYS = 3        # signed S3


def daily_max_heat_index(hourly: pd.DataFrame) -> pd.Series:
    """hourly: DatetimeIndex (local time), columns temp_c and rh. Returns daily max heat index (°F), NaN if insufficient."""
    hi = pd.Series(heat_index_f(c_to_f(hourly["temp_c"]), hourly["rh"].to_numpy(dtype=float)), index=hourly.index)
    day = hourly.index.normalize()
    valid = hi.notna().groupby(day).sum()
    out = hi.groupby(day).max()
    out[valid < MIN_VALID_HOURS] = np.nan
    out.index.name = "date"
    return out


def anomaly(h: pd.Series) -> pd.Series:
    """H(d) minus the mean of H over d-14..d-1 (needs >= 10 valid days). Weather history, not acclimatisation."""
    baseline = h.shift(1).rolling(BASELINE_DAYS, min_periods=BASELINE_MIN_DAYS).mean()
    return h - baseline


def workplace_signal(counts: pd.Series) -> pd.Series:
    """Number of reports with incident dates d-3..d-1. counts: reports per day on a continuous daily index."""
    return counts.shift(1).rolling(WORKPLACE_DAYS, min_periods=1).sum().fillna(0).astype(int)


def anomaly_by_block(frame: pd.DataFrame) -> pd.Series:
    """Recompute the anomaly within each (region, year) block of a season-filtered frame, keeping row order.

    Positional, because dates repeat across regions. Used for missing-input tests: early-season days have no
    April baseline here, so their anomaly is NaN (the anomaly term then cannot fire).
    """
    out = np.full(len(frame), np.nan)
    for pos in frame.groupby(["region", frame.index.year]).indices.values():
        out[pos] = anomaly(frame["h"].iloc[pos]).to_numpy()
    return pd.Series(out, index=frame.index)
