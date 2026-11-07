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
