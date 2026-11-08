# Heat Shift Planner

Future Health Digital Innovation Challenge (Abu Dhabi) · Challenge 06: Population and Workforce Health Early Warning.

**Try it (no login): https://drahmed7887.github.io/hack-future-health/** · In November, tap "Replay a day" to see a real summer day:
alerts run May to September only.

![How Heat Shift Planner works](docs/workflow.png)

The evening before a shift, a site supervisor in Abu Dhabi sees three things for tomorrow, plus one for emergencies:
1. **What the law already requires** (UAE midday break; the ADPHC rule that a heat stress programme applies at 35 °C or more).
2. **Whether tomorrow is hotter than most days for that place and time of year**, using a rule tested on real heat hospitalisations.
3. **A plan for their crew**: new or returning workers and heavy work change the steps, each with an owner and a source.
4. **What to do if someone collapses**: a red card on every screen. Heat stroke is treated by cooling on site at once,
   while the ambulance (998) is on its way ("cool first, transport second").

The regulator sees zones, never people. Nothing in the app clears anyone to work.

> This README is the single source for every claim. Slides, submission text and the video are made from it, and every number
> below comes from a script output in `results/`.

## Why a new rule was needed

A fixed heat trigger fails in both directions. The common US trigger (heat index ≥ 80 °F) alerted on **93 %** of summer days in
the original 8 test regions and **82 %** in 6 unseen ones: an alert that rarely switches off. A threshold tuned on the 8 original US regions (Texas, Florida, Oklahoma, Missouri) would put **every Abu Dhabi day from
June to September** in its top tier (`docs/g1_results.md`, transfer check). Heat-health research sets thresholds relative to
local climate because people adapt to their usual heat (Anderson & Bell 2009, PMID 19194300; Gasparrini et al. 2015,
PMID 26003380). So each zone gets thresholds from its own weather history.

## The rule (frozen before scoring)

Alert when the heat index is at least 80 °F **and** tomorrow is hotter than the zone's 60th percentile for that time of year
(**High**), or hotter than its 50th percentile and at least 3 °F above the previous 14 days (**Elevated**). Percentiles come from
each place's own 2015–2021 weather (ERA5). Model tiers run **May to September only**, the season it was tested on.
Code: `heatwarn/relative.py`; frozen parameters `results/frozen_params_r4.json`.

## How it was tested

No public data on work-related heat illness exists for Abu Dhabi. The closest real record is **US federal OSHA's Severe Injury
Reports**: 2,628 work-related heat hospitalisations, January 2015 to November 2025, with date and location. Each was matched to
that day's weather. Rules were tuned on 2015–2021, committed, and scored once on later data. Every step was pre-registered
(`docs/backtest_protocol.md`, `docs/protocol_v3_relative.md`, `docs/protocol_v4_trained_model.md`), including expected results and one logged amendment. One logged
bug fix in the confidence-interval code led to a re-run with rules and point estimates unchanged (`docs/decisions.md`).

**Transfer test: 6 US regions never used in tuning, 2022–2025** (86 days with a reported heat hospitalisation, a subset of the
2,628 reports; each day scored with the weather that actually happened, so this is a back-test, not a forecast test; the forecast check
is below; `results/holdout_results.json`)

| Rule | Days with a reported case that got an alert (95 % CI) | Share of days alerted |
|---|---|---|
| Fixed heat index ≥ 80 °F | 98.8 % (95.8–100) | 82 % |
| Calendar (15 Jun–15 Sep) | 76.7 % (65.8–86.0) | 61 % |
| Fixed thresholds tuned on the 8 original regions | 70.9 % (57.1–82.1) | 40 % |
| **Relative rule (this app)** | **79.1 % (69.6–87.9)** | **49 %** |

- Alert load stayed in a **25-point band** across cool and hot cities (36–60 % of days) with the relative rule, against
  **82 points** (7 % in the Pittsburgh area to 89 % in McAllen) with fixed thresholds. The pre-registered success criterion was met.
- The sensitivity gain over fixed thresholds (+8.1 points, 95 % CI −6.9 to +24.3) is **not statistically clear**.
- Within the climates it was tuned on, fixed thresholds did better (training sensitivity 78.4 % vs 67.4 %).

**Forecast the evening before** (8 original regions, 2024–2025, the years with archived 24-hour humidity forecasts; every input
available at 18:00 the day before): the deployed rule gave the same decision as observed weather on **84 %** of region-days.
The forecast ran warm, so it alerted on more days (59 % vs 51 %) and caught more reported-case days (81.7 % vs 73.1 %)
(`results/dayahead_r4_results.json`; frozen rule, checked after the main tests).

**The six measures the challenge asks for (item 5)**, deployed rule, 6 unseen US regions, 2022–2025, unless stated:

