"""Day-ahead check for the deployed rule R4 with a real-time baseline (code review MED 6; frozen rule, no tuning, post hoc).

For each original region, 2024-2025 May-Sep:
- tomorrow's heat index from the forecast made 24 h earlier (Previous Runs API, data/interim/dayahead_<key>.csv);
- percentile against the region's ERA5 May-Sep 2015-2021 days (the tested reference);
- 14-day anomaly baseline from Open-Meteo's Historical Forecast API (first hours of each model run, published in near real
  time), so every input exists the evening before. ERA5 (days-late) is used only for the observed comparison.
Output: results/dayahead_r4_results.json
"""
from __future__ import annotations

import csv
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from heatwarn.data import WEATHER_DIR, build_frame  # noqa: E402
from heatwarn.metrics import block_bootstrap, confusion  # noqa: E402
from heatwarn.regions import REGIONS  # noqa: E402
from heatwarn.relative import RelParams, percentile_rank, r4_relative  # noqa: E402
from heatwarn.signals import daily_max_heat_index  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]


def hist_forecast(reg) -> pd.DataFrame:
    path = WEATHER_DIR / f"histfc_{reg.key}.csv"
    if not path.exists():
        q = urllib.parse.urlencode({"latitude": reg.lat, "longitude": reg.lon, "start_date": "2024-04-01", "end_date": "2025-09-30",
                                    "hourly": "temperature_2m,relative_humidity_2m", "timezone": reg.tz})
        h = json.load(urllib.request.urlopen(f"https://historical-forecast-api.open-meteo.com/v1/forecast?{q}", timeout=120))["hourly"]
        with path.open("w", newline="") as f:
            w = csv.writer(f); w.writerow(["time", "temp_c", "rh"])
            w.writerows(zip(h["time"], h["temperature_2m"], h["relative_humidity_2m"]))
        time.sleep(2)
    return pd.read_csv(path, parse_dates=["time"], index_col="time")


def main() -> None:
    rp = RelParams(**json.loads((ROOT / "results" / "frozen_params_r4.json").read_text())["params"])
    full, _ = build_frame(last_year=2025)
    parts = []
    for reg in REGIONS:
        g = full[full["region"] == reg.key]
        ref = g[g.index.year <= 2021]["h"]
        g = g[g.index.year >= 2024].copy()
        h_fc = daily_max_heat_index(pd.read_csv(WEATHER_DIR / f"dayahead_{reg.key}.csv", parse_dates=["time"], index_col="time"))
        h_hf = daily_max_heat_index(hist_forecast(reg))
        h_hf = h_hf.reindex(pd.date_range(h_hf.index.min(), h_hf.index.max(), freq="D"))
        baseline = h_hf.shift(1).rolling(14, min_periods=10).mean()
        g["h_fc"] = h_fc.reindex(g.index)
        g["a_fc"] = g["h_fc"] - baseline.reindex(g.index)
        p_all = percentile_rank(pd.concat([ref, g["h_fc"]]))
        g["p_fc"] = p_all.iloc[len(ref):].to_numpy()
        parts.append(g)
    t = pd.concat(parts)
    t = t[t["h_fc"].notna()]
    t["obs"] = r4_relative(t["h"], t["p"], t["a"], rp)
    t["fc"] = r4_relative(t["h_fc"], t["p_fc"], t["a_fc"], rp)
    both = t["obs"].notna() & t["fc"].notna()
    t = t[both]
    res = {"rule": "R4 (deployed)", "region_days": len(t), "event_days": int(t["event"].sum()),
           "observed": confusion(t["obs"], t["event"]), "day_ahead": confusion(t["fc"], t["event"]),
           "same_decision_share": float((t["obs"] == t["fc"]).mean())}
    for k, name in (("obs", "observed"), ("fc", "day_ahead")):
        res[name]["sensitivity_95ci"] = list(block_bootstrap(t, lambda s, k=k: confusion(s[k], s["event"])["sensitivity"]))
    (ROOT / "results" / "dayahead_r4_results.json").write_text(json.dumps(res, indent=2, default=float))
    print(json.dumps({k: (v if not isinstance(v, dict) else {kk: v[kk] for kk in ("sensitivity", "sensitivity_95ci", "alert_fraction", "reported_event_ppv")}) for k, v in res.items()}, indent=1, default=float))


if __name__ == "__main__":
    main()
