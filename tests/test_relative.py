"""Tests for the relative rule R4, written before the implementation (protocol v3)."""
import pandas as pd
import pytest

from heatwarn.relative import RelParams, percentile_rank, r4_relative, tune_relative
from heatwarn.tune import TrainingLeakError

REF = (2015, 2016, 2017)


def _series(values_by_year: dict[int, float], test_years=()) -> pd.Series:
    parts = []
    for y, v in values_by_year.items():
        idx = pd.date_range(f"{y}-06-01", f"{y}-06-30", freq="D")
        parts.append(pd.Series(v, index=idx))
    return pd.concat(parts)


def test_training_day_leaves_its_own_year_out():
    h = _series({2015: 80.0, 2016: 100.0, 2017: 90.0})
    h.loc["2016-06-15"] = 95.0
    p = percentile_rank(h, ref_years=REF)
    assert p.loc["2016-06-15"] == pytest.approx(100.0)   # 2016's own 100s excluded; 95 > 80 and 90


def test_test_day_uses_all_reference_years():
    h = _series({2015: 80.0, 2016: 100.0, 2017: 90.0, 2022: 85.0})
    p = percentile_rank(h, ref_years=REF)
    assert p.loc["2022-06-15"] == pytest.approx(100 / 3, abs=0.5)  # only the 80s are below 85


def test_extremes():
    h = _series({2015: 80.0, 2016: 90.0, 2017: 85.0, 2022: 80.0})
    h.loc["2022-06-10"] = 120.0
    h.loc["2022-06-11"] = 60.0
    p = percentile_rank(h, ref_years=REF)
    assert p.loc["2022-06-10"] == 100.0 and p.loc["2022-06-11"] == 0.0


def test_floor_blocks_alerts_below_80f():
    idx = pd.date_range("2022-06-01", periods=3, freq="D")
    h = pd.Series([79.0, 80.0, 95.0], index=idx)
    p = pd.Series([99.0, 99.0, 50.0], index=idx)
    a = pd.Series([0.0, 0.0, 0.0], index=idx)
    out = r4_relative(h, p, a, RelParams(p_high=90, p_low=70, a=5))
    assert list(out) == [False, True, False]


def test_relative_tuning_refuses_test_years():
    idx = pd.date_range("2022-06-01", periods=3, freq="D")
    frame = pd.DataFrame({"region": "x", "h": 90.0, "a": 0.0, "p": 50.0, "event": False}, index=idx)
    with pytest.raises(TrainingLeakError):
        tune_relative(frame, r1_alert_days=10)
