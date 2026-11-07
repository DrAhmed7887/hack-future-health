# Claims audit (Phase 4)

Run 7 Nov 2026 (overnight, automated, Claude Code). Scope: `README.md`, all UI text in `web/app.js` and `web/logic.js`,
`web/index.html`, `docs/diagram/workflow.svg` and `docs/diagram/workflow_4x5.svg` (sources of `docs/workflow*.png`).
Every number was checked against `results/*.json` or `web/data/evidence.json` (built from them by `scripts/build_web_data.py`).
No number was typed in by hand, and no rule, threshold, results file or protocol was changed.

Status: **OK** = traced and the code does what it says · **FIXED** = wording corrected in this run · **NEEDS AHMED** = a
clinical or product decision, or a source quote that is missing.

## Numbers

| Claim | Where | Source | Status |
|---|---|---|---|
| 2,628 work-related heat hospitalisation reports, Jan 2015 – Nov 2025 | README, app Evidence, both diagrams | `results/holdout_results.json` data.heat_reports = 2628; `evidence.json` reports_total; filter = OIICS event codes 531/5310/5311/5312 (`heatwarn/data.py`), counts in `docs/evidence_pack.md` | OK |
| Fixed 80 °F rule alerts on 93 % of days (8 original regions) | README | `test_results.json` R1 alert_fraction 0.925 | OK |
| Fixed 80 °F rule alerts on 82 % of days (6 unseen regions) | README, app Evidence | `holdout_results.json` R1 alert_fraction 0.820; `evidence.json` fixed_80f_alert_share | OK |
| A threshold "tuned on Texas and Florida" puts every Abu Dhabi day Jun–Sep in its top tier | README, `docs/g1b_relative_results.md` | `docs/g1_results.md` transfer check (High share 100 % Jun–Sep). But the 8 tuning regions include Oklahoma City and Kansas City (`heatwarn/regions.py`) | FIXED: "the 8 original US regions (Texas, Florida, Oklahoma, Missouri)" |
| Table row "Fixed thresholds tuned in TX/FL" | README | same | FIXED: "tuned on the 8 original regions" |
| Rule R4: HI ≥ 80 °F and P ≥ 60 (High) or P ≥ 50 and anomaly ≥ 3 °F (Elevated); percentiles from own 2015–2021 ERA5 | README, diagram 16:9 box 3 | `results/frozen_params_r4.json` (p_high 60, p_low 50, a 3); `heatwarn/relative.py` r4_relative / r4_tier | OK |
| Tiers May–September only | README, app, diagrams | `web/logic.js` inTestedSeason (months 5–9); resolveDay | OK |
| Transfer table: R1 98.8 % (95.8–100), 82 %; R0 76.7 % (65.8–86.0), 61 %; R2 70.9 % (57.1–82.1), 40 %; R4 79.1 % (69.6–87.9), 49 % | README | `holdout_results.json` rules.R0/R1/R2/R4 sensitivity, sensitivity_95ci, alert_fraction | OK |
| Calendar rule = 15 Jun–15 Sep | README | `heatwarn/rules.py` r0_calendar (md 615–915) | OK |
| 86 event days in the transfer test | README, app | `holdout_results.json` data.event_days 86 | OK |
| R4 alert load 36–60 % per region, 25-point band; fixed 7 % (Pittsburgh) to 89 % (McAllen), 82 points | README, app Evidence ("25 vs 82"), diagram 16:9 | `holdout_results.json` per_region (Braddock 0.356 → McAllen 0.601; R2 Braddock 0.069 → McAllen 0.892); primary_B 0.245 vs 0.824 | OK. Wording FIXED: "Pittsburgh area" (the region is Braddock, PA) |
| Pre-registered success criterion met | README | `holdout_results.json` success_criterion_met = true; criterion in `docs/protocol_v3_relative.md` | OK |
| R4 − R2 sensitivity +8.1 points (−6.9 to +24.3), not statistically clear | README | `holdout_results.json` primary_A | OK |
| Training sensitivity 78.4 % (R2) vs 67.4 % (R4) | README | `frozen_params.json` r2.train 0.784; `frozen_params_r4.json` train 0.674 | OK |
| Day-ahead: same decision 84 %; 59 % vs 51 % alert days; 81.7 % vs 73.1 % sensitivity; 2024–2025, 8 regions | README, app Evidence | `dayahead_r4_results.json` same_decision_share 0.840, alert_fraction 0.592 / 0.509, sensitivity 0.817 / 0.731 | OK |
| "every input available at 18:00 the day before" | README | `docs/g1b_relative_results.md` day-ahead section (Previous Runs 24 h forecast; ERA5 2015–2021 percentiles; Historical Forecast API baseline) | OK |
| Workplace trigger −11.6 points (95 % CI −17.7 to −5.8) | README, app Evidence | `test_results.json` primary_r3_minus_r2_sensitivity; `evidence.json` workplace_trigger | OK numbers. Wording FIXED: it compares R3 with the earlier fixed-threshold rule R2 on the 8 original regions, not with the app's rule R4; the app now says so, and says "same training alert budget" (decisions log, 7 Nov) |
| "79% of case days", "36 to 60%", "7 to 89%" | both diagrams | same as above | OK |
| Evidence screen showed 79% (70% to 88%) and "12 … −18 to −6" where README says 79.1 % (69.6–87.9) and −11.6 (−17.7 to −5.8) | app Evidence | same `evidence.json` values, rounded to whole numbers in `app.js` (flagged by the video-director review) | FIXED: the sensitivity, its interval and the workplace result now show one decimal, matching README; no value changed |
| Replay day Mussafah 1 Aug 2025: High, max 45 °C, percentile 100, +19.8 °F (11 °C) above 14 days, peak 14:00 | app replay (video shot) | `web/data/replay.json` | OK |

