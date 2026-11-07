"""Daily job: tomorrow's tier per Abu Dhabi zone -> web/data/live.json. Light: 4 forecast calls, no history download.

Percentiles use web/data/reference.json (each zone's daily max heat index, 2015-2021, built by build_web_data.py).
The anomaly baseline uses the forecast API's past 15 days (model analysis), so it needs no archive call.
On any failure the old live.json is kept; the app then shows "Not enough data" once it is older than 36 h.
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

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "web" / "data"
ZONES = {"mussafah": ("Mussafah", 24.35, 54.50), "adcity": ("Abu Dhabi city", 24.47, 54.37),
         "ruwais": ("Ruwais", 24.11, 52.73), "alain": ("Al Ain", 24.21, 55.74)}
SEASON = (5, 9)


def forecast_hourly(lat: float, lon: float) -> pd.DataFrame:
    q = urllib.parse.urlencode({"latitude": lat, "longitude": lon, "hourly": "temperature_2m,relative_humidity_2m",
                                "past_days": 15, "forecast_days": 3, "timezone": "Asia/Dubai"})
    h = json.load(urllib.request.urlopen(f"https://api.open-meteo.com/v1/forecast?{q}", timeout=60))["hourly"]
    return pd.DataFrame({"temp_c": h["temperature_2m"], "rh": h["relative_humidity_2m"]}, index=pd.to_datetime(h["time"]))


def zone_row(key: str, name: str, lat: float, lon: float, ref: dict, rp: RelParams) -> dict:
    fc = forecast_hourly(lat, lon)
    h_fc = daily_max_heat_index(fc)
    h_ref = pd.Series(ref[key], dtype=float)
    h_ref.index = pd.to_datetime(h_ref.index)
    tomorrow = (pd.Timestamp.now(tz="Asia/Dubai").normalize() + pd.Timedelta(days=1)).tz_localize(None)
    h_all = pd.concat([h_ref, h_fc]).sort_index()
    p = percentile_rank(h_all)
    a = anomaly(h_fc)
    tier = r4_tier(h_fc, p.reindex(h_fc.index), a, rp)
    tmax = fc["temp_c"].groupby(fc.index.normalize()).max()
    hi = pd.Series(heat_index_f(c_to_f(fc["temp_c"]), fc["rh"].to_numpy(dtype=float)), index=fc.index)
    peak = hi.groupby(fc.index.normalize()).idxmax()
    if tomorrow not in h_fc.index or pd.isna(h_fc[tomorrow]):
        return {"name": name, "date": tomorrow.strftime("%Y-%m-%d"), "tier": "Insufficient data"}
    in_season = SEASON[0] <= tomorrow.month <= SEASON[1]
    return {"name": name, "date": tomorrow.strftime("%Y-%m-%d"),
            "heat_index_f": round(float(h_fc[tomorrow]), 1), "heat_index_c": round((float(h_fc[tomorrow]) - 32) * 5 / 9, 1),
            "peak_hour": int(peak[tomorrow].hour) if pd.notna(peak[tomorrow]) else None,
            "percentile": None if pd.isna(p[tomorrow]) else round(float(p[tomorrow])),
            "anomaly_f": None if pd.isna(a[tomorrow]) else round(float(a[tomorrow]), 1),
            "max_temp_c": round(float(tmax[tomorrow]), 1),
            "tier": tier[tomorrow] if in_season else "Outside tested season"}


def main() -> None:
    rp = RelParams(**json.loads((ROOT / "results" / "frozen_params_r4.json").read_text())["params"])
    ref = json.loads((WEB / "reference.json").read_text())
    out = {"generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M"), "zones": {}}
    for key, (name, lat, lon) in ZONES.items():
        out["zones"][key] = zone_row(key, name, lat, lon, ref, rp)
    (WEB / "live.json").write_text(json.dumps(out, indent=1, allow_nan=False))  # NaN would break JSON.parse in the app
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
