# For judges: each criterion and where its evidence is

**Try it (no login):** https://drahmed7887.github.io/hack-future-health/. Outside May–September, tap "Replay a day" to see a real summer day.

**Headline result:** in 6 US regions never used in tuning (2022–2025), the relative rule alerted on **79.1 %** of days with a reported work heat hospitalisation (95 % CI 69.6–87.9). It did this while alerting on **49 %** of days; the common fixed trigger (heat index ≥ 80 °F) alerted on 82 %. Source: `results/holdout_results.json`. Limits are below and in the README.

Every number here comes from a script output in `results/`. The README is the single source for claims; this page only points to them.

| Criterion (challenge wording) | Evidence | Where |
|---|---|---|
| **Health impact and clinical relevance** | Real outcome data: 2,628 work-related heat hospitalisations (US OSHA Severe Injury Reports, 2015–2025), each matched to that day's weather. A collapse card ("cool first, transport second"), with its wording signed by a physician and backed by sources. Expected impact: fewer severe heat illness cases and lost workdays (to be measured in the pilot). | README "How it was tested", "From warning to survival", "Expected impact"; `docs/evidence_pack.md`; `docs/signoff.md` |
| **Technical depth and architecture** | A rule ranked against local climate, pre-registered and tuned on 2015–2021, then scored once on later data. A trained model was tested too; it missed the pass mark set before scoring, so the app keeps the rule. A day-ahead forecast check: same decision as observed weather on 84 % of region-days. | `docs/backtest_protocol.md`, `docs/protocol_v3_relative.md`, `docs/protocol_v4_trained_model.md`; `results/`; `heatwarn/`; `docs/workflow.png`, `docs/diagram/workflow.svg` |
| **Working solution and demonstration quality** | A live static app, refreshed every evening by a scheduled forecast job. Automated tests run in CI on every push. | Live link above; `.github/workflows/tests.yml`, `refresh-live.yml`, `deploy-pages.yml`; `tests/`, `web/tests/`; README "Reproduce" |
| **Responsible AI, safety and data governance** | No worker names, health data or job histories. The regulator view is aggregated by zone, with zones under 5 sites hidden. It never clears anyone to work. Failures are reported, not hidden, and limits are stated. | README "Privacy and governance", "What did not work", "Limits"; `docs/claims_audit.md`; `docs/stress_round.md` |
| **Scalability and deployment readiness** | A static site (GitHub Pages) with no app server or database; one forecast a day from Open-Meteo (CC BY 4.0), fetched by a scheduled GitHub Action. Stale or missing data shows "Not enough data" and is treated as Elevated. | `web/`; `scripts/refresh_live.py`; `web/logic.js` (`STALE_HOURS`); README measures table |
| **Commercial viability and path to pilot** | Target pilot partner: ADPHC (no agreement or contact yet). A shadow-mode pilot in summer 2027, the first heat season with outcomes to measure. Large-employer integrations come later. | Submission business plan and deck (path-to-pilot slide); README "Expected impact" |

## Limits (from the README)

- US data, reported cases only; most cases go unreported. Not validated on Abu Dhabi outcomes: local shadow-mode validation comes first.
- 86 event days in the transfer test, so intervals are wide. The sensitivity gain over fixed thresholds (+8.1 points, 95 % CI −6.9 to +24.3) is not statistically clear.
- Decision support for supervisors. Not a diagnosis, not a medical device, never a clearance to work.

## Reproduce

```bash
uv run pytest -q && node --test web/tests/logic.test.js
```

The full pipeline, which rebuilds every number from the raw data, is listed in the README under "Reproduce".
