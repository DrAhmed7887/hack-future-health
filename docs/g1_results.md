# G1: back-test results (test years 2022–2025, scored once with rules frozen on 2015–2021)

Source: `results/test_results.json` from `scripts/score_test.py` (commit ce0f0ec); frozen parameters `results/frozen_params.json` (commit df74a4e, made before test years were loaded).
8 regions, May–Sep, 4,896 region-days, 225 days with at least one reported heat hospitalisation (250 reports, 251 workers).
Of all 2,628 heat reports (2015–2025), 743 fall within 100 km of a region centre; 1,846 fall outside every region and 1 has no location.

| Rule | Sensitivity (95 % CI) | Reported-event PPV | Alert days | Episodes | Longest run |
|---|---|---|---|---|---|
| R0 calendar (15 Jun–15 Sep) | 82.7 % (77.2–87.3) | 6.2 % | 61 % | 32 | 93 |
| R1 heat index ≥ 80 °F | 99.1 % (97.7–100.0) | 4.9 % | 93 % | 165 | 153 |
| **R2 weather** (Elevated ≥ 85 °F with anomaly ≥ 9 °F; High ≥ 95 °F) | **85.8 % (80.1–90.3)** | 7.3 % | 54 % | 419 | 93 |
| R3 weather + workplace (80 / 100 / 3 °F + reports in previous 3 days) | 74.2 % (67.6–79.9) | 7.2 % | 47 % | 544 | 56 |

**Primary comparison (R3 − R2 sensitivity): −11.6 points (95 % CI −17.7 to −5.8).** The workplace signal did not help. Both rules were tuned to the same **training** alert budget; on the test years their realised alert shares differ (R2 54 %, R3 47 %), so this compares the two frozen rule packages, not the workplace signal's isolated value at equal alert frequency. The displacement explanation below is a hypothesis.

## Expected (written 7 Nov before running) vs actual
- R0 high sensitivity, many alert days: **as expected** (82.7 %, 61 % of days).
- R1 close to R0: **wrong**: R1 fires on 93 % of summer days, far more than the calendar, catching 99 % of event days.
- R2 fewer alert days than R1, lower sensitivity: **as expected** (54 % vs 93 % of days; 85.8 % vs 99.1 %). R2 also beats the calendar rule: fewer alert days (54 % vs 61 %) at similar sensitivity (85.8 % vs 82.7 %; intervals overlap).
- R3 small gain over R2: **wrong**: R3 lost 11.6 points. Reports are sparse (most event days have one report, 225 event days in 4 years across 8 regions), so alerts spent on "recent report" days likely displaced heat days (hypothesis, not demonstrated). The back-test also assumed reports reach the regulator within 24 h of the incident (the legal deadline); the public dataset is published much later, so W is an idealised signal.

## Missing inputs (never shown as low risk)
- 20 % of days missing at random: 983 days marked "insufficient data"; R2 sensitivity on the remaining days 86.5 %.
- 3-day outage in each season's hottest week: 96 days "insufficient"; R2 sensitivity 85.3 %.
- Workplace feed unavailable: R3 falls back to its weather terms, 69.3 %.

## Per region (R2 event days caught / event days, alert share)
DFW 57/64 (59 %) · Houston 41/43 (71 %) · Jacksonville 9/14 (47 %) · Kansas City 8/13 (26 %) · Oklahoma City 4/6 (41 %) · Orlando 28/32 (58 %) · San Antonio 10/10 (72 %) · Tampa 36/43 (60 %). Regions with < 10 event days are too small to estimate.

## Subgroups (R2, days with a report from that industry)
Construction 53/60 (88.3 %) · transport/warehousing 43/52 (82.7 %) · admin/waste services 37/41 (90.2 %). Small numbers; coverage only, not fairness.

## Still to do in Phase 1
- Day-ahead sub-study (forecasts made 24 h before; humidity archive coverage to audit).
