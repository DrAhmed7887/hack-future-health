"""Day-ahead sub-study (protocol v2): frozen R2 on forecasts made 24 h earlier vs R2 on observed weather, same region-days.

Anomaly baseline = observed heat index of d-14..d-1 (known when the alert is issued the evening before; the d-1 maximum
is normally reached by mid-afternoon). Output: results/dayahead_results.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from heatwarn.data import WEATHER_DIR, build_frame  # noqa: E402
from heatwarn.metrics import block_bootstrap, confusion  # noqa: E402
from heatwarn.rules import Params, r2_weather  # noqa: E402
from heatwarn.signals import daily_max_heat_index  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    p2 = Params(**json.loads((ROOT / "results" / "frozen_params.json").read_text())["r2"]["params"])
    full, _ = build_frame(last_year=2025)
    parts = []
    for region, g in full.groupby("region", sort=False):
        fc = pd.read_csv(WEATHER_DIR / f"dayahead_{region}.csv", parse_dates=["time"], index_col="time")
        h_fc = daily_max_heat_index(fc)
        g = g[g.index.year >= 2024].copy()
        g["h_fc"] = h_fc.reindex(g.index)
        g["baseline"] = g["h"] - g["a"]               # observed mean of d-14..d-1
        g["a_fc"] = g["h_fc"] - g["baseline"]
        parts.append(g)
    t = pd.concat(parts)
    t = t[t["h_fc"].notna()]
    t["obs"] = r2_weather(t["h"], t["a"], p2)
    t["fc"] = r2_weather(t["h_fc"], t["a_fc"], p2)
    res = {"region_days": len(t), "event_days": int(t["event"].sum()),
           "observed": confusion(t["obs"], t["event"]), "day_ahead": confusion(t["fc"], t["event"]),
           "same_decision_share": float((t["obs"] == t["fc"]).mean()),
           "heat_index_forecast_error_f": {"mean": float((t["h_fc"] - t["h"]).mean()),
                                           "mean_abs": float((t["h_fc"] - t["h"]).abs().mean())}}
    for k in ("obs", "fc"):
        res["observed" if k == "obs" else "day_ahead"]["sensitivity_95ci"] = list(
            block_bootstrap(t, lambda s, k=k: confusion(s[k], s["event"])["sensitivity"]))
    (ROOT / "results" / "dayahead_results.json").write_text(json.dumps(res, indent=2, default=float))
    print(json.dumps(res, indent=2, default=float))


if __name__ == "__main__":
    main()
