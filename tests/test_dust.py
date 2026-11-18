"""v4 dust signal (proposal D1-D3 in docs/evidence_v3_signals.md). Tests written before heatwarn/dust.py."""
import numpy as np
import pandas as pd

from heatwarn.dust import ELEVATED_PM10, HIGH_PM10, MIN_VALID_HOURS, daily_pm10, dust_level


def _hours(values_per_day, start="2025-06-01"):
    idx = pd.date_range(start, periods=24 * len(values_per_day), freq="h")
    return pd.Series(np.repeat(values_per_day, 24).astype(float), index=idx)


def test_thresholds_are_the_sourced_numbers():
    assert ELEVATED_PM10 == 150 and HIGH_PM10 == 250 and MIN_VALID_HOURS == 18


def test_daily_mean_of_the_local_day():
    s = _hours([100.0, 300.0])
    d = daily_pm10(s)
    assert list(d.round(1)) == [100.0, 300.0]


def test_fewer_than_18_valid_hours_is_missing():
    s = _hours([200.0])
    s.iloc[:7] = np.nan            # 17 valid hours left
    assert daily_pm10(s).isna().all()
    s2 = _hours([200.0])
    s2.iloc[:6] = np.nan           # 18 valid hours: enough
    assert daily_pm10(s2).iloc[0] == 200.0


def test_levels_use_strictly_above():
    assert dust_level(150.0) == "None"
    assert dust_level(150.1) == "Elevated"
    assert dust_level(250.0) == "Elevated"
    assert dust_level(250.1) == "High"
    assert dust_level(float("nan")) == "Insufficient data"
    assert dust_level(None) == "Insufficient data"


def test_infinite_values_never_reach_the_json():
    s = _hours([200.0])
    s.iloc[:3] = np.inf
    d = daily_pm10(s)
    assert np.isfinite(d.iloc[0]) and d.iloc[0] == 200.0      # 21 finite hours remain
    s2 = _hours([np.inf])
    assert daily_pm10(s2).isna().all()
