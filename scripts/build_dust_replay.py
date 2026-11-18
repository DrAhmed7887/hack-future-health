"""Build web/data/dust_replay.json: daily mean PM10 per Abu Dhabi zone, May-Sep 2025 (v4, proposal D1-D3).

Source: Open-Meteo Air Quality API (CAMS global, CC BY 4.0), hourly pm10, local day (Asia/Dubai).
A day with fewer than 18 valid hours is stored as null. Run once; the file is committed.
"""
from __future__ import annotations

import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from heatwarn.dust import daily_pm10  # noqa: E402
from scripts.refresh_live import ZONES  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
START, END = "2025-05-01", "2025-09-30"


def hourly_pm10(lat: float, lon: float, start: str, end: str) -> pd.Series:
    q = urllib.parse.urlencode({"latitude": lat, "longitude": lon, "hourly": "pm10",
                                "start_date": start, "end_date": end, "timezone": "Asia/Dubai"})
    h = json.load(urllib.request.urlopen(f"https://air-quality-api.open-meteo.com/v1/air-quality?{q}", timeout=60))["hourly"]
    return pd.Series(h["pm10"], index=pd.to_datetime(h["time"]), dtype=float)


def main() -> None:
    out = {"source": "Open-Meteo Air Quality API (CAMS global), daily mean of hourly PM10, ug/m3", "zones": {}}
    for key, (_name, lat, lon) in ZONES.items():
        d = daily_pm10(hourly_pm10(lat, lon, START, END))
        out["zones"][key] = {k.strftime("%Y-%m-%d"): (None if pd.isna(v) else round(float(v), 1)) for k, v in d.items()}
    (ROOT / "web" / "data" / "dust_replay.json").write_text(json.dumps(out, indent=0, allow_nan=False))
    for key, days in out["zones"].items():
        vals = [v for v in days.values() if v is not None]
        print(key, len(vals), "days, >150:", sum(v > 150 for v in vals), ">250:", sum(v > 250 for v in vals), "max", max(vals))


if __name__ == "__main__":
    main()
