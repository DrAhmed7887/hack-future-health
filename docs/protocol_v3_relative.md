# Protocol v3 addendum: relative (location-calibrated) rule and holdout-region transfer test

Pre-registered 7 Nov 2026, committed before any holdout-region weather is fetched or any holdout outcome is joined to weather.
Reason: the frozen absolute rule R2 puts every Abu Dhabi day from June to September in the top tier
(`docs/g1_results.md`, transfer check). Ahmed chose to test a relative rule (7 Nov).

## What has already been seen (disclosure)
- 2015–2021 and 2022–2025 outcomes for the original 8 regions (scored with R0–R3).
- Report counts by half-degree cell for all years (7 Nov, before G0), including some holdout cities (e.g. Philadelphia: 24
  reports 2015–2025). Holdout weather has never been fetched, and holdout outcomes have never been joined to weather or scored.

## Holdout regions (fixed rule, `scripts/select_new_regions.py`, output `results/holdout_regions.json`)
Half-degree cells ranked by 2015–2021 counts; cells within 200 km of an original centre dropped; kept cells > 200 km apart;
≥ 10 training reports; max 8. Result: New Orleans LA, Philadelphia PA, McAllen TX, Fort Lauderdale FL, Braddock PA
(Pittsburgh area), Kennesaw GA (Atlanta area). Centre = mean of the cell's training-report coordinates. Assignment: nearest
holdout centre within 100 km. Timezones: Central for LA/TX, Eastern otherwise.

## Relative rule R4
- **Local climatology:** for region r and day d, P(d) = percentile rank (0–100) of H(d) among reference daily max heat index
  values of region r on calendar days within ±15 days of d's day of year, reference years 2015–2021. For a training day in year
  y, year y is left out of the reference (no in-sample percentile). Test-year days use all of 2015–2021.
- **Rule:** alert if H ≥ 80 °F (absolute floor; OSHA NEP heat priority day) AND [P ≥ p_high OR (P ≥ p_low AND A ≥ a)].
  Tier: High if P ≥ p_high, else Elevated. A = the existing 14-day anomaly (°F).
- **Grid:** p_high ∈ {80, 85, 90, 95}, p_low ∈ {60, 70, 80} (p_low < p_high), a ∈ {3, 5, 7, 9}.
- **Operating point:** same rule as v2: highest training sensitivity with alert days ≤ 50 % of R1's training alert days,
  ties to fewer alert days. Tuned on the original 8 regions, 2015–2021 only. Frozen and committed before scoring.

## Endpoints (holdout regions, 2022–2025, scored once)
1. **Primary A:** sensitivity of R4 minus sensitivity of frozen R2 (block bootstrap by region-season, 95 % CI).
2. **Primary B:** spread of alert share across the 6 holdout regions (max − min) for R4 vs R2.
3. Success criterion for using R4 in the Abu Dhabi app: R4's sensitivity point estimate no more than 5 points below R2's
   **and** its alert-share spread smaller. If it fails, the app keeps absolute tiers and says that every summer day is High.
4. Secondary (descriptive): reported-event PPV, alert days, episodes, per-region results; R4 on the original 8 regions'
   test years (already-seen data, labelled exploratory).
5. **Abu Dhabi (descriptive, no outcomes):** share of days per tier by month, 2025, for 4 zones (Mussafah, ICAD, Ruwais,
   Abu Dhabi city), climatology from ERA5 2015–2021 at each zone.

## Power warning (stated before running)
The holdout regions had 10–17 training reports each over 7 years, so 2022–2025 will likely give roughly 30–60 event days in
total. Confidence intervals will be wide; a null difference is likely uninformative.

## Expected results (written before running)
- R2 alert share in holdouts varies a lot with climate (high in McAllen/New Orleans/Fort Lauderdale, low in Pittsburgh and
  Philadelphia); R4's spread is smaller by construction.
- R4 sensitivity: lower than R2 in the hottest holdouts, higher in the temperate ones; pooled difference within ±10 points
  with a wide CI.
- Abu Dhabi: R4 alerts on a minority of summer days (roughly 10–30 %), concentrated in the hottest spells.

## Unit tests written before the code
- Percentile rank uses only reference years, and a training day's own year is left out.
- A day hotter than every reference value gets P = 100; colder than all gets P = 0.
- H below 80 °F never alerts, whatever P is.
- Tuning still refuses rows with year ≥ 2022.
