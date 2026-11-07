# Demo video plan: Heat Shift Planner (working name)

**DRAFT: awaiting Ahmed's approval before any recording.** Nothing in this plan has been recorded, rendered or voiced.

Written 7 Nov 2026. Sources: `README.md` (the only source of claims), `docs/claims_audit.md`, `docs/user_flow.md`,
`docs/g1b_relative_results.md`, `web/app.js`, `web/logic.js`, `web/data/replay.json`, `web/data/evidence.json`, `docs/workflow.png`.
I checked that the deployed `app.js` and `logic.js` on the live URL match the local files byte for byte (7 Nov).

---

## 1. Intent and audience

The film is for the Department of Health Abu Dhabi panel: a clinician, a regulator, an AI reviewer and a commercial reviewer,
who will have watched many entries back to back. Most of them will assume a heat alert is a weather app with a threshold on it.
The one belief to shift: **this rule was tested before it was shown. It was frozen first, scored once on US regions it had never
seen, and the film says plainly what failed and where it stops.** The one thing to remember tomorrow: *79.1 % of reported-case days
caught in six unseen regions, alerting on 49 % of days, with the law shown first and nothing that clears anyone to work.* The
strongest artifact is the Evidence screen, and within it the "What did not work" paragraph. Any team can show a good number. Few
will show a pre-registered idea that failed. So the film opens on one real day (the Mussafah replay, 1 Aug 2025), puts every
validation number in the first ~70 s, then shows the plan changing as the crew answers change, the regulator view and the limits.
It closes on the 79.1 % figure and where that figure stops applying. Voice: calm, plain, first person. No music swell, no
"AI predicts", no claim of winning, no patient data. The banner on every screen already says sites, crews and incident notices are
simulated, and the narration repeats it once.

**Runtime: 2:05 (302 spoken words, about 145 wpm).** To get under 2:00, use the cut list at the end of section 2.

---

## 2. Shot list

Format: 1920×1080 final. Each app frame is a phone capture (360×640 CSS px at 3× = 1080×1920) placed full height in the
left third. The right two-thirds hold the overlays and the burned-in captions (section 3 explains why).
Two camera moves in the whole film (S4 and S8). Every other shot is a locked frame or a hard cut.
Overlays use ink and grey only. Red and yellow appear only where the app itself uses them for tiers.

Every app string quoted below comes from `web/app.js` / `web/logic.js` for the stated state. Every overlay number comes from
`README.md`. **Gate G1 (section 5, Q1) has to be settled before S4, S6 and S12 are captured.**

