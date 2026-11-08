"""Protocol v4 unit tests, written before the feature and model code."""
import numpy as np
import pandas as pd
import pytest

from heatwarn.features import FEATURES, daily_weather_features, spell_days
from heatwarn.model import fit_gb, operating_threshold, select_and_fit
from heatwarn.relative import percentile_rank
from heatwarn.tune import TrainingLeakError


def hourly_frame(days=40, seed=0):
    rng = np.random.default_rng(seed)
    idx = pd.date_range("2018-06-01", periods=24 * days, freq="h")
    hour = idx.hour.to_numpy()
    temp = 28 + 7 * np.sin((hour - 9) / 24 * 2 * np.pi) + rng.normal(0, 1, len(idx))
    return pd.DataFrame({"temp_c": temp, "rh": 60 + rng.normal(0, 5, len(idx)),
                         "sw": np.clip(800 * np.sin((hour - 6) / 12 * np.pi), 0, None), "wind": 10 + rng.normal(0, 2, len(idx))},
                        index=idx)


def test_features_use_no_future_hours():
    hourly = hourly_frame()
    base = daily_weather_features(hourly)
    cut = pd.Timestamp("2018-06-20")
    later = hourly.copy()
    later.loc[later.index >= cut, ["temp_c", "sw", "wind"]] += 15  # change only day 20 onwards
    changed = daily_weather_features(later)
    before = base.index < cut
    pd.testing.assert_frame_equal(base[before], changed[before])


def test_spell_counts_only_previous_days():
    p = pd.Series([70, 70, 70, 10, 70, 70], index=pd.date_range("2018-06-01", periods=6))
    s = spell_days(p)
    assert s.tolist() == [0, 1, 2, 3, 0, 1]
    p2 = p.copy(); p2.iloc[2] = 0          # today's own P never changes today's spell
    assert spell_days(p2).iloc[2] == s.iloc[2]


def test_spell_is_capped_at_10():
    p = pd.Series([90] * 20, index=pd.date_range("2018-06-01", periods=20))
    assert spell_days(p).max() == 10


def test_training_percentile_leaves_own_year_out():
    idx = pd.date_range("2015-06-01", "2021-06-30", freq="D")
    idx = idx[idx.month == 6]
    h = pd.Series(np.where(idx.year == 2016, 100.0, 0.0), index=idx)
    p = percentile_rank(h)
    assert (p[p.index.year == 2016] == 100).all()   # own year excluded, so it beats every reference value


def toy_frame(years):
    rng = np.random.default_rng(1)
    rows = []
    for y in years:
        for d in pd.date_range(f"{y}-05-01", f"{y}-09-30"):
            x = {f: rng.normal() for f in FEATURES}
            x["event"] = bool(rng.random() < 1 / (1 + np.exp(-(x["h"] * 1.5 - 3))))
            rows.append((d, x))
    return pd.DataFrame([r for _, r in rows], index=pd.DatetimeIndex([d for d, _ in rows]))


def test_fit_refuses_test_years():
    with pytest.raises(TrainingLeakError):
        select_and_fit(toy_frame([2020, 2021, 2022]))


def test_monotonic_gb_never_lowers_risk_when_h_rises():
    fr = toy_frame([2018, 2019])
    m = fit_gb(fr[FEATURES], fr["event"], {"max_depth": 3, "learning_rate": 0.1, "max_iter": 100, "min_samples_leaf": 50})
    row = fr[FEATURES].iloc[[0] * 40].copy()
    row["h"] = np.linspace(-3, 3, 40)
    risk = m.predict_proba(row)[:, 1]
    assert (np.diff(risk) >= -1e-12).all()


def test_operating_threshold_reproduces_alert_count():
    scores = np.random.default_rng(2).random(8568)
    t = operating_threshold(scores, 3672)
    assert int((scores >= t).sum()) == 3672
