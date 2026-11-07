"""Tests written before the implementation (protocol v2, 'Unit tests written before the code')."""
import numpy as np
import pandas as pd
import pytest

from heatwarn.heat_index import heat_index_f
from heatwarn.regions import REGIONS, Region, assign_region
from heatwarn.rules import Params, r2_weather, r3_weather_workplace
from heatwarn.signals import anomaly, daily_max_heat_index, workplace_signal
from heatwarn.metrics import episodes
from heatwarn.tune import TrainingLeakError, tune


# NWS heat index chart, RH 60 % row (weather.gov/safety/heat-index). Tolerance 1 °F (regression error ±1.3 °F).
@pytest.mark.parametrize("t_f,expected", [(86, 91), (90, 100), (96, 116)])
def test_heat_index_matches_nws_chart(t_f, expected):
    assert abs(heat_index_f(t_f, 60) - expected) <= 1.0


def test_heat_index_below_80_uses_simple_formula():
    hi = heat_index_f(70, 50)
    assert 68 <= hi <= 71


def _hourly(day_values_c, rh=60.0, start="2020-06-01"):
    """One day per value, 24 identical hours."""
    idx = pd.date_range(start, periods=24 * len(day_values_c), freq="h")
    temps = np.repeat(day_values_c, 24).astype(float)
    return pd.DataFrame({"temp_c": temps, "rh": rh}, index=idx)


def test_humidity_missing_gives_insufficient_not_low():
    hourly = _hourly([35.0, 35.0])
    hourly.loc[hourly.index.date == hourly.index[0].date(), "rh"] = np.nan
    h = daily_max_heat_index(hourly)
    assert np.isnan(h.iloc[0])          # insufficient, not a number
    assert h.iloc[1] > 100
    p = Params(t_low=80, t_high=95, a=5)
    a = anomaly(h)
    assert pd.isna(r2_weather(h, a, p).iloc[0])   # NA, never False


def test_anomaly_uses_only_previous_14_days():
    h = pd.Series(80.0, index=pd.date_range("2020-06-01", periods=30, freq="D"))
    base = anomaly(h)
    h2 = h.copy()
    h2.iloc[20] = 110.0
    a2 = anomaly(h2)
    assert a2.iloc[20] == pytest.approx(30.0)      # today's value minus a baseline that excludes today
    assert a2.iloc[21] != base.iloc[21]            # today enters tomorrow's baseline
    assert a2.iloc[19] == base.iloc[19]


def test_workplace_signal_uses_only_d_minus_3_to_d_minus_1():
    days = pd.date_range("2020-06-01", periods=10, freq="D")
    counts = pd.Series(0, index=days)
    counts.iloc[5] = 2
    w = workplace_signal(counts)
    assert w.iloc[5] == 0
    assert list(w.iloc[6:9]) == [2, 2, 2]
    assert w.iloc[9] == 0


def test_region_assignment_nearest_and_excluded():
    a = Region("a", "A", 30.0, -95.0, "UTC")
    b = Region("b", "B", 30.0, -94.0, "UTC")
    mid = assign_region(30.0, -94.5, regions=(a, b))
    assert mid in {"a", "b"} and mid == assign_region(30.0, -94.5, regions=(a, b))
    assert assign_region(45.0, -70.0, regions=REGIONS) is None


def test_r3_alerts_are_superset_of_r2():
    idx = pd.date_range("2020-06-01", periods=5, freq="D")
    h = pd.Series([82, 82, 96, 70, 85], index=idx, dtype=float)
    a = pd.Series([0, 0, 0, 0, 0], index=idx, dtype=float)
    w = pd.Series([1, 0, 0, 1, 0], index=idx)
    p = Params(t_low=80, t_high=95, a=5)
    r2, r3 = r2_weather(h, a, p), r3_weather_workplace(h, a, w, p)
    assert list(r2) == [False, False, True, False, False]
    assert list(r3) == [True, False, True, False, False]   # W needs H >= t_low (day 4 has H=70)


def test_tuning_refuses_test_years():
    idx = pd.date_range("2022-06-01", periods=3, freq="D")
    frame = pd.DataFrame({"region": "hou", "h": 90.0, "a": 0.0, "w": 0, "event": False}, index=idx)
    with pytest.raises(TrainingLeakError):
        tune(frame)


def test_episodes():
    s = pd.Series([True, True, False, True, False, False, True, True, True])
    n, longest = episodes(s)
    assert (n, longest) == (3, 3)


def test_block_bootstrap_resamples_whole_region_seasons_not_dates():
    from heatwarn.metrics import block_bootstrap
    idx = pd.date_range("2022-06-01", periods=10, freq="D")
    frame = pd.concat([pd.DataFrame({"region": r, "x": 1.0}, index=idx) for r in ("a", "b", "c")])
    lo, hi = block_bootstrap(frame, lambda s: float(len(s)), reps=50)
    assert lo == hi == 30.0      # 3 blocks of 10 rows each, always 30 rows (dates are shared across regions)


def test_recompute_anomaly_keeps_rows_aligned_per_region():
    from heatwarn.signals import anomaly_by_block
    idx = pd.date_range("2022-05-01", periods=20, freq="D")
    a = pd.DataFrame({"region": "zz", "h": 80.0}, index=idx)
    b = pd.DataFrame({"region": "aa", "h": 100.0}, index=idx)
    frame = pd.concat([a, b])                 # region order not alphabetical, dates duplicated
    frame.iloc[15, frame.columns.get_loc("h")] = 90.0
    out = anomaly_by_block(frame)
    assert out.iloc[15] == pytest.approx(10.0)   # region zz day 16: 90 - 80
    assert out.iloc[35] == pytest.approx(0.0)    # region aa day 16: 100 - 100