| Measure | Result | Source and note |
|---|---|---|
| Sensitivity | 79.1 % of 86 reported-case days (95 % CI 69.6–87.9) | `results/holdout_results.json` |
| Positive predictive value | 3.8 % (68 of 1,797 alert days had a reported case) | Reported severe cases only: most heat illness is never reported to OSHA (illness reporting about 25 % in one state, evidence pack 6.3), so this is a floor, not the true rate |
| False alarms | 1,729 of 3,586 days with no reported case got an alert (48 %); the common fixed trigger alerted on 82 % of all days | Same file; the alert is a prompt to plan, not an evacuation |
| Lead time | Forecast scheduled at 18:00 Abu Dhabi time the evening before, about 12 hours before a 06:00 shift | `.github/workflows/refresh-live.yml`; GitHub can delay scheduled runs |
| Data latency | One forecast a day; data older than 36 hours is treated as missing | `web/logic.js` (`STALE_HOURS`) |
| Missing inputs | Fewer than 18 valid hours in a day, or a stale forecast: "Not enough data", treated as Elevated; the legal layer stays visible (0 such days in the test data) | `heatwarn/signals.py`, `web/logic.js`, tests |

## What did not work

We expected recent incident reports nearby to improve the alert, and pre-registered that test. A rule that also used them
as a trigger, tuned to the same training alert budget, caught **11.6 points fewer** heat days than a weather-only rule tuned separately
(95 % CI −17.7 to −5.8) (`results/test_results.json`; earlier fixed-threshold rules, 8 original regions, 2022–2025). This compares two separately tuned rules, not the reports' isolated
value: spending part of the alert budget on "recent report" days left less for hot days. In the app the reports appear only
as a prompt to check that workplace, never as a reason to raise the level.

## We also trained a model. It missed the pass mark set before scoring, so the app keeps the rule

We trained a risk model (logistic regression, chosen over gradient boosting by leave-one-year-out cross-validation) on the
same 2015–2021 data with more inputs: night-time heat, days in a row of unusual heat, sunshine, wind, season and weekend.
It was frozen, set to the rule's training alert count, and scored once on the same 6 unseen regions
(`docs/protocol_v4_trained_model.md`, `results/model_v4_results.json`). The deployment criterion was fixed in advance: catch at
least as many case days as the rule, with alert-load spread no more than 5 points wider.

| | Days with a reported case that got an alert (95 % CI) | Share of days alerted | Spread in alert load across regions |
|---|---|---|---|
| Trained model | 77.9 % (65.8–87.6) | 40 % | 76 points (5 % in the Pittsburgh area to 81 % in McAllen) |
| **Relative rule (this app)** | **79.1 % (69.6–87.9)** | **49 %** | **25 points** |

