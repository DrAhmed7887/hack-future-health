# Back-test protocol v2 (pre-registered before any result is computed)

Status: v2, 7 Nov 2026, after an independent stress test (GPT-6 Astra via Azure; findings checked against the data and the
Open-Meteo docs before adoption, see "Changes from v1"). Items marked **[SIGN]** need Ahmed's sign-off against
`docs/evidence_pack.md`. Once the test years are scored, any change is logged here with the reason, and the test years then
count as a development set.

## Question
Do weather plus recent workplace incident reports flag the days on which **reported** work-related heat hospitalisations
happen, with fewer alert days than the fixed rules used today?

What it is: a retrospective check of a **regional** early-warning rule on real US outcomes.
What it is not: individual risk prediction, Abu Dhabi calibration, or proof that alerts prevent illness.

## Data (all public, declared)
| Signal | Source | Role | Notes |
|---|---|---|---|
| Work-related heat hospitalisations | OSHA Severe Injury Reports 1 Jan 2015 – 30 Nov 2025 (`January2015toNovember2025.zip`, sha256 `a3f7f434e200fb956131f12277378e592993a25db3f328716fbece106f846bb0`, downloaded 7 Nov 2026). US government data | Outcome **and** (lagged) workplace signal | OIICS event 531/5310/5311/5312 "Exposure to environmental heat": 2,628 reports, 2,627 with lat/lon, all with Hospitalized ≥ 1 (2,625 × 1, 3 × 2), no duplicate IDs (checked 7 Nov). Incident date (`EventDate`) used. Federal-OSHA states only (CA, AZ, WA and other state-plan states missing); hospitalised cases only; heavily under-reported. |
| Observed weather | Open-Meteo Historical Weather API (ERA5 reanalysis), hourly temperature and relative humidity | Environmental signal | One point per region (region centre); this does not represent every worksite in the region. |
| Day-ahead forecast | Open-Meteo Previous Runs API, `*_previous_day1` (value forecast 24 h before valid time) | Sub-study only | Checked 7 Nov: temperature available 2021–2025; humidity returned for Jul 2025 but not for Jul 2021–2023 or Jan 2024. Exact coverage audited per region before use. The "Historical Forecast API" is **not** used for lead time: it stitches the first hours of each run (near-observed). |

## Units and events
- **Regions:** chosen from **2015–2021 counts only** (half-degree cells with the most heat reports): Dallas, Orlando, Houston,
  Tampa, Kansas City, San Antonio, Jacksonville, Oklahoma City (+ Pasadena TX merged into Houston). Each report is assigned to the
  **nearest** region centre within **[SIGN] 100 km**, so no report counts twice. A map of assignments is published.
- **Season:** 1 May – 30 Sep.
- **Event (region-day):** at least one environmental-heat hospitalisation with that incident date in the region. Counts
  (workers, reports) are reported alongside the binary label.

