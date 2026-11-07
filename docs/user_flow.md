# User flow (Phase 2, draft for G2)

Primary user: **the site supervisor** of an outdoor crew in Abu Dhabi (construction, logistics yard, industrial plant), on a
phone, standing on site. Two moments: **the evening before** (planning tomorrow) and **06:30 pre-shift** (briefing the crew).
Second user: **the company OSH practitioner** (one site or several). Third: **the regulator's OSH specialist** (aggregate view only).
Judges arrive with no login and must be able to test every screen.

Rules for every screen: no green "safe to work"; no score without its reason; every screen has one obvious next step;
"insufficient data" never shows as low risk; legal requirements are shown whatever the model says.

## Screen 1 — Pick your site (first visit only)
- Sees: four Abu Dhabi zones (Mussafah, Abu Dhabi city, Ruwais, Al Ain) and a banner "Demo: no real sites or workers".
- Does: taps a zone. Next: Screen 2.
- Why: tier depends on the zone's own climate.

## Screen 2 — Tomorrow at a glance (home)
- Sees, top to bottom:
  1. **Legal today** (always): midday break in force 15 Jun–15 Sep, 12:30–15:00 (yes/no for tomorrow); "Forecast max 41 °C:
     at or above 35 °C → your heat stress programme applies (ADPHC CoP 11.0 §3.1.1(e))".
  2. **Model tier for tomorrow**: High / Elevated / No escalation / Insufficient data / Outside tested season (Oct–Apr).
     One line why: "Heat index peak 112 °F at 14:00 — hotter than 78 % of days at this time of year here; 6 °F above the last
     14 days."
  3. Forecast issued time and data freshness.
- Does: taps **"Plan tomorrow's crew"**. Next: Screen 3.
- Why: one glance answers "is tomorrow different from normal, and what does the law already require?".

## Screen 3 — Tomorrow's crew (5 seconds, two switches)
- Sees: two switches, both default **"not answered"** (never assumed "no"):
  - "Crew includes new or returning workers (first 5 days, or back after more than 14 days away)"
  - "Heavy outdoor work planned (e.g. concrete pour, manual lifting)"
- Does: sets them. Next: Screen 4.
- Why: same weather, different crew → different plan (signed S4/S5). No names, no job histories.

## Screen 4 — Tomorrow's plan
- Sees three blocks, each labelled with its source and status:
  1. **Required by law** (from Screen 2).
  2. **Always on**: water (2 L every 2–3 h, ADPHC), shade, buddy system, symptoms → stop work, first aid, call emergency.
  3. **Because of tomorrow's tier and your crew** (guideline-based, not tested on outcomes): e.g. High + new workers →
     "New workers: 20 % of usual heat exposure on day 1, +20 % a day (NIOSH); no unacclimatised worker in high-risk work
     (ADPHC TG)"; High + heavy work → "OSH practitioner site assessment before heavy work; re-time heavy tasks away from the forecast's hottest hours (shown on the card)". No fixed clock window is claimed: none is sourced beyond the legal midday break.
  - Owner and deadline per action ("Supervisor, before 06:30").
- Does: taps **"Acknowledge plan"**. Next: confirmation with "Unacknowledged plans escalate to the OSH practitioner at 06:30"
  and next review time (tomorrow 18:00).

## Screen 5 — Why should I trust this? (from a link on Screens 2 and 4)
- Sees: plain-language evidence: tested on 2,628 US work heat hospitalisations; catches 79 % of reported heat days in 6
  regions it had never seen; what failed (workplace reports as a trigger); limits (US data, not validated on Abu Dhabi
  outcomes, May–Sep only, TWL not computed). Link to the full back-test.

## Screen 6 — Replay a real day (judge mode)
- Sees: date picker over May–Sep 2025 with suggested days ("hottest day", "early-season jump", "humid Gulf day",
  "a normal summer day"). Runs Screens 2–4 on that day's real weather.
- Why: judges test in late November, which is outside the tested season.

## Screen 7 — Regulator view (OSH specialist, aggregate)
- Sees: zones × tomorrow's tier; share of sites that acknowledged their plan; **simulated** incident notifications in the
  last 3 days shown as "check these workplaces" prompts (not a tier change; decision 1+5). Cells with fewer than 5 sites are
  suppressed. Banner: "No individual worker data. Not for employment or disciplinary use."
- Does: taps a zone → list of prompts. Next: export a short brief.

## What is real vs simulated in the demo
- Real: weather (ERA5 2015–2025, live forecast), the rule, thresholds, back-test numbers, legal texts.
- Simulated and labelled: sites, crews, acknowledgements, incident notifications.
