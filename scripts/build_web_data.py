"""Build the JSON the web app reads (every number comes from a script; nothing typed into the UI by hand).

web/data/replay.json  : Abu Dhabi zones, every day May-Sep 2025: heat index peak + hour, local percentile, anomaly, max temp, tier.
web/data/reference.json: each zone's daily max heat index 2015-2021 (percentile reference for scripts/refresh_live.py).
web/data/evidence.json: headline back-test numbers copied from results/*.json.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from heatwarn.heat_index import c_to_f, heat_index_f  # noqa: E402
from heatwarn.relative import RelParams, percentile_rank, r4_tier  # noqa: E402
from heatwarn.signals import anomaly, daily_max_heat_index  # noqa: E402
from scripts.abu_dhabi_tiers import ZONES, hourly  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "web" / "data"
SEASON = (5, 9)


def peak_hour(df: pd.DataFrame) -> pd.Series:
    hi = pd.Series(heat_index_f(c_to_f(df["temp_c"]), df["rh"].to_numpy(dtype=float)), index=df.index)
    return hi.groupby(df.index.normalize()).idxmax().map(lambda t: t.hour if pd.notna(t) else None)


def day_rows(df: pd.DataFrame, rp: RelParams, keep) -> list[dict]:
    h = daily_max_heat_index(df)
    a = anomaly(h)                                   # full-year series, as in the back-test
    in_season = h[(h.index.month >= SEASON[0]) & (h.index.month <= SEASON[1])]
    p = percentile_rank(in_season).reindex(h.index)  # percentiles over May-Sep only, as in the back-test (review MED 8)
    tier = r4_tier(h, p, a, rp)
    tmax = df["temp_c"].groupby(df.index.normalize()).max()
    ph = peak_hour(df)
    rows = []
    for d in h.index:
        if not keep(d):
            continue
        in_season = SEASON[0] <= d.month <= SEASON[1]
        rows.append({"date": d.strftime("%Y-%m-%d"), "heat_index_f": round(float(h[d]), 1), "heat_index_c": round((float(h[d]) - 32) * 5 / 9, 1),
                     "peak_hour": None if ph.get(d) is None or pd.isna(ph.get(d)) else int(ph.get(d)), "percentile": None if pd.isna(p[d]) else round(float(p[d])),
                     "anomaly_f": None if pd.isna(a[d]) else round(float(a[d]), 1), "max_temp_c": round(float(tmax[d]), 1),
                     "tier": tier[d] if in_season else "Outside tested season"})
    return rows


def main() -> None:
    rp = RelParams(**json.loads((ROOT / "results" / "frozen_params_r4.json").read_text())["params"])
    WEB.mkdir(parents=True, exist_ok=True)
    replay = {key: {"name": name, "days": day_rows(hourly(key, lat, lon), rp, keep=lambda d: d.year == 2025 and SEASON[0] <= d.month <= SEASON[1])}
              for key, (name, lat, lon) in ZONES.items()}
    (WEB / "replay.json").write_text(json.dumps(replay))
    ref = {}
    for key, (name, lat, lon) in ZONES.items():
        h = daily_max_heat_index(hourly(key, lat, lon))
        h = h[(h.index.year >= 2015) & (h.index.year <= 2021) & (h.index.month >= SEASON[0]) & (h.index.month <= SEASON[1])].dropna()
        ref[key] = {d.strftime("%Y-%m-%d"): round(float(v), 2) for d, v in h.items()}
    (WEB / "reference.json").write_text(json.dumps(ref))
    ho = json.loads((ROOT / "results" / "holdout_results.json").read_text())
    te = json.loads((ROOT / "results" / "test_results.json").read_text())
    da = json.loads((ROOT / "results" / "dayahead_results.json").read_text())
    ev = {"reports_total": ho["data"]["heat_reports"],
          "holdout": {"regions": 6, "event_days": ho["data"]["event_days"],
                      "r4_sensitivity": ho["rules"]["R4"]["sensitivity"], "r4_ci": ho["rules"]["R4"]["sensitivity_95ci"],
                      "r4_alert_share": ho["rules"]["R4"]["alert_fraction"], "r2_sensitivity": ho["rules"]["R2"]["sensitivity"],
                      "spread_r2": ho["primary_B_alert_share_spread"]["R2"], "spread_r4": ho["primary_B_alert_share_spread"]["R4"]},
          "workplace_trigger": {"r3_minus_r2": te["primary_r3_minus_r2_sensitivity"]["point"], "ci": te["primary_r3_minus_r2_sensitivity"]["95ci"]},
          "fixed_80f_alert_share": ho["rules"]["R1"]["alert_fraction"],  # same unseen regions as the R4 figures
          "dayahead_same_decision": da["same_decision_share"]}
    (WEB / "evidence.json").write_text(json.dumps(ev, indent=1))
    print({k: len(v["days"]) for k, v in replay.items()})


if __name__ == "__main__":
    main()
