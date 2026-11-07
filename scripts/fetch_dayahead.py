"""Download day-ahead forecasts (value forecast 24 h before valid time) from the Open-Meteo Previous Runs API.

Seasons 2024-2025 only: humidity at a 24 h lead is archived from 2024 (audited 7 Nov 2026, Houston: 2022-2023 temperature
only). Model: Open-Meteo default ("best_match"). Output: data/interim/dayahead_<key>.csv, local time.
"""
from __future__ import annotations

import csv
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from heatwarn.regions import REGIONS  # noqa: E402

URL = "https://previous-runs-api.open-meteo.com/v1/forecast"
OUT = Path(__file__).resolve().parents[1] / "data" / "interim"
VARS = "temperature_2m_previous_day1,relative_humidity_2m_previous_day1"


def main() -> None:
    for reg in REGIONS:
        path = OUT / f"dayahead_{reg.key}.csv"
        rows = []
        for year in (2024, 2025):
            q = urllib.parse.urlencode({"latitude": reg.lat, "longitude": reg.lon, "start_date": f"{year}-05-01",
                                        "end_date": f"{year}-09-30", "hourly": VARS, "timezone": reg.tz})
            with urllib.request.urlopen(f"{URL}?{q}", timeout=120) as r:
                h = json.load(r)["hourly"]
            rows += zip(h["time"], h["temperature_2m_previous_day1"], h["relative_humidity_2m_previous_day1"])
            time.sleep(2)
        with path.open("w", newline="") as f:
            w = csv.writer(f); w.writerow(["time", "temp_c", "rh"]); w.writerows(rows)
        print(f"wrote {path.name}: {len(rows)} hours, missing temp {sum(r[1] is None for r in rows)}, missing rh {sum(r[2] is None for r in rows)}")


if __name__ == "__main__":
    main()