## Signals and the frozen rule
- **H** = daily maximum of the hourly heat index (NWS Rothfusz regression with its published adjustments, computed from the
  same hour's temperature and humidity; below 80 °F the simple Steadman formula, per NWS). Not WBGT.
- **A** = recent-weather anomaly: H minus the mean H of the previous 14 days (days d-14 … d-1 only). Named honestly: this is
  weather history, **not** a measure of anyone's acclimatisation.
- **W** = workplace signal: number of heat hospitalisation reports in the region with incident dates d-3 … d-1. Assumes the
  regulator receives reports within 24 h (29 CFR 1904.39 requires hospitalisations be reported within 24 h). Abu Dhabi
  analogue: incident notification to the regulator (to verify).

Rules compared (primary comparison = R3 vs R2):
- **R0 Calendar:** every day 15 Jun – 15 Sep (analogue of the UAE midday break season).
- **R1 Fixed heat index:** H ≥ 80 °F (OSHA NEP heat priority day).
- **R2 Weather model:** H ≥ T_high, OR (H ≥ T_low AND A ≥ a).
- **R3 Weather + workplace:** R2 OR (H ≥ T_low AND W ≥ 1).

Tuning (2015–2021 only): grid T_low ∈ {80, 85, 90} °F, T_high ∈ {95, 100, 103} °F, a ∈ {3, 5, 7, 9} °F. The operating point is the
grid point with the highest training sensitivity whose alert days are ≤ **[SIGN] 50 %** of R1's training alert days. Grid and
rule are frozen in `scripts/` before the test years are loaded.

## Split
Tune on 2015–2021 (observed weather). Score once on 2022–2025 (observed weather). Day-ahead sub-study: rerun the frozen rule on
day-ahead forecasts for the region-summers where they exist; report how much sensitivity and alert days change.

## Metrics (from `scripts/backtest.py`; every number in README, slides and video comes from its output)
- **Primary:** sensitivity on 2022–2025 at the training-selected alert budget, R3 vs R2 vs R1 vs R0.
- Counts: eligible region-days, event days, prevalence, missing days, TP/FP/FN/TN, alert fraction.
- **Reported-event PPV** and **alerts without a recorded event** (not "false alarms").
- Alert burden: alert days, alert **episodes** (consecutive runs), longest run.
- Uncertainty: 95 % intervals by block bootstrap over region-seasons (heat days are correlated).
- Results per region; **coverage and subgroup performance** by industry (NAICS 23, 48–49, 56). Not a fairness claim.
- **Action window:** the alert is designed to be issued the evening before (18:00) for a 07:00 shift = 13 h. This is a design
  property, reported as such, not a measured lead time. Measured lead-time claims come only from the day-ahead sub-study.
- Missing inputs: (a) humidity missing → status "insufficient data", never a lower tier; (b) 20 % of days missing at random;
  (c) 3-day outage during the hottest week of each season; (d) W unavailable (reports delayed) → R3 falls back to R2, labelled.

All other comparisons (85 °F screen, single industries, months) are **secondary/exploratory** and labelled so.

## Honesty notes (go into README limitations, not into headline numbers)
- Sensitivity is for **reported** hospitalisations. Under-reporting is large (Illinois linkage: 25.1 % of non-fatal work
  illnesses reported; not a heat-specific or national correction factor). If recorded events are real and missing ones are the
  only label error, reported-event PPV understates true PPV; this is a conditional argument, not a guarantee.
- US data. Abu Dhabi use needs local shadow-mode validation.
- New/returning-worker rules are guideline-based and **not** tested here (2 of 2,628 narratives mention job tenure).

## Expected results (written before running, 7 Nov)
- R0: high sensitivity, many alert days. R1 fires on most summer days in TX/FL, close to R0.
- R2: fewer alert days than R1 by design; sensitivity lower than R1.
- R3: W adds sensitivity on clustered days (several reports in a heatwave); gain expected to be small because most event days
  have a single report.
- If R3 does not beat R2 on the primary metric, we say so.

## Unit tests written before the code
- H from 35 °C / 60 % RH matches the NWS calculator value (to ±1 °F).
- A uses only d-14 … d-1 (a test fails if day d leaks in).
- W uses only d-3 … d-1 (same).
- Region assignment: a report equidistant to two centres goes to exactly one; a report > 100 km from all → excluded and counted.
- Humidity missing → "insufficient data", never "low".
- Tuning code refuses to load rows with year ≥ 2022.

## Changes from v1 (stress test, 7 Nov) — what was adopted and why
- Lead time: v1 claimed the historical forecast archive gave an honest lead time. **Wrong**: that archive stitches the first hours
  of each run (Open-Meteo docs). Now: observed weather for the main test, Previous Runs day-ahead sub-study, 13 h reported as a
  design window.
- Regions were picked from all years' counts; now from 2015–2021 only, nearest-centre assignment (no double counting).
- Multi-signal: v1 alerted on weather only (fits Challenge 07 more than 06). Added W, a real lagged workplace signal.
- Algorithm and operating point frozen; one primary comparison; bootstrap intervals; episodes; renamed metrics.
- "Acclimatisation-loss term" renamed recent-weather anomaly; "fairness" renamed subgroup performance.
- Dry-bulb fallback removed (it can understate humid heat).
