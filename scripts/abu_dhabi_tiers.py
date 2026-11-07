"""Descriptive: frozen R2 and R4 tiers on Abu Dhabi zones, 2025 (no outcome data exists). Protocol v3 endpoint 5.

Zones (ERA5 points): Mussafah industrial, Abu Dhabi city, Ruwais (Al Dhafra industrial), Al Ain (inland).
ICAD from the protocol was replaced by Al Ain: ICAD falls in the same ERA5 grid cell as Mussafah.
Climatology: each zone's own ERA5 2015-2021. Output: results/abu_dhabi_tiers.json + data/interim/weather_ad_<key>.csv
"""
from __future__ import annotations

import csv
import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from heatwarn.relative import RelParams, percentile_rank, r4_tier  # noqa: E402
from heatwarn.rules import Params, r2_weather  # noqa: E402
from heatwarn.signals import anomaly, daily_max_heat_index  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
ZONES = {"mussafah": ("Mussafah", 24.35, 54.50), "adcity": ("Abu Dhabi city", 24.47, 54.37),
         "ruwais": ("Ruwais", 24.11, 52.73), "alain": ("Al Ain", 24.21, 55.74)}


def hourly(key: str, lat: float, lon: float) -> pd.DataFrame:
    path = ROOT / "data" / "interim" / f"weather_ad_{key}.csv"
    if not path.exists():
        q = urllib.parse.urlencode({"latitude": lat, "longitude": lon, "start_date": "2015-01-01", "end_date": "2025-12-31",
                                    "hourly": "temperature_2m,relative_humidity_2m", "timezone": "Asia/Dubai"})
        h = json.load(urllib.request.urlopen(f"https://archive-api.open-meteo.com/v1/archive?{q}", timeout=120))["hourly"]
        with path.open("w", newline="") as f:
            w = csv.writer(f); w.writerow(["time", "temp_c", "rh"])
            w.writerows(zip(h["time"], h["temperature_2m"], h["relative_humidity_2m"]))
    return pd.read_csv(path, parse_dates=["time"], index_col="time")


def main() -> None:
    p2 = Params(**json.loads((ROOT / "results" / "frozen_params.json").read_text())["r2"]["params"])
    p4 = RelParams(**json.loads((ROOT / "results" / "frozen_params_r4.json").read_text())["params"])
    out = {}
    for key, (name, lat, lon) in ZONES.items():
        h = daily_max_heat_index(hourly(key, lat, lon))
        a, p = anomaly(h), percentile_rank(h)
        d = pd.DataFrame({"r2": r2_weather(h, a, p2), "r4": r4_tier(h, p, a, p4), "h": h})
        d = d[d.index.year == 2025]
        out[name] = {int(m): {"median_heat_index_f": round(float(g["h"].median()), 1),
                              "R2_alert_share": round(float(g["r2"].fillna(False).astype(bool).mean()), 2),
                              "R4_high_share": round(float((g["r4"] == "High").mean()), 2),
                              "R4_any_alert_share": round(float(g["r4"].isin(["High", "Elevated"]).mean()), 2)}
                     for m, g in d.groupby(d.index.month)}
    (ROOT / "results" / "abu_dhabi_tiers.json").write_text(json.dumps(out, indent=1))
    for name, months in out.items():
        print(name, " ".join(f"{m}:{v['R2_alert_share']:.0%}/{v['R4_any_alert_share']:.0%}" for m, v in months.items()))


if __name__ == "__main__":
    main()
