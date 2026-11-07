# Stress round 1 (7 Nov 2026, local build, commit after c198625)

The app is static (no server, no paid API, no user data sent anywhere), so the template's load/spend/rate-limit rows apply
to the hosting CDN only and are re-checked on the live URL. Hostile and broken inputs were run in the browser:

| Check | Result |
|---|---|
| Corrupt saved site (`<img onerror>` in storage) + unknown route | site picker shown, no error |
| All 5 tiers × crew answers (yes/no/unsure/unanswered)² = 80 plans | 80 rendered, none empty, 0 errors |
| Live entry missing percentile, anomaly, peak hour | "Air temperature up to 40 °C." — no crash |
| No live entries at all | "No forecast for this site yet" + law and always-on protections |
| Forecast older than 36 h | "Not enough data — treat as Elevated" (node test + browser) |
| HTML injected into a zone name | escaped |
| Replay date outside May–Sep 2025 | falls back to 15 Jul 2025 |
| Data files missing | "The forecast data did not load" message |
| Console errors during the round | 0 |

Still to run on the live URL: 10 parallel sessions, cold load on a phone over 4G, data files cached correctly, logged-out access.

## Live URL (7 Nov 2026, https://drahmed7887.github.io/hack-future-health/, checked logged out with curl)
| Check | Result |
|---|---|
| Site files (index, css, logic, app, 3 data files) | all 200 |
| Non-site files (tests, reference.json, repo paths) | 404: only the site is deployed |
| 10 parallel cold loads of index + replay data (20 requests) | 20/20 = 200, max 0.23 s, mean 0.11 s |
| Cache | `cache-control: max-age=600`; the app fetches data with `no-store`, so a refresh is at most 10 min behind the CDN |
| Live data through the app logic (node) | 4 zones: "Outside tested season" (November), legal layer correct |
| Cost per visitor | none: visitors load static files; only the daily job calls the weather API |
Not checked here: a real phone over 4G (the browser pane disconnected). Ahmed to open the link on his phone.

## Live URL (7 Nov 2026, https://drahmed7887.github.io/hack-future-health/)
- Deployed by `.github/workflows/deploy-pages.yml` (site files only: no tests, raw data or reference climatology). Code repo stays private.
- No login: `curl` without credentials returns 200 for every file; tests path returns 404.
- Total payload about 134 kB; each file 0.19–0.30 s from Valencia. 20 parallel cold loads of the largest file: 20 × 200, all under 0.2 s.
- Judge path in a fresh browser: site → replay hottest day (High) → crew yes/yes → 5-step plan → acknowledge → evidence (79 %, 82 %, 25 vs 82, 84 %). 0 console errors.
- Live day shows "Today" after midnight Abu Dhabi time until the 18:00 refresh (resolver behaviour, as designed).
