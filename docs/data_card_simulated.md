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
| `sites` | Fixed per zone: Mussafah 12, Abu Dhabi city 9, Ruwais 4, Al Ain 7 (as in v2) | — |
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

**In the pilot** these would be replaced by real feeds: plan acknowledgements and cooling-station check-ins from the app itself,
and ADOSH-SF incident notifications by zone and day.
