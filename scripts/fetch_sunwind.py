"""Download hourly ERA5 shortwave radiation and 10 m wind (Open-Meteo Historical Weather API), protocol v4.

Output: data/interim/sunwind_<key>.csv (local time): time, sw (W/m2, mean of the preceding hour), wind (km/h).
Regions: the 8 original, the 6 holdout and the 4 Abu Dhabi zones. Weather only; no outcomes are read.
Open-Meteo data are CC BY 4.0.
"""
from __future__ import annotations

import csv
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from heatwarn.data import holdout_regions  # noqa: E402
from heatwarn.regions import REGIONS  # noqa: E402

URL = "https://archive-api.open-meteo.com/v1/archive"
OUT = Path(__file__).resolve().parents[1] / "data" / "interim"
AD_ZONES = {"ad_mussafah": (24.35, 54.50), "ad_adcity": (24.47, 54.37), "ad_ruwais": (24.11, 52.73), "ad_alain": (24.21, 55.74)}


def fetch(lat: float, lon: float, tz: str, start: str, end: str) -> dict:
    q = urllib.parse.urlencode({"latitude": lat, "longitude": lon, "start_date": start, "end_date": end,
                                "hourly": "shortwave_radiation,wind_speed_10m", "timezone": tz})
    for attempt in range(8):
        try:
            with urllib.request.urlopen(f"{URL}?{q}", timeout=180) as r:
                data = json.load(r)
            break
        except urllib.error.HTTPError as e:
            if e.code != 429 or attempt == 7:
                raise
            wait = 90 * (attempt + 1)
            print(f"429 rate limit; waiting {wait} s", flush=True)
            time.sleep(wait)
    if "hourly" not in data:
        raise RuntimeError(f"unexpected response {str(data)[:200]}")
    return data["hourly"]


def main() -> None:
    jobs = [(r.key, r.lat, r.lon, r.tz, "2015-04-01", "2025-09-30") for r in (*REGIONS, *holdout_regions())]
    jobs += [(k, lat, lon, "Asia/Dubai", "2015-01-01", "2025-12-31") for k, (lat, lon) in AD_ZONES.items()]
    for key, lat, lon, tz, start, end in jobs:
        path = OUT / f"sunwind_{key}.csv"
        if path.exists():
            print(f"cached {path.name}")
            continue
        h = fetch(lat, lon, tz, start, end)
        with path.open("w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["time", "sw", "wind"])
            w.writerows(zip(h["time"], h["shortwave_radiation"], h["wind_speed_10m"]))
        print(f"wrote {path.name}: {len(h['time'])} hours")
        time.sleep(20)


if __name__ == "__main__":
    main()
