# Clinical and safety criteria: sign-off sheet v2

Proposed 7 Nov 2026 after the Astra stress test. Sources: `docs/evidence_pack.md` (Arbury 2014 PMID 25102413 and Tustin 2018
PMID 29975679 spot-checked on PubMed). Signed by: **Ahmed Zayed, 7 Nov 2026** (in chat, "Yes, signed"). Changes after this date are logged in `docs/decisions.md`.

| # | Criterion | Proposed | Source | Tested on real outcomes? |
|---|---|---|---|---|
| S1 | Alert tiers on daily max heat index (H) | **Elevated** at H ≥ T_low, **High** at H ≥ T_high; T_low from {80, 85, 90} °F and T_high from {95, 100, 103} °F, chosen on 2015–2021 only. Own tier names (not NWS "Danger", which starts at 103 °F). A screening rule, not a safety certificate | OSHA NEP CPL 03-00-024 (2026): 80 °F heat priority day; OSHA Heat Safety Tool bands; Tustin MMWR 2018: 85 °F screen | Yes (2022–2025) |
| S2 | Recent-weather anomaly | H minus mean of previous 14 days; cut-off from {3, 5, 7, 9} °F tuned on 2015–2021. Labelled weather history, not acclimatisation | Tustin 2018 mentions early-season heat waves; no sourced cut-off | Yes |
| S3 | Workplace signal | ≥ 1 reported heat hospitalisation in the region in the previous 3 days, with H ≥ T_low | 29 CFR 1904.39 (24 h reporting) | Yes |
| S4 | New / returning workers | Crew-level switch "crew includes new or returning workers" (no names or job histories collected). Shows the acclimatisation schedule from the source (NIOSH: new workers ≤ 20 % of usual exposure day 1, +20 %/day; returning workers per NIOSH separately; ADPHC: no unacclimatised person in TWL medium/high zones). Raising the tier for these crews is **our heuristic**, labelled so | NIOSH 2016; Arbury 2014; Tustin JOEM 2018; ADPHC TG v4.0 | **No** |
| S5 | Actions, in three separate layers | **1. Legal, always shown, never switched by the model:** UAE midday break 15 Jun–15 Sep 12:30–15:00; ADPHC CoP 11.0 §3.1.1(e) "temperature at or above 35 °C" → heat stress programme (shown with its exact wording; not mapped onto heat index). **2. Baseline, always on:** water, shade, training, buddy system, symptom → immediate first aid/emergency escalation regardless of tier. **3. Model escalation:** Elevated → supervisor pre-shift check and acknowledgement; High → OSH practitioner site assessment before heavy outdoor work, heavy tasks re-timed, new-worker crews off heavy outdoor work; unacknowledged alert escalates; next review time shown. US OSHA 15 min/2 h appears only as "US proposed rule, reference" | ADPHC CoP 11.0 / TG v4.0; MoHRE midday break; OSHA NPRM 89 FR 70698 | No |
| S6 | Three separate rules | **Statistics:** always show n and 95 % interval; below 5 events show "too few events to estimate". **Privacy:** published views aggregate to region × month; no employer names, no narratives, no industry × region × day cells; no individual worker data collected; explicit ban on employment or disciplinary use. **Exclusions:** reports > 100 km from every region, counted and reported | Design choices; challenge item 4 | — |

Always shown with any output: no green "safe to work" state; "TWL not computed (needs globe temperature and a verified TWL
algorithm)"; "US data, not validated in Abu Dhabi"; "insufficient data" instead of a low tier when inputs are missing.

## S7: cool first, call 998 at the same time (signed by Ahmed Zayed, 8 Nov 2026, in chat: "Signed, build it")

| # | Criterion | Wording in the app | Source | Tested on real outcomes? |
|---|---|---|---|---|
| S7a | Cooling station on alert days | Plan step on Elevated and High days: "Before the shift: set up a cooling station in the shade (a tub or a tarp you can fill with water, ice, and towels) and name who runs it." | ACSM 2023 (PMID 37036463); ADPHC TG v4.0 4.5(c) | No (not by this app) |
| S7b | Emergency card, on every screen | 1 Stop work, move to shade. 2 Call 998, say "suspected heat stroke". 3 Start cooling now, don't wait for the ambulance: cold water to the neck with the head held out, or whole body covered in towels or sheets soaked in ice water, swapped as they warm. 4 Keep cooling until medics take over; tell them when cooling started. 5 No drinks if confused or drowsy. | ACSM 2023; Tishukaj 2024 (PMID 39183116); Stearns 2024 (PMID 37655801); DeGroot 2023 (PMID 36806435); Hemingway 2025 (PMID 40139736); ADPHC TG 4.5(c); u.ae (998) | No (by this app); survival evidence from published cohorts |
| S7c | Regulator measure | Sites with a cooling station ready on Elevated and High days (simulated in the demo) | Pilot measure | No |

Open questions answered by default when signing "as drafted": S7a shows on Elevated **and** High; S7b keeps step 5. Alignment
with UAE ambulance instructions (National Ambulance / SEHA) is not checked; it is a pilot item.