- The model **ranks days better** (AUC 0.73 against 0.66 for the rule's tiers; difference +0.07, 95 % CI +0.01 to +0.13).
- It caught about the same share of case days (difference −1.2 points, 95 % CI −13.9 to +10.8), but its alert load swung
  with local climate, so the criterion was **not met**.
- Why absolute heat was an input at all: the protocol tested whether standard weather inputs transfer to a new climate as
  they are, without forcing them to be relative. They did not, which is the evidence for keeping the relative rule.
- The reason is in its weights: it learned **absolute heat** (standardised coefficient 0.86), not how unusual the day is for that
  place (0.01). Run on Abu Dhabi's four zones, it would alert on **93–100 % of May–September 2025 days**: the same failure as the
  fixed thresholds. A ranking against each zone's own climate is what transferred.

## Combining signals (challenge requirement 1)

Two levels. **At the site**, environmental (the forecast, ranked against local climate) and workplace (supervisor-entered
crew composition and planned heavy work) are combined into the plan. **For the regulator**, each zone's heat tier is shown with
site-level service signals: plans acknowledged, cooling stations ready and incident notices (simulated in the demo; in the pilot,
ADOSH-SF incident notifications and emergency-department heat-illness visits by zone and day), so ADPHC can see zones where
risk is high and preparation is low. Incident notices never change the tier (that rule failed its pre-registered test). The workplace rules come from guidelines (NIOSH 2016 acclimatisation schedule;
ADPHC Code of Practice 11.0 and Technical Guideline "Safety in the Heat", v4.0, 2024) and are **labelled as not tested on outcomes**.

## From warning to survival (wording signed by Dr Ahmed Zayed, physician; not tested by this app)

Prediction only helps if the worst case is handled well. For heat stroke, survival depends on how fast the body is cooled, so
the app adds two things on Elevated and High days and on every screen:
- **A cooling station before the shift**: a tub or tarp with water, ice and towels in the shade, with a named person in charge.
- **An emergency card**: move them to shade, call 998, start cooling now without waiting for the ambulance (cold water to the
  neck, or whole-body towels or sheets soaked in ice water), keep cooling until medics take over, no drinks if confused.

Evidence: rapid total-body cooling is "essential for survival … time is tissue" (ACSM consensus 2023, PMID 37036463). In US
states whose ambulance guidelines include cold-water immersion and "cool first, transport second", labourers were 3.0 and 3.7
times less likely to die of heat stroke (Tishukaj 2024, PMID 39183116; ecological, state level). 454 runners with heat stroke
treated by cold-water immersion all survived (Stearns 2024, PMID 37655801); ice-soaked sheets had 0.20 % mortality in 462
soldiers (DeGroot 2023, PMID 36806435). The ADPHC guideline says "Cool the employee"; the card says how. Wording signed in
`docs/signoff.md` (S7). Alignment with UAE ambulance instructions is a pilot item. The regulator view's cooling-station counts
are simulated.

## Limits

- US data, reported cases only; most cases go unreported. Not validated on Abu Dhabi outcomes: local shadow-mode validation is needed first.
- Tested for May to September only. The app shows "Outside tested season" for other months.
- It does not calculate the Thermal Work Limit, Abu Dhabi's official heat stress index (needs on-site globe temperature).
- The heat index ranks days; NWS states its formula "is not valid for extreme temperature and relative humidity conditions".
- Small numbers: 86 event days in the transfer test; intervals are wide.
- Decision support for supervisors. Not a diagnosis, not a medical device, never a clearance to work.

## Expected impact (challenge item 6)

Preventing severe heat illness means fewer hospital days and less **sickness absence and lost workdays**: the outcome tested here,
work heat hospitalisation, means days off work every time. Not yet shown in Abu Dhabi; the pilot measures it. The pilot logs
(tier, plan acknowledged, cooling ready, cases) by zone and day also give ADPHC **evidence for policy**, for example whether
the 35 °C programme trigger and the 15 June – 15 September midday break cover the days that turn out dangerous.

## Privacy and governance

No worker names, health data or job histories are collected. Crew questions are yes / no / not sure ("not sure", or no answer, counts as yes).
The regulator view aggregates by zone and hides site counts and incident notices for zones with fewer than 5 sites. Not for employment or disciplinary use.
Sites, acknowledgements and incident notices in the demo are simulated and labelled.

## Data sources and licences

- US OSHA Severe Injury Reports, Jan 2015 – Nov 2025 (US government public data). Raw file not committed; `docs/backtest_protocol.md` records its SHA-256.
- Weather: Open-Meteo (CC BY 4.0): Historical Weather API (ERA5 reanalysis, Copernicus Climate Change Service), Previous Runs API, Forecast API.
- Guidance quoted: NIOSH 2016; OSHA CPL 03-00-024 (2026); ADPHC CoP 11.0 and TG Safety in the Heat (v4.0); UAE MoHRE midday break. Evidence with quotes: `docs/evidence_pack.md`, `docs/evidence_relative_thresholds.md`.

## Reproduce

**Quick check, no downloads** (all results are committed in `results/`):

```bash
uv sync
uv run pytest -q && node --test web/tests/logic.test.js
python3 -m http.server 8765 --directory web   # then open http://localhost:8765
```

**Full rebuild from raw data.** First download the OSHA Severe Injury Reports file (osha.gov/severe-injury-reports) into
`data/raw/osha_sir/` (not redistributed; its SHA-256 is in `docs/backtest_protocol.md`). Weather is fetched from Open-Meteo.

```bash
uv run python scripts/fetch_weather.py && uv run python scripts/fetch_weather.py --holdout
uv run python scripts/tune.py && uv run python scripts/score_test.py        # original regions
uv run python scripts/tune_relative.py && uv run python scripts/score_holdout.py
uv run python scripts/fetch_dayahead.py && uv run python scripts/score_dayahead.py && uv run python scripts/score_dayahead_r4.py
uv run python scripts/fetch_sunwind.py && uv run python scripts/train_model.py && uv run python scripts/score_model.py   # trained model (not deployed)
uv run python scripts/abu_dhabi_tiers.py && uv run python scripts/build_web_data.py
```

Deck, film and diagram scripts (`scripts/build_deck.py`, `build_video.py`, `capture_video_stills*.py`, `draw_path_to_pilot.py`)
need extra packages, run as `uv run --with python-pptx --with pillow --with playwright python <script>`. The live forecast refresh is scheduled
daily at 18:00 Abu Dhabi time (`.github/workflows/refresh-live.yml`); GitHub can delay scheduled runs by hours, and the app
shows "Not enough data" if the forecast is out of date.

## Repository map

`heatwarn/` rule and back-test code · `scripts/` every number's source · `results/` frozen parameters and results ·
`docs/` protocols, evidence, decisions log, user flow · `web/` the app (static) · `tests/`, `web/tests/` tests.