## Method and process claims

| Claim | Where | Source | Status |
|---|---|---|---|
| Tuned on 2015–2021, committed, scored once on later data; pre-registered; one logged amendment | README | `docs/backtest_protocol.md`, `docs/protocol_v3_relative.md` (amendment 1), git history | FIXED: added the logged bootstrap bug fix that re-ran scoring with rules and point estimates unchanged (`docs/decisions.md`) |
| Reproduce block lists every script | README | `scripts/` | FIXED: `score_dayahead_r4.py` (source of the 84 % / 59 % / 81.7 % numbers) was missing |
| Thresholds relative to local climate (Anderson & Bell 2009, PMID 19194300; Gasparrini 2015, PMID 26003380) | README | `docs/evidence_relative_thresholds.md` (quotes re-checked on PubMed 7 Nov) | OK |
| Forecast refreshed daily at 18:00 Abu Dhabi time | README, app home, app plan, diagrams | `.github/workflows/refresh-live.yml` cron `0 14 * * *` (18:00 Dubai); GitHub delays scheduled runs (first run 4.5 h late) | README OK. App FIXED: "Updates daily at 18:00" and "Next forecast: tomorrow at 18:00" → "scheduled for 18:00 Abu Dhabi time". 4x5 diagram FIXED: "Every evening at 18:00" → "Scheduled each evening at 18:00" (16:9 was already fixed in 1ca8048) |
| Stale forecast shows "Not enough data", treated as Elevated | README, app | `web/logic.js` resolveDay (36 h / date check), effectiveTier floor; node tests | OK |
| "Plans not acknowledged by 06:30 go to the OSH practitioner" | app plan screen (twice), user flow | No code sends anything; it is the intended workflow (S5 "unacknowledged alert escalates") | FIXED: "would go to the OSH practitioner (this demo sends nothing)". Diagram "acknowledge by 06:30" is OK (the button exists) |
| "a locally calibrated heat alert" | `web/index.html` meta description | "Calibrated" implies outcome calibration in Abu Dhabi, which was not done | FIXED: "a heat alert ranked against local climate" |
| "every work-related heat hospitalisation reported to US federal OSHA from 2015 to 2025" | app Evidence | Selection is by event code (20 heat narratives are coded otherwise, `docs/evidence_pack.md`); data end Nov 2025 | FIXED: "the work-related heat hospitalisations reported … from January 2015 to November 2025" |
| "An alert that rarely switches off gets ignored" | app Evidence | General alert-fatigue statement, no source in the evidence pack | FIXED: softened to "is easy to ignore" |
| NWS: heat index formula "is not valid for extreme temperature and relative humidity conditions" | README, app Evidence | `docs/evidence_pack.md` line 81 (NWS WPC) | OK |
| "…which Abu Dhabi summers often reach" | app Evidence | Evidence pack line 83 is our reasoning, not a source | FIXED: "conditions Abu Dhabi summers can reach" |
| Thermal Work Limit is Abu Dhabi's official index; not calculated | README, app legal layer | TG Safety in the Heat v4.0 §2.1 (evidence pack line 134) | OK |

