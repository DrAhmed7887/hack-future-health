"""Protocol v4 features. Every feature for day d uses hourly data dated d or earlier (tests/test_model.py)."""
from __future__ import annotations

import numpy as np
import pandas as pd

from heatwarn.heat_index import c_to_f, heat_index_f
from heatwarn.signals import MIN_VALID_HOURS, anomaly, daily_max_heat_index

FEATURES = ["h", "p", "a", "night", "spell", "sun", "wind", "season_sin", "season_cos", "weekend"]
MONOTONIC_UP = {"h", "p", "a", "night", "spell", "sun"}  # risk may only rise with these (gradient boosting)
SPELL_P, SPELL_CAP = 60, 10
NIGHT_HOURS = range(0, 7)    # 00:00-06:00 local
MIDDAY_HOURS = range(10, 17)  # 10:00-16:00 local


def daily_weather_features(hourly: pd.DataFrame) -> pd.DataFrame:
    """hourly (local time): temp_c, rh, sw (shortwave W/m2, hour mean), wind (km/h). One row per day."""
    day = hourly.index.normalize()
    hour = hourly.index.hour
    h = daily_max_heat_index(hourly[["temp_c", "rh"]])
    hi = pd.Series(heat_index_f(c_to_f(hourly["temp_c"]), hourly["rh"].to_numpy(dtype=float)), index=hourly.index)
    night = hi[np.isin(hour, NIGHT_HOURS)].groupby(day[np.isin(hour, NIGHT_HOURS)]).min()
    sw_valid = hourly["sw"].notna().groupby(day).sum()
    sun = hourly["sw"].groupby(day).sum() * 3600 / 1e6          # MJ/m2
    sun[sw_valid < MIN_VALID_HOURS] = np.nan
    mid = np.isin(hour, MIDDAY_HOURS)
    wind = hourly["wind"][mid].groupby(day[mid]).mean()
    out = pd.DataFrame({"h": h, "a": anomaly(h), "night": night, "sun": sun, "wind": wind})
    out.index.name = "date"
    return out


def spell_days(p: pd.Series) -> pd.Series:
    """Consecutive previous days (in series order) with P >= 60, capped at 10. Today's own P is not used."""
    hot = (p >= SPELL_P).fillna(False).to_numpy()
    out = np.zeros(len(p), dtype=int)
    for i in range(1, len(p)):
        out[i] = min(out[i - 1] + 1, SPELL_CAP) if hot[i - 1] else 0
    return pd.Series(out, index=p.index)


def add_model_features(frame: pd.DataFrame, extras: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """frame: build_frame output (region, h, a, p, event...). extras: region -> daily_weather_features."""
    fr = frame.copy()
    for col in ("night", "sun", "wind"):
        fr[col] = np.nan
    fr["spell"] = 0
    for pos in fr.groupby("region", sort=False).indices.values():
        reg = fr["region"].iloc[pos[0]]
        ex = extras[reg].reindex(fr.index[pos])
        for col in ("night", "sun", "wind"):
            fr.iloc[pos, fr.columns.get_loc(col)] = ex[col].to_numpy()
    for pos in fr.groupby(["region", fr.index.year], sort=False).indices.values():
        fr.iloc[pos, fr.columns.get_loc("spell")] = spell_days(fr["p"].iloc[pos]).to_numpy()
    doy = fr.index.day_of_year.to_numpy()
    fr["season_sin"], fr["season_cos"] = np.sin(2 * np.pi * doy / 365.25), np.cos(2 * np.pi * doy / 365.25)
    fr["weekend"] = (fr.index.day_of_week >= 5).astype(float)
    return fr