| # | Start–end | Screen / URL + exact capture actions | On-screen text / caption overlays | Narration (verbatim) |
|---|---|---|---|---|
| S1 | 0:00–0:13 | `#replay` → zone select `#rz` = Mussafah → click `[data-day="2025-08-01"]` (label "Hottest day: Fri, 1 Aug 2025") → lands on `#home`. Locked frame on the zone bar, the replay line, the tier card and the why-sentence with the strip. App shows: "Replay of a real day: Fri, 1 Aug 2025." · "That day" · **High** · "Hotter than most days here at this time of year. Extra steps are in the plan." · why: "Air temperature up to 45 °C. Heat and humidity together peak around 14:00. On that combined measure, it is as hot as the hottest days here at this time of year in 2015 to 2021, and 11 °C above the previous 14 days." | Top right: **Mussafah · Fri 1 Aug 2025 · real weather (ERA5)**. Thin ink underline under "as hot as the hottest days … 2015 to 2021" and "11 °C above the previous 14 days" as each is spoken. No product name yet. | Mussafah, the first of August 2025. Heat and humidity together: as hot as the hottest days there at this time of year, and 11 degrees above the previous 14 days. |
| S2 | 0:13–0:19 | Same `#home` state, cut to the top of the page so the app header "Heat Shift Planner" and the demo banner ("Demo. Sites, crews and incident notices are simulated. Weather and the rule are real.") are in frame. | Lower third: **Heat Shift Planner (working name)** / **Ahmed Zayed, physician** (wording: Q6). | Heat Shift Planner turns that into tomorrow's plan for site supervisors in Abu Dhabi. |
| S3 | 0:19–0:28 | Navigate to `#site` (no click on a zone). App shows: "Where does your crew work? Each zone's days are ranked against its own weather in 2015 to 2021. The cut-offs were tested on US data." with the four zones. | Right panel, one held card: **Fixed thresholds tuned on the 8 original US regions → top tier on every Abu Dhabi day, June to September.** Source line (small): README, "Why a new rule was needed". | A fixed threshold tuned on eight US regions would put every Abu Dhabi day, June to September, in its top tier. |
| S4 | 0:28–0:49 | `#trust`. Open on the h1 "How was this tested?" and the first paragraph (it contains "(2,628 reports)"). **Camera move 1:** a slow push from the paragraph down to the first fact card at "Frozen, then scored once", landing on the big "79%" (the app's rounding; see G1). | 0:30 **2,628 work-related heat hospitalisation reports · US OSHA · Jan 2015 – Nov 2025** · 0:38 **Tuned on 2015–2021 · frozen · scored once** · 0:42 **6 unseen US regions, 2022–2025 · 86 days with a reported case** · 0:45 **79.1 % caught (95 % CI 69.6–87.9) · 49 % of days alerted** · small, from 0:46: **Gain over fixed thresholds +8.1 points (95 % CI −6.9 to +24.3): not statistically clear.** | Abu Dhabi has no public data on work heat illness. So I tested on 2,628 heat hospitalisation reports from US federal OSHA. Frozen, then scored once in six US regions it had never seen: it caught 79 percent of reported-case days, alerting on 49 percent of days. |
| S5 | 0:49–0:56 | `#trust`, hard cut to the fourth fact card ("84%": "…the same decision from the forecast made the evening before … The forecast ran warm, so it alerted on more days (59% against 51%)."). | **Same decision on 84 % of region-days · forecast issued the evening before · 8 US regions, 2024–2025** · second line: **Forecast ran warm: alerted on 59 % vs 51 % of days.** | On the evening-before forecast: the same decision as the real weather on 84 percent of days. |
| S6 | 0:56–1:10 | `#trust`, cut to the h2 "What did not work" and its paragraph in full. Hold. **This is the proof beat: no motion, nothing else on screen.** | **Workplace-trigger rule vs the earlier fixed-threshold rule: −11.6 points (95 % CI −17.7 to −5.8)** · small: **Two separately tuned rules, same training alert budget, 8 original US regions, 2022–2025. Not the reports' isolated value.** | I expected recent incident reports to help. A rule using them as a trigger caught 11.6 points fewer heat days than the earlier fixed-threshold rule. So they only prompt a check. |
| S7 | 1:10–1:20 | Back to `#home` (the replay state persists in memory). Cut to the section "Required by law, whatever the forecast": "Midday break: no outdoor work in direct sun from 12:30 to 15:00." · "Air temperature reached 45 °C. At 35 °C or more, your site's heat stress programme applies." · "Abu Dhabi's heat stress index (Thermal Work Limit) needs on-site readings. This app does not calculate it." | Ink bracket beside the three items, labelled **Shown whatever the model says**. Source lines are already on screen in the app (MoHRE; ADPHC CoP 11.0 §3.1.1(e); ADPHC TG Safety in the Heat). | Whatever the forecast, the law shows: the midday break, and the heat stress programme from 35 degrees. The Thermal Work Limit is not calculated. |
| S8 | 1:20–1:35 | `#crew` with both questions answered **No** (pre-set during capture). Four cuts, each on a tap: **(a)** tap Heavy work **Yes** → **(b)** `#plan`, model layer "Because of the forecast and your crew": new line "Move heavy tasks away from the hottest hours (heat peaks around 14:00)." → **(c)** `#crew` tap New or returning workers **Yes** → **(d)** `#plan`: two new lines, "New or returning workers: no more than 20% of the usual heat exposure on day 1, adding 20% a day." and "No unacclimatised worker in medium or high risk heat work." **Camera move 2:** a gentle push on (d) only, onto the two new lines. | Thin ink box round each line as it appears (no colour). Top right: **Same day, same weather: the crew answers change the plan.** Small, on (d): **Crew rules come from guidelines (NIOSH 2016; ADPHC). Not tested on outcomes.** The status line "Based on guidelines and a heat rule tested on US data. Not yet validated in Abu Dhabi." must stay in frame. | Heavy work planned? Yes adds: move heavy tasks away from the 2 p.m. peak. New or returning workers? Yes adds the acclimatisation steps: 20 percent of usual heat exposure on day one, adding 20 percent a day. |
| S9 | 1:35–1:44 | Second capture session: `#replay` → `#rd` = 2025-07-07 → "Show this day" → crew No/No → `#plan`: **No extra steps**, model layer "No extra steps from the forecast." with the law block in the same frame (35 °C programme applies; 38.2 °C reached). Cut → crew New or returning workers **Yes** → `#plan`: **Elevated** and the status line "Raised one level from No escalation because the crew may include new or returning workers. This is our rule, based on guidelines, not tested on outcomes." | **Mon 7 Jul 2025 · Mussafah · replay** · on the second frame: underline "This is our rule, based on guidelines, not tested on outcomes." | On the seventh of July, the forecast adds no steps. The same yes raises the tier one level, labelled as our rule. |
| S10 | 1:44–1:52 | Back to session 1 (replay date 1 Aug 2025). `#regulator`: "Regulator view" · "Zones, not people. Fri, 1 Aug 2025 (replay)." Four zones: Mussafah High, "Plans acknowledged: 9 of 12 sites", "1 incident notice in the last 3 days. … This does not change the tier." · Abu Dhabi city High, 6 of 9 · Ruwais High, "Fewer than 5 sites in this zone, so site counts are hidden." · Al Ain High, 5 of 7, 1 notice. Footer: "Sites, acknowledgements and incident notices are simulated for the demo. …" | **SIMULATED: sites, acknowledgements, incident notices** (top right, held for the whole shot). Underline the Ruwais line and "This does not change the tier." | The regulator sees zones, not people. Below five sites, site counts are hidden. Sites and notices here are simulated. |
| S11 | 1:52–1:59 | `#trust`, cut to the h2 "Limits" and its paragraph. Locked. | Four short lines, one per beat: **US data, reported cases only · Not validated on Abu Dhabi outcomes · Tested May to September only · Not a medical device. Never a clearance to work.** | Limits: US data, May to September only, not a medical device, never a clearance to work. |
| S12 | 1:59–2:05 | Return to the S4 end frame (the first fact card), locked, with the app dimmed to 40 % behind the overlay. Hold 1.5 s of room tone after the last word. | Large: **79.1 %** · under it: **of reported-case days caught · 6 US regions it had never seen · 49 % of days alerted** · then: **Not yet validated in Abu Dhabi.** · small, bottom: **drahmed7887.github.io/hack-future-health** | 79 percent, in regions it had never seen. Not yet validated in Abu Dhabi. |

Pronunciation: Mussafah = moo-SAF-fah · OSHA = OH-sha · acclimatisation = a-KLY-ma-tie-ZAY-shun · "11.6" = "eleven point six".
Captions are typed from the narration column above. Never auto-transcribe them from the voice track.

**Words per shot (spoken, numbers read out):** S1 31 · S2 14 · S3 21 · S4 52 · S5 16 · S6 33 · S7 24 · S8 37 · S9 22 · S10 19 ·
S11 16 · S12 14 = 299 words over 125 s. Every shot is at 137–149 wpm.

**Cut list, if it must come in under 2:00:** (1) drop the S3 narration and keep its card under silent room tone for 4 s (saves 5 s).
(2) Drop "Below five sites, site counts are hidden" from S10, since the underline carries it (saves 2 s). Do **not** cut S6 or S9.
They are the credibility of the film.

**What the film deliberately leaves out:** the workflow diagram (it is plumbing; it belongs in the submission document), the
Always-on block on the plan screen (two citations there are still open in `claims_audit.md`, see Q3), the live `#home` in
November (it shows "Outside tested season", which is correct but costs time), the PPV column (3.8 %: reported-event PPV is
misleading without the under-reporting caveat, and 2 minutes has no room to explain it; it stays in the document) and any
health-impact figure (the README has none, so the film claims none).

---

## 3. Playwright capture outline (not run; for review)

**Viewport: phone, 360×640 CSS px, deviceScaleFactor 3 (1080×1920 per frame), isMobile, hasTouch.**
Why: the primary user is a supervisor on a phone on site (`docs/user_flow.md`), and the layout is phone-first (`main` max-width
520 px). At 1280×800 the app is a narrow column in a mostly empty frame, with small text. A 3× phone frame scaled to 1080 px tall
puts the 16 px body text at about 27 px in the final 1080p film, readable on a judge's laptop. The empty right two-thirds become
the overlay and caption space, so overlays never cover app text. Stills beat screen video here: Playwright's `recordVideo`
records at CSS resolution (360×640, blurry). So capture DPR-3 screenshots and build the motion in the edit.

```js
// OUTLINE ONLY. Do not run until Ahmed approves the plan.
const BASE = "https://drahmed7887.github.io/hack-future-health/";
const OUT = "<capture folder outside the repo>";      // not committed

const ctxOpts = {
  viewport: { width: 360, height: 640 }, deviceScaleFactor: 3, isMobile: true, hasTouch: true,
  locale: "en-GB", timezoneId: "Asia/Dubai", colorScheme: "light", reducedMotion: "reduce",
};
// recall() does JSON.parse, so the stored value must be a JSON string: "\"mussafah\"", not "mussafah".
const seedZone = () => localStorage.setItem("zone", JSON.stringify("mussafah"));

async function ready(page) {                       // after every navigation or re-render
  await page.waitForSelector("#app h1, #app .tier");
  await page.evaluate(() => document.fonts.ready);  // Atkinson Hyperlegible + Barlow Condensed from Google Fonts
}
const go = (page, hash) => page.evaluate(h => { location.hash = h; }, hash);   // keeps in-memory replay state
const shot = (page, name, opts = {}) => page.screenshot({ path: `${OUT}/${name}.png`, animations: "disabled", caret: "hide", ...opts });
const answer = (page, q, v) => page.click(`label:has(input[name="${q}"][value="${v}"])`);   // inputs are opacity 0, pointer-events none
const checked = (page, q, v) => page.waitForSelector(`input[name="${q}"][value="${v}"]:checked`);

// ---- Session 1: Mussafah, Fri 1 Aug 2025 (S1–S8, S10–S12) ----
// ctx = browser.newContext(ctxOpts); ctx.addInitScript(seedZone); page = ctx.newPage()
// 1  goto BASE + "#replay"; ready; assert #rz value === "mussafah"
// 2  click '[data-day="2025-08-01"]'   (the "Hottest day" button; "Biggest jump" is the same date and is de-duplicated)
//    wait hash "#home"; ready
//    assert '.tier .word' === "High"; assert '.why' contains "as hot as the hottest days" and "11 °C"  (non-breaking spaces)
//    shot S1_home (viewport). Also fullPage for the contact sheet.
// 3  scroll to top; shot S2_header (header + demo banner + tier)
// 4  go "#site"; ready; shot S3_site            // do NOT click a zone
// 5  go "#trust"; ready; shot S4a_trust_top; fullPage shot S4_trust_full (the source for the push-in)
//    locator('.facts > div').nth(0).scrollIntoViewIfNeeded(); shot S4b_fact79
//    locator('.facts > div').nth(3) → shot S5_fact84
//    locator('h2', { hasText: "What did not work" }) scroll to top of viewport → shot S6_failed
//    locator('h2', { hasText: "Limits" }) → shot S11_limits
//    save page.innerText('#app') to S4_trust.txt (for the number check in section 4)
// 6  go "#home"; ready; locator('.legal').scrollIntoViewIfNeeded(); shot S7_law
//    assert text contains "12:30 to 15:00", "Air temperature reached 45 °C", "does not calculate it"
// 7  go "#crew"; ready
//    answer newWorkers no; checked; answer heavy no; checked        // each change re-renders the view
//    shot S8_crew_nono
//    click '.cta .btn:not(.secondary)'  ("See the plan"); wait h1 "The plan for that day"; ready
//    locator('.layer.model') scroll to top; shot S8_plan_nono   (expect 2 steps: crew check; OSH assessment)
// 8  go "#crew"; answer heavy yes; checked; shot S8a_crew_heavy
//    go "#plan"; ready; shot S8b_plan_heavy   (expect "Move heavy tasks away from the hottest hours (heat peaks around 14:00).")
// 9  go "#crew"; answer newWorkers yes; checked; shot S8c_crew_new
//    go "#plan"; ready; shot S8d_plan_new     (expect the two acclimatisation lines; expect NO ".status" "Raised one level":
//    High is already the top tier, see Q2)
//    Optional: click '.cta .btn:not(.secondary)' (Acknowledge plan) → '.ack' "Plan acknowledged at HH:MM … (this demo sends nothing)."
//    The time is the real capture clock (Q11). Do not fake it with page.clock.
// 10 go "#regulator"; ready; assert "Fri, 1 Aug 2025 (replay)"; assert Ruwais row has "Fewer than 5 sites"
//    shot S10_regulator (viewport) + fullPage; save innerText
// ctx.close()

// ---- Session 2: Mussafah, Mon 7 Jul 2025 (S9) ----  a fresh context, so crew answers start empty
// 1  goto BASE + "#replay"; ready; fill '#rd' "2025-07-07"; click '.cta .btn' ("Show this day"); wait "#home"; ready
//    assert '.tier .word' === "No extra steps"
// 2  go "#crew"; answer newWorkers no; answer heavy no; go "#plan"; ready
//    assert "No extra steps from the forecast."; the law block must show in the same frame → shot S9a_plan_none
// 3  go "#crew"; answer newWorkers yes; checked; go "#plan"; ready
//    assert '.tier .word' === "Elevated"; assert '.status' contains "Raised one level from No escalation"
//    shot S9b_plan_raised
// ctx.close(); browser.close()        // close everything (8 GB RAM)
```

Waits: the rendering is synchronous, but every hash change and radio change replaces `#app`'s HTML. Wait on a selector or text
that only exists after the re-render (`:checked`, the h1 text), never on a fixed timeout. The only fixed waits allowed are
`document.fonts.ready` and one 300 ms settle after the first load.

---

## 4. Audio and finish checklist

- [ ] Gate G1 (Q1) settled, and the numbers on screen match the overlay in the same frame.
- [ ] Captured `#app` innerText for S1, S4–S7, S10 checked line by line against `README.md`: 2,628 · 79.1 % (69.6–87.9) · 49 % · 86 days ·
      6 regions · 84 % · 59 % vs 51 % · −11.6 (−17.7 to −5.8) · 45 °C · 11 °C · 14:00 · 12:30–15:00 · 35 °C · 5 sites. No other number appears.
- [ ] The wording audit is respected: "the earlier fixed-threshold rule", "this demo sends nothing", "scheduled for 18:00", "simulated".
- [ ] Narration recorded at 137–149 wpm per shot. Full stops held as real pauses. One weighted word only, "frozen" in S4. Everything else level.
- [ ] No silence longer than 4 s anywhere (the 1.5 s end hold in S12 counts). Room tone, not digital silence, under the gaps.
- [ ] Loudness: integrated about −16 LUFS, true peak ≤ −1 dBTP (measure with `ffmpeg -af loudnorm=print_format=summary`, or ebur128).
      No music, or a bed at least −20 dB under the voice with no swell (Q8).
- [ ] Captions burned in, typed from the verbatim narration (not auto-transcribed). Check the spellings Mussafah, OSHA, ADPHC,
      acclimatisation, Thermal Work Limit. An SRT file kept alongside.
- [ ] Contact sheet: one frame per shot, sampled at 25 % and at 90 % of each shot's length. Check for front-loading: overlays must
      appear on their spoken cue, not at the start of the shot.
- [ ] Key frames exported at full 1920×1080 and read at 100 %: S1 (tier + why), S4 end (79 %), S6 (failure paragraph), S8d (the plan
      after both Yes answers), S9b (raised one level), S10 (regulator), S12 (end card).
- [ ] Cuts: on S8 a→b→c→d and S9 a→b, the phone frame keeps exactly the same position and scale. Only the app content changes.
- [ ] The demo banner "Demo. Sites, crews and incident notices are simulated…" is legible in every app frame where it falls in view.
- [ ] Hostile screenshot check: S9a ("No extra steps" on a 38.2 °C day) must show the law block with "At 35 °C or more, your site's
      heat stress programme applies" in the same frame. No frame shows a green or "safe" state (the app has none). No frame shows
      the unsourced Always-on citations (Q3).
- [ ] No terminal, no GitHub, no code, no browser chrome. The URL appears only on the end card.
- [ ] Export: 1920×1080, 30 fps, H.264, AAC 48 kHz. Runtime 2:05 or less (or under 2:00 with the cut list). File name has no personal data.
- [ ] Watch it once muted and once eyes-closed. Muted, does every claim still land? Eyes closed, does any sentence depend on the picture?

---

## 5. Open questions for Ahmed

1. **RESOLVED 7 Nov (commit ce934ab): the Evidence screen now shows 79.1 % (69.6 % to 87.9 %) and −11.6 (−17.7 to −5.8), matching the README; overlays can copy the screen.** Original note: **G1, rounding (blocking for S4, S6, S12).** The Evidence screen rounds what the README states to one decimal. The screen shows
   79 % "(95% interval 70% to 88%)", where the README has 79.1 % (69.6–87.9). It shows "12 percentage points fewer … difference -12,
   95% interval -18 to -6", where the README has −11.6 (−17.7 to −5.8). With README overlays beside the app in the same frame, a
   viewer sees two different numbers. My recommendation is to show one decimal for these figures in the `trust()` view before
   capture: a small, display-only change to `web/app.js` (I did not edit it). The alternative is overlays that copy the app's
   rounded figures, with the README value in the source line. Your call.
2. **The tier raise cannot be shown on 1 Aug.** Mussafah is already High that day, and `effectiveTier` keeps High at High, so
   answering Yes adds the acclimatisation steps but shows no "Raised one level" line. S9 shows the raise on Mon 7 Jul 2025 instead
   (No escalation → Elevated, the app's own "not tested on outcomes" line). It doubles as the counter-case, the model not firing.
   Keep S9, or drop it and say the raise in narration only?
3. *(Resolved 7 Nov: both Always-on citations now have quotes in `docs/evidence_pack.md`; the block can be shown.)* 3. **The Always-on block has two citations still marked NEEDS AHMED** in `claims_audit.md`: shade and cooling shelters ("section 3.2(b)",
   no quote found) and the first-aid steps with 998 (no official source). The plan keeps that block out of frame. If you resolve
   them, S8 can show it.
4. **Returning workers in the NIOSH schedule** (also NEEDS AHMED). The owner line in S8d reads "NIOSH 2016 schedule for new workers;
   using it for returning workers too is stricter than NIOSH". That is honest as it stands. Keep it, or change it first?
5. **Voice: yours or TTS?** I recommend your own voice. A physician saying "I expected recent incident reports to help" carries the
   S6 beat better than a synthetic voice, and TTS tends to mangle Mussafah, OSHA and acclimatisation. If TTS: use the phonetic
   hints above, and type the captions by hand.
6. **Name on screen.** The lower third in S2 reads "Ahmed Zayed, physician". Keep it, add "MB BCh", or leave your name off? The product
   name stays "Heat Shift Planner (working name)" until you choose a final one.
7. **Format and length rules.** The FAQ says "full requirements are shared when you register". Please check the Hack2skill portal
   for the required aspect ratio, maximum length, and upload method (YouTube or Drive). This plan assumes 16:9, about 2 minutes.
8. **Music:** none (recommended), or a very low bed?
9. **End-card URL:** the Pages URL shows your GitHub username, and the repo itself is still private. Show the URL, or a QR code to
   the same address?
10. **S9 hostile reading:** a clinician may screenshot "No extra steps" on a 38.2 °C day. The plan keeps the law block in the same
    frame to answer that. Is that enough for you clinically, or would you rather drop S9 (see Q2)?
11. **Acknowledge button:** the confirmation shows the real clock time of capture ("Plan acknowledged at 10:42"). Capture in the
    evening so it fits the evening-before story, leave the button out, or keep any time?
12. **Health impact (challenge criterion 6):** the README has no impact figure, so the film makes no impact claim. Is that right, or
    is there a sourced line you want added to the README first?