## Privacy and governance claims

| Claim | Where | Source | Status |
|---|---|---|---|
| No worker names, health data or job histories collected; two yes/no/not sure questions | README, app crew screen | `web/app.js` crew view (radio buttons only); `state.crew` | OK |
| "Not sure" counts as yes | README, app | `logic.js` answeredYes(v) = v !== "no", so an unanswered question also counts as yes | FIXED: "\"not sure\", or no answer, counts as yes" |
| Regulator view "hides zones with fewer than 5 sites" | README, diagram 16:9 ("small zones hidden") | `app.js` regulator: zone and tier still shown; site counts and notices hidden when n < 5 | FIXED in both: "hides site counts and incident notices for zones with fewer than 5 sites" / "site counts hidden below 5 sites" |
| Sites, acknowledgements, incident notices simulated and labelled | README, app banner, regulator footer | `SIM_SITES`, `SIM_NOTICES` in `app.js`; banner in `index.html` | OK |
| Not for employment or disciplinary use | README, regulator view | signed S6 | OK |
| Reports appear only as a prompt, never raise the tier | README, regulator view | `app.js` regulator notice text; tiers come only from the frozen rule | OK |

## Action text (plan screen)

| Claim | Where | Source | Status |
|---|---|---|---|
| Midday break 12:30–15:00, 15 Jun–15 Sep | app legal layer | `docs/evidence_pack.md` §5.1 (MoHRE via WAM, The National, Gulf News); `logic.js` legalItems | OK |
| 35 °C → site heat stress programme applies (CoP 11.0 §3.1.1(e)) | README, app legal layer | evidence pack line 142 (full quote includes "unless … TWL … no risk") | OK (simplified; the exception is not shown, which is the conservative side) |
| Water: at least 2 litres every 2 to 3 hours (ADPHC CoP 11.0) | app always-on | evidence pack line 146, CoP 2(d)(ii) | OK |
| Shade and cooling shelters, "ADPHC CoP 11.0, section 3.2(b)(vii)" | app always-on | Quote added to evidence pack (CoP v4.0 §3.2(b)(vii)); citation narrowed to (vii) | RESOLVED 7 Nov |
| Nobody works alone in heat stress areas (CoP §3.2(e)) | app always-on | evidence pack line 146 | OK |
| Symptoms → stop, cool, water; call 998 if confused/collapsed (ADPHC TG §4.4(c), §4.5(c); u.ae) | app always-on | TG first-aid quotes and the u.ae 998 quote added to evidence pack (u.ae page moved to .../safety/handling-emergencies) | RESOLVED 7 Nov |
| New: first 5 days; returning: back after more than 14 days | app crew screen | TG acclimatisation table Days 1–5; TG Table 1 note "off work for more than 14 days" (evidence pack lines 140, 144) | OK |
| "New or returning workers: no more than 20% … day 1, adding 20% a day", owner "NIOSH 2016 criteria document" | app plan (`logic.js`) | NIOSH 2016 sets 20 %/+20 % for **new** workers; experienced workers start at 50/60/80/100 % (evidence pack lines 89–90). Signed S4 says "returning workers per NIOSH separately" | Attribution FIXED (owner now says the NIOSH schedule is for new workers and using it for returning workers is stricter than NIOSH; advice unchanged). NEEDS AHMED: keep the stricter single schedule, or show NIOSH's / the TG's separate returning-worker schedule as S4 says |
| No unacclimatised worker in medium or high risk heat work | app plan | TG Table 1 (evidence pack lines 138–139) | OK |
| New/returning workers raise the tier one level; labelled as our rule | README, app plan | signed S4; `logic.js` effectiveTier; node tests | OK |
| High → OSH practitioner assessment before heavy work; heavy tasks moved from peak | app plan | signed S5 (model layer); `logic.js` planSteps | OK |

## Checks run after the fixes
- `uv run pytest -q`: 18 passed. `node --test web/tests/logic.test.js`: 15 passed.
- `docs/workflow.png` (1600×900) and `docs/workflow_4x5.png` (1080×1350) re-rendered with headless Chrome and inspected: text fits its boxes.
