"""Relative (location-calibrated) rule R4: tiers from each region's own heat climatology (protocol v3)."""
from __future__ import annotations

import itertools
from dataclasses import dataclass

import numpy as np
import pandas as pd

from heatwarn.metrics import confusion
from heatwarn.rules import FIXED_HI_F
from heatwarn.tune import BUDGET_FRACTION, TRAIN_LAST_YEAR, TrainingLeakError

REF_YEARS = tuple(range(2015, 2022))
WINDOW_DAYS = 15
GRID_P_HIGH = (50, 60, 70, 80, 85, 90, 95)  # amendment 1 (training-only)
GRID_P_LOW = (30, 40, 50, 60, 70, 80)
GRID_A = (3, 5, 7, 9)


@dataclass(frozen=True)
class RelParams:
    p_high: float
    p_low: float
    a: float


def percentile_rank(h: pd.Series, ref_years=REF_YEARS, window: int = WINDOW_DAYS) -> pd.Series:
    """Percentile (0-100) of each day's H among reference-year values within ±window calendar days.

    A day inside the reference years leaves its own year out. Ties count half. NaN in -> NaN out.
    """
    ref = h[h.index.year.isin(ref_years)].dropna()
    r_doy, r_year, r_val = ref.index.day_of_year.to_numpy(), ref.index.year.to_numpy(), ref.to_numpy()
    out = np.full(len(h), np.nan)
    for i, (d, x) in enumerate(zip(h.index, h.to_numpy())):
        if np.isnan(x):
            continue
        dist = np.abs(r_doy - d.day_of_year)
        mask = np.minimum(dist, 366 - dist) <= window
        if d.year in ref_years:
            mask &= r_year != d.year
        v = r_val[mask]
        if len(v):
            out[i] = 100.0 * ((v < x).sum() + 0.5 * (v == x).sum()) / len(v)
    return pd.Series(out, index=h.index)


def r4_relative(h: pd.Series, p: pd.Series, a: pd.Series, rp: RelParams) -> pd.Series:
    alert = (h >= FIXED_HI_F) & ((p >= rp.p_high) | ((p >= rp.p_low) & (a.fillna(-1e9) >= rp.a)))
    out = alert.astype("boolean")
    out[h.isna() | p.isna()] = pd.NA
    return out


def r4_tier(h: pd.Series, p: pd.Series, a: pd.Series, rp: RelParams) -> pd.Series:
    """'High', 'Elevated', 'No escalation' or 'Insufficient data' (never 'safe')."""
    alert = r4_relative(h, p, a, rp)
    tier = pd.Series("No escalation", index=h.index, dtype=object)
    tier[alert.fillna(False).astype(bool)] = "Elevated"
    tier[alert.fillna(False).astype(bool) & (p >= rp.p_high)] = "High"
    tier[alert.isna()] = "Insufficient data"
    return tier


def tune_relative(frame: pd.DataFrame, r1_alert_days: int) -> dict:
    if (frame.index.year > TRAIN_LAST_YEAR).any():
        raise TrainingLeakError("tuning frame contains test years (>= 2022)")
    budget = BUDGET_FRACTION * r1_alert_days
    best = None
    for p_high, p_low, a in itertools.product(GRID_P_HIGH, GRID_P_LOW, GRID_A):
        if p_low >= p_high:
            continue
        rp = RelParams(p_high, p_low, a)
        c = confusion(r4_relative(frame["h"], frame["p"], frame["a"], rp), frame["event"])
        if c["alert_days"] > budget:
            continue
        key = (c["sensitivity"], -c["alert_days"])
        if best is None or key > best[0]:
            best = (key, rp, c)
    if best is None:
        raise RuntimeError("no relative grid point within budget")
    return {"params": best[1].__dict__, "train": best[2], "budget_alert_days": budget}
