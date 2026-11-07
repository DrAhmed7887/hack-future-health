"""Load OSHA heat reports and cached weather into one daily frame per region.

`last_year` filters at load time, so the tuning step never reads test-year rows.
"""
from __future__ import annotations

import csv
from pathlib import Path

import pandas as pd

from heatwarn.regions import REGIONS, assign_region
from heatwarn.signals import anomaly, daily_max_heat_index, workplace_signal

ROOT = Path(__file__).resolve().parents[1]
OSHA_CSV = ROOT / "data" / "raw" / "osha_sir" / "January2015toNovember2025.csv"
WEATHER_DIR = ROOT / "data" / "interim"
HEAT_EVENT_CODES = {"531", "5310", "5311", "5312"}  # OIICS: exposure to environmental heat
SEASON = (5, 9)  # May-September


def load_osha_heat(last_year: int, path: Path = OSHA_CSV) -> tuple[pd.DataFrame, dict]:
    csv.field_size_limit(10**9)
    rows, stats = [], {"heat_reports": 0, "no_latlon": 0, "outside_regions": 0}
    with path.open(encoding="latin-1", newline="") as f:
        for r in csv.DictReader(f):
            if r["Event"].strip() not in HEAT_EVENT_CODES:
                continue
            date = pd.to_datetime(r["EventDate"], format="%m/%d/%Y")
            if date.year > last_year:
                continue
            stats["heat_reports"] += 1
            if not (r["Latitude"] and r["Longitude"]):
                stats["no_latlon"] += 1
                continue
            region = assign_region(float(r["Latitude"]), float(r["Longitude"]))
            if region is None:
                stats["outside_regions"] += 1
                continue
            workers = float(r["Hospitalized"] or 0) or 1.0
            rows.append({"date": date, "region": region, "workers": workers, "naics2": r["Primary NAICS"][:2]})
    return pd.DataFrame(rows), stats


def load_daily_heat(key: str, last_year: int) -> pd.Series:
    w = pd.read_csv(WEATHER_DIR / f"weather_{key}.csv", parse_dates=["time"], index_col="time")
    w = w[w.index.year <= last_year]
    return daily_max_heat_index(w)


def build_frame(last_year: int) -> tuple[pd.DataFrame, dict]:
    reports, stats = load_osha_heat(last_year)
    parts = []
    for reg in REGIONS:
        h = load_daily_heat(reg.key, last_year)
        idx = pd.date_range(h.index.min(), h.index.max(), freq="D")
        h = h.reindex(idx)
        mine = reports[reports["region"] == reg.key] if len(reports) else reports
        counts = mine.groupby("date").size().reindex(idx, fill_value=0) if len(mine) else pd.Series(0, index=idx)
        workers = mine.groupby("date")["workers"].sum().reindex(idx, fill_value=0) if len(mine) else pd.Series(0.0, index=idx)
        df = pd.DataFrame({"region": reg.key, "h": h, "a": anomaly(h), "w": workplace_signal(counts),
                           "reports": counts, "workers": workers}, index=idx)
        df["event"] = df["reports"] > 0
        parts.append(df[(df.index.month >= SEASON[0]) & (df.index.month <= SEASON[1])])
    frame = pd.concat(parts)
    frame.index.name = "date"
    stats["assigned_reports"] = int(frame["reports"].sum())
    return frame, stats
