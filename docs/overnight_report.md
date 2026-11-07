# Overnight report, 7 Nov 2026 (automated run, Claude Code)

Scheduled task "future-health-claims-audit-video-plan". Gates held: the repo stays private, nothing was submitted, sent, posted
or recorded, the name is unchanged, and no rule, threshold, results file or protocol was touched. No paid API was used.

## What I did
1. **Claims audit (Phase 4):** `docs/claims_audit.md`. Every claim in README, app UI text, `index.html` and both diagrams was traced to
   `results/*.json`, a script or the evidence pack. All numbers match. 15 wording fixes, 4 items for Ahmed.
2. **Video plan:** `docs/video_plan.md` (video-director agent, DRAFT). 12 shots, 2:05, 299 words. The Mussafah 1 Aug 2025 replay opens
   the film. Every validation number lands in the first ~70 s, including what failed. It also covers the legal layer, crew answers
   (shown on 7 Jul 2025, because 1 Aug is already High and cannot rise), the regulator view and the limits. It closes on
   "79 percent, in regions it had never seen. Not yet validated in Abu Dhabi." Capture is planned as phone-size Playwright stills
   in a 16:9 frame. Nothing was recorded.
3. **Leak scan:** `docs/prepublish_scan.md`. **CLEAN** (38 commits, exit 0). Raw data is not tracked.
4. **Organiser email:** a draft only, in Drive `Zayed OS/Hackathons/2026-11-future-health/organiser_email_draft.md`. Not sent.
5. **Live site:** redeployed by `deploy-pages` after each push; the corrected text was confirmed on the live URL. CI tests pass.

## Fixes (all wording or display; tests 18 + 15 passing before each push)
| Commit | Fix |
|---|---|
| 937d848 | README and g1b: tuning regions are TX, FL, OK and MO (not "Texas and Florida"); "Pittsburgh area"; logged bootstrap bug-fix re-run disclosed; `score_dayahead_r4.py` added to Reproduce; the workplace result names the rule it was compared with (earlier fixed-threshold R2, 8 original regions); "no answer counts as yes"; regulator hides **site counts** below 5 sites, not zones |
| 937d848 | App: refresh "scheduled for 18:00 Abu Dhabi time" (not a promise); 06:30 escalation "would go … (this demo sends nothing)"; Evidence: "the heat hospitalisations reported … Jan 2015 to Nov 2025" (not "every"); "same training alert budget"; softened two unsourced phrases; meta "ranked against local climate" (not "locally calibrated"); NIOSH owner line says the 20 % schedule is NIOSH's for new workers and using it for returning workers is stricter (advice unchanged) |
| 937d848 | Diagrams: 4:5 "Scheduled each evening at 18:00"; 16:9 regulator box "site counts hidden below 5 sites"; both PNGs re-rendered and checked |
| 048924e | `docs/claims_audit.md` |
| ce934ab | Evidence screen shows README precision: 79.1 % (69.6–87.9) and −11.6 (−17.7 to −5.8) instead of 79 % / −12 (flagged by video-director; values unchanged) |
| 9e1e745 | `docs/video_plan.md` (draft) and `docs/prepublish_scan.md` |

## Needs Ahmed (one line each)
- Shade line cites "ADPHC CoP 11.0 §3.2(b)", but the evidence pack has no shade or shelter quote: add the quote or change the citation.
- The first-aid line and "998" have no quote in the evidence pack, and the u.ae page returned 404: add the TG quote and an official 998 source.
- Returning workers get NIOSH's new-worker 20 % schedule, but signed S4 says returning workers follow NIOSH separately (50/60/80/100 %): keep the stricter single schedule or split them.
- Approve the video plan, or change it; its section 5 has 11 open questions (voice: his own recommended; name on screen; S9 on 7 Jul; music; end-card URL; acknowledge time; health-impact line).
- Check the Hack2skill portal for the video format rules, then edit and send the organiser email (remote GITEX pitch; deadline time zone).
- Before G5: 36 commits carry `[author email, removed before publishing]` as author email, which becomes visible once the repo is public. Keep it, or switch to noreply before going public (that needs a history rewrite and a new remote).
- Final product name (still "Heat Shift Planner (working name)").

## Next step
Ahmed resolves the three citation items (or accepts them as is) and approves `docs/video_plan.md`. Then capture runs from the live
site with Playwright per the plan, followed by a contact sheet and G4 (he watches it with sound).
