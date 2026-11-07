"""Build the JSON the web app reads (every number comes from a script; nothing typed into the UI by hand).

web/data/replay.json  : Abu Dhabi zones, every day May-Sep 2025: heat index peak + hour, local percentile, anomaly, max temp, tier.
web/data/live.json    : tomorrow per zone from the Open-Meteo forecast (past 14 days observed-model for the anomaly).
web/data/evidence.json: headline back-test numbers copied from results/*.json.
"""
from __future__ import annotations

import json
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone
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
    a, p = anomaly(h), percentile_rank(h)
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


def live(rp: RelParams) -> dict:
    out = {"generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M"), "zones": {}}
    for key, (name, lat, lon) in ZONES.items():
        q = urllib.parse.urlencode({"latitude": lat, "longitude": lon, "hourly": "temperature_2m,relative_humidity_2m",
                                    "past_days": 15, "forecast_days": 3, "timezone": "Asia/Dubai"})
        h = json.load(urllib.request.urlopen(f"https://api.open-meteo.com/v1/forecast?{q}", timeout=60))["hourly"]
        fc = pd.DataFrame({"temp_c": h["temperature_2m"], "rh": h["relative_humidity_2m"]}, index=pd.to_datetime(h["time"]))
        hist = hourly(key, lat, lon)                       # 2015-2025 reference for percentiles
        both = pd.concat([hist[hist.index < fc.index.min()], fc])
        tomorrow = (pd.Timestamp.now(tz="Asia/Dubai").normalize() + pd.Timedelta(days=1)).tz_localize(None)
        rows = day_rows(both, rp, keep=lambda d, t=tomorrow: d == t)
        out["zones"][key] = {"name": name, **(rows[0] if rows else {"tier": "Insufficient data"})}
    return out


def main() -> None:
    rp = RelParams(**json.loads((ROOT / "results" / "frozen_params_r4.json").read_text())["params"])
    WEB.mkdir(parents=True, exist_ok=True)
    replay = {key: {"name": name, "days": day_rows(hourly(key, lat, lon), rp, keep=lambda d: d.year == 2025 and SEASON[0] <= d.month <= SEASON[1])}
              for key, (name, lat, lon) in ZONES.items()}
    (WEB / "replay.json").write_text(json.dumps(replay))
    (WEB / "live.json").write_text(json.dumps(live(rp), indent=1))
    ho = json.loads((ROOT / "results" / "holdout_results.json").read_text())
    te = json.loads((ROOT / "results" / "test_results.json").read_text())
    da = json.loads((ROOT / "results" / "dayahead_results.json").read_text())
    ev = {"reports_total": ho["data"]["heat_reports"],
          "holdout": {"regions": 6, "event_days": ho["data"]["event_days"],
                      "r4_sensitivity": ho["rules"]["R4"]["sensitivity"], "r4_ci": ho["rules"]["R4"]["sensitivity_95ci"],
                      "r4_alert_share": ho["rules"]["R4"]["alert_fraction"], "r2_sensitivity": ho["rules"]["R2"]["sensitivity"],
                      "spread_r2": ho["primary_B_alert_share_spread"]["R2"], "spread_r4": ho["primary_B_alert_share_spread"]["R4"]},
          "workplace_trigger": {"r3_minus_r2": te["primary_r3_minus_r2_sensitivity"]["point"], "ci": te["primary_r3_minus_r2_sensitivity"]["95ci"]},
          "fixed_80f_alert_share": te["rules"]["R1 heat index >= 80 F"]["alert_fraction"],
          "dayahead_same_decision": da["same_decision_share"]}
    (WEB / "evidence.json").write_text(json.dumps(ev, indent=1))
    print(json.dumps(json.loads((WEB / "live.json").read_text()), indent=1)[:900])
    print({k: len(v["days"]) for k, v in replay.items()})


if __name__ == "__main__":
    main()
