# Assistant prompt: smoke test (18 Nov 2026)

Two questions, one run each, with Claude Haiku 5.5 (`claude -p --model claude-haiku-5-5`; the model was confirmed from
`modelUsage`). Prompt: `prompts/supervisor_assistant.md` plus the 26 Jun 2025 replay data for Al Ain, built by
`node cli/heatwarn.js prompt`. This is a smoke test, not an evaluation: two answers, one model, no scoring panel.

What it showed:
- An earlier prompt let the model read "tomorrow" as the real current date (November), so it said the replay day did not
  apply and left out the High level. Rule 1 now pins the day to the date in the data. The answer below is from after that fix.
- The emergency answer printed the card word for word in English (checked by script against `EMERGENCY_STEPS` in
  `web/logic.js`), then an Arabic translation, then stopped.
- The planning answer ran to 217 words against the 150-word rule. Every action had an owner and a deadline, and the simulated
  parts were named.

## 1. "My crew pours concrete from 11:00 to 15:00 tomorrow. What do I need to do?"

**Al Ain: High heat, new today (2025-06-26).** Your 11:00–15:00 pour covers the hottest hours; heat peaks around 13:00.

**Actions**
- **Before 06:00:** set up a shaded cooling station (tub or tarp, water, ice, towels) and name who runs it. Owner: Supervisor.
- **Before the shift starts:** check every crew member for symptoms, sleep and fluids. Owner: Supervisor.
- **By 06:30:** acknowledge the plan. Owner: site supervisors. Escalates to the OSH practitioner at 06:30 and the ADPHC OSH zone officer at 09:00.
- **Before heavy work starts:** get a site heat assessment. Owner: OSH practitioner.
- **When setting the shift plan:** move heavy tasks away from 13:00. Owner: Supervisor. The data doesn't say whether a pour can move; ask your OSH practitioner.

**Cooling-station gap:** only 3 of 7 Al Ain sites have a station ready (simulated). ADPHC OSH zone officer calls sites by 07:00 and checks sites planning heavy work by 10:00. Escalates to the ADPHC OSH duty manager at 09:00.

Whether your site has a station ready is not in today's data; ask the ADPHC OSH zone officer.

Always: water, shade, rest, a buddy, and report symptoms at once.

Sites, crews, acknowledgements and cooling stations are simulated for the demo.

Decision support, not a clearance to work. Tested on US data; not yet validated in Abu Dhabi.

## 2. Arabic: a worker is confused and talking strangely after working in the sun. What do I do?

1. Stop their work and move them into the shade.
2. Call 998 now. Say "suspected heat stroke".
3. Start cooling now. Don't wait for the ambulance. Put them in cold water up to the neck with someone holding their head out of the water, or cover their whole body with towels or sheets soaked in ice water and swap them as they warm.
4. Keep cooling until the medics take over. Tell them what time cooling started.
5. Give no drinks to anyone confused or drowsy.

**الترجمة:**

1. أوقف عمله وانقله إلى الظل.
2. اتصل بالرقم 998 الآن. قل "اشتباه بضربة شمس".
3. ابدأ التبريد الآن. لا تنتظر سيارة الإسعاف. ضعه في ماء بارد حتى مستوى الرقبة مع شخص يُبقي رأسه فوق الماء، أو غطِّ جسمه كله بمناشف أو أغطية مبللة بماء الثلج، وبدّلها عندما تسخن.
4. واصل التبريد حتى يتولى المسعفون الأمر. أخبرهم بالوقت الذي بدأ فيه التبريد.
5. لا تُعطِ أي مشروب لمن يبدو مرتبكًا أو مُثقلًا بالنعاس.
