# Back-test protocol (DRAFT, pre-registered before any result is computed)

Status: draft 7 Nov 2026. Thresholds marked **[SIGN]** need Ahmed's sign-off against `docs/evidence_pack.md`.
Nothing below may be changed after the test split is scored without logging the change and the reason here.

## Question
Does a weather-based worker heat alert, issued before the shift, flag the days on which real heat hospitalisations happen,
better than the fixed rules used today, and with how many false alarms?

## Data (all public, declared)
| Signal | Source | Type | Notes |
|---|---|---|---|
| Outcome: work-related heat hospitalisations | OSHA Severe Injury Reports, 1 Jan 2015 – 30 Nov 2025 (`January2015toNovember2025.zip`, sha256 a3f7f434…bb0, downloaded 7 Nov 2026) | Workplace incident | OIICS event codes 531/5310/5311/5312 "Exposure to environmental heat": 2,628 reports, 2,627 with lat/lon (2 decimals). Federal-OSHA states only (state-plan states such as CA, AZ, WA are missing). Only severe cases (hospitalisation), under-reported. Employer names are public; no worker names. We use date + location + code only and publish aggregates. |
| Environment (observed) | Open-Meteo Historical Weather API (ERA5 reanalysis) | Environmental | Daily max temperature, apparent temperature, wet-bulb max, humidity, shortwave radiation. Checked 7 Nov: Houston 2015-05-01→2025-09-30 returns 3,806 days. |
| Environment (as forecast at the time) | Open-Meteo Historical Forecast API | Environmental | Archived forecasts: used for the honest lead-time test (what the system would have known the evening before). Checked 7 Nov (Houston): values returned for 1 Jul 2021, 2022 and 2023, null for 1 Jul 2016, so the archive covers the test years 2022–2025. |

What this back-test cannot show: individual days-since-arrival (2 of 2,628 narratives mention it), Abu Dhabi performance (US data;
recalibration needed), effect of the alert on behaviour.

## Units
- **Region-day**, May–September, for fixed regions: circles of radius **[SIGN] 100 km** around Dallas–Fort Worth, Houston,
  San Antonio, Orlando, Tampa, Jacksonville, Miami, Atlanta, Kansas City, Philadelphia (chosen from case counts on 7 Nov,
  before any weather was joined).
- **Event** = at least one environmental-heat hospitalisation reported in the region on that day.
- **Alert** = the rule fires for that region-day.

## Rules compared
1. **Calendar rule** (analogue of the UAE midday break): alert every day 15 Jun – 15 Sep.
2. **Fixed heat-index rule:** alert when forecast daily max heat index ≥ **[SIGN] 80 °F / 26.7 °C** (OSHA NEP trigger, to verify) and a high tier at **[SIGN] 90 °F**.
3. **HeatShield:** estimated WBGT/heat index tier **plus** a relative-heat term: today's max vs the region's mean of the previous
   **[SIGN] 14 days** (population acclimatisation proxy: early-season heat and sudden heat after a cool spell).

## Split (fixed before scoring)
- Tune any threshold or weight on **2015–2021** only.
- Score once on **2022–2025** (locked). Archived forecasts (covered, checked 7 Nov) are used on the test years; ERA5 observed weather is used for tuning on 2015–2021.

## Metrics (all from `scripts/backtest.py`, re-run after any change)
- Sensitivity = event days alerted / event days.
- PPV = alerted days with an event / alerted days.
- False alarms per region per summer.
- Lead time = hours from alert issue (forecast issued the evening before, 18:00 local) to the start of the shift (07:00). Reported as a
  distribution; not "time to the hospitalisation", which OSHA does not record.
- Data latency: forecast available at issue time (yes/no); OSHA reports are not used for alerting (they arrive days later).
- Missing input: rerun with humidity dropped, with radiation dropped, and with 20% of days' weather missing; report the change.
- Fairness/coverage: results per region and per industry group (NAICS 23 construction, 48–49 transport/warehousing, 56 admin/waste).

## Expected results (written before running, 7 Nov)
- Calendar rule: sensitivity close to 90% (most cases are Jun–Aug), PPV low (most summer days have no reported case).
- Fixed heat-index 80 °F: fires on nearly every summer day in TX/FL, so it behaves like the calendar rule.
- HeatShield: lower sensitivity than the calendar rule, higher PPV; the relative-heat term should add most in May–June.
- If HeatShield does not beat the fixed rule on PPV at a similar sensitivity on 2022–2025, we say so in the README and the video.

## Test cases written before the code (unit level)
- A region-day with max heat index 105 °F after 14 days averaging 85 °F → high tier + relative-heat flag.
- The same 105 °F after 14 days averaging 104 °F → high tier, no relative-heat flag.
- Humidity missing → falls back to dry-bulb tier with a "reduced confidence" label, never silently "low risk".
- A report with lat/lon outside every region → not counted, and the excluded count is reported.
- A region with fewer than **[SIGN] 5** events in the test years → shown, but with "too few events to estimate" instead of a percentage.
