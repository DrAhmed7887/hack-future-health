# G1b: relative rule (R4) — holdout transfer test and Abu Dhabi check

Pre-registration: `docs/protocol_v3_relative.md` (commit f3eefd5; amendment 1 widened the grid on training data only, before any
holdout weather was fetched). Frozen R4 (`results/frozen_params_r4.json`, commit decbf94): heat index ≥ 80 °F AND
[local percentile ≥ 60 (High) OR (≥ 50 AND 14-day anomaly ≥ 3 °F) (Elevated)]. Percentiles from each region's own 2015–2021 weather.

## Training (original 8 regions, 2015–2021)
R4 67.4 % sensitivity at 43 % alert days vs R2 78.4 % at 45 %. **Within the climates it was tuned on, the absolute rule is better.**

## Holdout transfer test (6 unseen regions, 2022–2025, scored once; `results/holdout_results.json`)
3,672 region-days, 86 event days (90 reports). Regions: New Orleans, Philadelphia, McAllen TX, Fort Lauderdale, Braddock PA (Pittsburgh), Kennesaw GA (Atlanta).

| Rule | Sensitivity (95 % CI) | Reported-event PPV | Alert days |
|---|---|---|---|
| R0 calendar | 76.7 % (65.8–86.0) | 3.0 % | 61 % |
| R1 heat index ≥ 80 °F | 98.8 % (95.8–100) | 2.8 % | 82 % |
| R2 absolute (frozen) | 70.9 % (57.1–82.1) | 4.1 % | 40 % |
| **R4 relative (frozen)** | **79.1 % (69.6–87.9)** | 3.8 % | 49 % |

- **Primary A:** R4 − R2 sensitivity = **+8.1 points (95 % CI −6.9 to +24.3)**: not statistically clear, and R4 alerted on more days (49 % vs 40 %).
- **Primary B:** alert-share spread across holdout regions: **R2 82 points (7 % Pittsburgh to 89 % McAllen); R4 25 points (36–60 %).**
- **Pre-registered success criterion met** (R4 not more than 5 points below R2, and smaller spread).

| Holdout region | R2 caught / events (alert share) | R4 caught / events (alert share) |
|---|---|---|
| New Orleans | 5/6 (52 %) | 5/6 (57 %) |
| Philadelphia | 15/24 (17 %) | 21/24 (39 %) |
| McAllen TX | 8/8 (89 %) | 7/8 (60 %) |
| Fort Lauderdale | 25/27 (59 %) | 19/27 (57 %) |
| Pittsburgh area | 1/8 (7 %) | 7/8 (36 %) |
| Atlanta area | 7/13 (18 %) | 9/13 (45 %) |

What it means: absolute thresholds tuned in Texas/Florida go almost silent in cooler cities (Pittsburgh 1 of 8 event days)
and fire almost daily in the hottest (McAllen 89 %). The relative rule keeps alert load in a similar band in every climate
and still caught 79 % of reported event days. Small numbers: 86 event days in total.

Expected (written before running) vs actual: spread smaller — as expected. Sensitivity lower in hot holdouts, higher in
temperate ones — as expected (McAllen 7 vs 8, Fort Lauderdale 19 vs 25; Philadelphia 21 vs 15, Pittsburgh 7 vs 1).
Pooled difference within ±10 points — as expected (+8.1), CI wide.

## Abu Dhabi (descriptive; no outcome data exists; `results/abu_dhabi_tiers.json`)
Share of 2025 days with any alert, R2 absolute → R4 relative (each zone's own May–Sep 2015–2021 climatology, the same
in-season percentile definition as the back-test):

| Zone | May | Jun | Jul | Aug | Sep |
|---|---|---|---|---|---|
| Mussafah | 94 → 74 % | 100 → 30 % | 100 → 48 % | 100 → 26 % | 100 → 67 % |
| Abu Dhabi city | 87 → 68 % | 100 → 27 % | 100 → 55 % | 100 → 52 % | 100 → 80 % |
| Ruwais | 81 → 55 % | 97 → 20 % | 100 → 32 % | 100 → 65 % | 100 → 67 % |
| Al Ain | 94 → 77 % | 100 → 50 % | 100 → 58 % | 100 → 84 % | 100 → 90 % |

- In summer the relative rule separates days again (20–90 % instead of 100 %).
- Outside May–September the model issues no tiers (Ahmed's decision, 7 Nov). An earlier version of this table computed
  percentiles over the whole year and showed about half of December days alerting; that definition was never tested and is
  not deployed (code review, 7 Nov: deployment now uses the tested in-season definition).

## Evidence for location-relative thresholds (`docs/evidence_relative_thresholds.md`; three quotes re-checked on PubMed 7 Nov)
- Anderson & Bell 2009 (PMID 19194300), 107 US communities: larger heterogeneity for absolute than for percentile-based
  temperature estimates "provides evidence for acclimatization."
- Gasparrini 2015 (PMID 26003380): minimum-mortality temperature "varied from roughly the 60th percentile in tropical areas to
  about the 80-90th percentile in temperate regions."
- Anderson & Bell 2011 (PMID 21084239): first heat wave of summer 5.04 % mortality increase vs 2.65 % for later ones.
- No Gulf study derives a local occupational heat-illness threshold (searched 7 Nov).
