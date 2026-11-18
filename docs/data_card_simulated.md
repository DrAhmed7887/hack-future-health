# Data card: simulated workplace and service signals (v3 risk map)

**What it is.** Per zone and per day: number of sites, plans acknowledged, sites with a cooling station ready, sites with new or
returning workers, sites with heavy outdoor work planned, and incident notices in the last 3 days. Used by the risk map
(`web/dash.js`), the alerts (`web/alerts.js`) and the regulator view.

**What it is not.** Not real data, not drawn from any source, and not calibrated to Abu Dhabi. No relationship between these
numbers and the weather is modelled: they are drawn independently of heat. They exist to show the workflow (who is told, what
they do, when it escalates), not to support any claim. Every number from this file is labelled "Simulated" in the app.

**How it is made.** Seeded and deterministic: the key `zone|date` is hashed (FNV-1a) and fed to a mulberry32 generator
(`simSignals` in `web/alerts.js`), so the same zone and day always give the same numbers on every device and in the tests.

| Field | Rule | Range |
|---|---|---|
| `sites` | Fixed per zone: Mussafah 12, Abu Dhabi city 9, Ruwais 4, Al Ain 7 (as in v2); from v4 also Al Taweelah 10, Al Wathbah 6, Sweihan 3, Madinat Zayed 5, Ghayathi 3, Liwa 4 (illustrative) | — |
| `acked` | round(sites × U(0.6, 1.0)) | 60–100 % of sites |
| `cooling` | round(sites × U(0.4, 1.0)) | 40–100 % of sites |
| `newWorkerSites` | floor(sites × 0.35 × U(0, 1)) | 0–35 % of sites |
| `heavySites` | round(sites × U(0.3, 0.8)) | 30–80 % of sites |
| `notices3d` | 1 with probability 0.07, else 0 | 0 or 1 |

**Privacy.** Zones with fewer than 5 sites (Ruwais) show no site counts, no preparedness alert and no incident-notice alert
(small-cell suppression, as in v2). There is no person-level field.

**App rules that use it (operational, not clinical; not tested on outcomes).**
- *High risk, low preparation* alert: a heat alert on a High or Elevated day (not on a no-forecast day, where the heat alert already plans as Elevated) **and** fewer than 75 % of sites with a cooling
  station ready **or** fewer than 80 % of plans acknowledged. Thresholds are our choice for the demo.
- Escalation: an unacknowledged heat alert passes from the site supervisors to the OSH practitioner at 06:30 (as in v2), and to
  the ADPHC OSH zone officer at 09:00 (new in v3). A preparedness alert passes to the ADPHC OSH duty manager at 09:00. These roles
  and times are proposals for the pilot.
- Incident notices raise a "check that workplace" alert and **never** change the heat level (that use failed its pre-registered
  test; README, "What did not work").

## Simulated health signal (v4): heat-illness emergency-department visits

**What it is.** One daily count per zone, 21 Apr to 30 Sep 2025 (10 run-in days before the May–September replay), in
`web/health.js` (`simulate`). It feeds the EARS C2 flag (rules E1–E6 in `docs/evidence_v3_signals.md`, signed 18 Nov 2026).

**What it is not.** Not real visits and not modelled on heat: no public daily series of heat-illness visits exists for Abu
Dhabi zones. The counts are drawn independently of the weather, so the app makes no claim that heat caused them.

**How it is made.** Seeded (`zone|health`, FNV-1a + mulberry32). Background: Poisson with an illustrative daily rate
(Mussafah 1.5, Abu Dhabi city 1.2, Ruwais 0.6, Al Ain 1.0, Al Taweelah 0.9, Al Wathbah 0.7, Sweihan 0.4, Madinat Zayed 0.5,
Ghayathi 0.3, Liwa 0.4). Three clusters per zone are injected on purpose, one in each
~5-week window from 1 June, each 3 days long with +5, +6 and +4 extra visits.

**What the app shows.** The C2 score and the flag. A count under 5 is never shown ("Fewer than 5"), the usual small-cell rule
for health data. The Evidence page reports how the flag did on this simulation (injected clusters caught, flags on other
days); because the clusters were made easy to see, that number checks the code, not real-world performance.

## Dust (v4): real modelled data, not simulated

Daily mean PM10 per zone from the Open-Meteo Air Quality API (CAMS, CC BY 4.0): summer 2025 in
`web/data/dust_replay.json` (`scripts/build_dust_replay.py`), and tomorrow's forecast in `web/data/live.json` (nightly
`scripts/refresh_live.py`). Mussafah and Abu Dhabi city fall in the same CAMS grid cell, as do Ruwais and Ghayathi, so each pair shares values. CAMS accuracy
over Abu Dhabi was not checked here. Thresholds (D1–D6) were signed on 18 Nov 2026 and are not tested on outcomes.

**In the pilot** these would be replaced by real feeds: plan acknowledgements and cooling-station check-ins from the app itself,
and ADOSH-SF incident notifications by zone and day.
