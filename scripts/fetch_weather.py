"""Download hourly ERA5 temperature and humidity (Open-Meteo Historical Weather API) for each region.

Output: data/interim/weather_<key>.csv (local time). Re-run is idempotent; cached files are kept unless --force.
Source declared in docs/data_card.md. Open-Meteo data are CC BY 4.0 (attribution required).
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from heatwarn.regions import REGIONS  # noqa: E402
from heatwarn.data import holdout_regions  # noqa: E402

URL = "https://archive-api.open-meteo.com/v1/archive"
START, END = "2015-04-01", "2025-09-30"
OUT = Path(__file__).resolve().parents[1] / "data" / "interim"


def fetch(reg) -> dict:
    q = urllib.parse.urlencode({
        "latitude": reg.lat, "longitude": reg.lon, "start_date": START, "end_date": END,
        "hourly": "temperature_2m,relative_humidity_2m", "timezone": reg.tz,
    })
    with urllib.request.urlopen(f"{URL}?{q}", timeout=120) as r:
        data = json.load(r)
    if "hourly" not in data:
        raise RuntimeError(f"{reg.key}: unexpected response {str(data)[:200]}")
    return data


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--holdout", action="store_true", help="fetch the holdout regions instead")
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    for reg in (holdout_regions() if a.holdout else REGIONS):
        path = OUT / f"weather_{reg.key}.csv"
        if path.exists() and not a.force:
            print(f"cached {path.name}")
            continue
        h = fetch(reg)["hourly"]
        with path.open("w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["time", "temp_c", "rh"])
            w.writerows(zip(h["time"], h["temperature_2m"], h["relative_humidity_2m"]))
        print(f"wrote {path.name}: {len(h['time'])} hours")
        time.sleep(2)


if __name__ == "__main__":
    main()
