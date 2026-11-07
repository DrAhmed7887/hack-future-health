"""Select holdout regions by a fixed rule using 2015-2021 report counts only (protocol v3).

Rule: half-degree cells of 2015-2021 environmental-heat reports; drop cells whose report centroid is within 200 km of any
original region centre; rank by count; greedily keep cells whose centroid is > 200 km from every already-kept holdout centre;
keep cells with >= 10 training reports, at most 8. Centre = mean lat/lon of that cell's training reports (2 decimals).
Writes results/holdout_regions.json. Run once, before any holdout weather is fetched.
"""
from __future__ import annotations

import collections
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from heatwarn.data import load_osha_heat_points  # noqa: E402
from heatwarn.regions import REGIONS, haversine_km  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
MIN_REPORTS, MAX_REGIONS, SEP_KM = 10, 8, 200.0


def main() -> None:
    pts = load_osha_heat_points(last_year=2021)
    cells: dict = collections.defaultdict(list)
    for lat, lon, city, state in pts:
        cells[(round(lat * 2) / 2, round(lon * 2) / 2)].append((lat, lon, city, state))
    ranked = sorted(cells.items(), key=lambda kv: (-len(kv[1]), kv[0]))
    kept = []
    for _, rows in ranked:
        if len(rows) < MIN_REPORTS or len(kept) >= MAX_REGIONS:
            break
        clat = round(sum(r[0] for r in rows) / len(rows), 2); clon = round(sum(r[1] for r in rows) / len(rows), 2)
        if any(haversine_km(clat, clon, r.lat, r.lon) <= SEP_KM for r in REGIONS):
            continue
        if any(haversine_km(clat, clon, k["lat"], k["lon"]) <= SEP_KM for k in kept):
            continue
        city = collections.Counter(f"{r[2].title()}, {r[3].title()}" for r in rows).most_common(1)[0][0]
        kept.append({"key": f"h{len(kept)+1}", "name": city, "lat": clat, "lon": clon, "train_reports": len(rows)})
    (ROOT / "results" / "holdout_regions.json").write_text(json.dumps(kept, indent=2))
    print(json.dumps(kept, indent=2))


if __name__ == "__main__":
    main()
