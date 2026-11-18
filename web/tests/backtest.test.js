// v4 back-test explorer: the frozen R4 rule against real US OSHA case days. Written before web/backtest.js.
const test = require("node:test");
const assert = require("node:assert");
const fs = require("node:fs");
const path = require("node:path");
const BT = require("../backtest.js");
const DATA = JSON.parse(fs.readFileSync(path.join(__dirname, "..", "data", "backtest.json"), "utf8"));
const HO = JSON.parse(fs.readFileSync(path.join(__dirname, "..", "..", "results", "holdout_results.json"), "utf8")).rules;

test("all regions, all years: the same totals as results/holdout_results.json", () => {
  const s = BT.summary(DATA);
  assert.equal(s.days, HO.R4.days);
  assert.equal(s.events, HO.R4.event_days);
  assert.equal(s.caught, HO.R4.tp);
  assert.equal(s.alertDays, HO.R4.alert_days);
  assert.equal(s.fixedAlertDays, HO.R1.alert_days);
});

test("per region and year, the parts add up to the whole", () => {
  const all = BT.summary(DATA);
  let caught = 0, events = 0, days = 0;
  for (const r of Object.keys(DATA.regions)) for (const y of BT.years(DATA)) {
    const s = BT.summary(DATA, r, y);
    caught += s.caught; events += s.events; days += s.days;
    assert.ok(s.caught <= s.events && s.alertDays <= s.days);
  }
  assert.deepEqual([caught, events, days], [all.caught, all.events, all.days]);
  assert.deepEqual(BT.years(DATA), [2022, 2023, 2024, 2025]);
});

test("a day carries its level, drivers and reports", () => {
  const r = Object.keys(DATA.regions)[0];
  const d = BT.day(DATA, r, DATA.regions[r].dates[0]);
  assert.ok(["High", "Elevated", "No alert"].includes(d.level));
  assert.ok(Number.isInteger(d.hi_f) && Number.isInteger(d.pctl) && Number.isInteger(d.reports));
  assert.equal(d.event, d.reports > 0);
  assert.equal(BT.day(DATA, r, "2021-07-01"), null);
});

test("the explanation names the rule's own reason", () => {
  assert.match(BT.why({ level: "High", hi_f: 98, pctl: 87, jump_f: 4.7 }), /87th percentile/);
  assert.match(BT.why({ level: "Elevated", hi_f: 92, pctl: 55, jump_f: 3.4 }), /3\.4 °F/);
  assert.match(BT.why({ level: "No alert", hi_f: 78, pctl: 20, jump_f: 0 }), /below 80 °F/);
  assert.match(BT.why({ level: "No alert", hi_f: 88, pctl: 40, jump_f: 1 }), /40th percentile/);
});

test("months grid lays out May to September of one year", () => {
  const r = Object.keys(DATA.regions)[0];
  const g = BT.months(DATA, r, 2024);
  assert.deepEqual(g.map(m => m.month), [5, 6, 7, 8, 9]);
  assert.equal(g[0].days.length, 31); assert.equal(g[1].days.length, 30);
  assert.ok(g.every(m => m.days.every(d => d === null || d.date.startsWith("2024-"))));
});

test("the shown values reproduce the level on every day (rounded down, never across a threshold)", () => {
  let bad = 0;
  for (const [k, r] of Object.entries(DATA.regions)) for (const date of r.dates) {
    const d = BT.day(DATA, k, date);
    const lvl = d.hi_f >= 80 && d.pctl >= 60 ? "High" : d.hi_f >= 80 && d.pctl >= 50 && d.jump_f >= 3 ? "Elevated" : "No alert";
    if (lvl !== d.level) bad += 1;
  }
  assert.equal(bad, 0);
});

test("the view draws one square per day, starts on a case day, and escapes names", () => {
  const v = BT.defaultView(DATA);
  const r = DATA.regions[v.region], i = r.dates.indexOf(v.date);
  assert.equal(r.event[i], "1");
  const esc = s => String(s).replace(/[&<>"']/g, c => `&#${c.charCodeAt(0)};`);
  const out = BT.html(DATA, v, esc, d => d);
  assert.equal((out.match(/data-btd=/g) || []).length, 153);   // 1 May to 30 September
  assert.match(out, /reported work heat hospitalisation/);
  assert.match(out, new RegExp(`${HO.R4.tp} of ${HO.R4.event_days}`));
});

test("firstCase finds the first case day of a region and year, or none", () => {
  const r = Object.keys(DATA.regions)[0], y = 2022;
  const d = BT.firstCase(DATA, r, y);
  if (d) { assert.ok(d.startsWith("2022-")); assert.equal(BT.day(DATA, r, d).event, true); }
  assert.equal(BT.firstCase(DATA, r, 2019), null);
});

test("stepCase walks the case days of one year and wraps round", () => {
  const v = BT.defaultView(DATA);
  const r = DATA.regions[v.region];
  const cases = r.dates.filter((d, k) => d.startsWith(String(v.year)) && r.event[k] === "1");
  assert.equal(BT.stepCase(DATA, v.region, v.year, cases[0], 1), cases[1] || cases[0]);
  assert.equal(BT.stepCase(DATA, v.region, v.year, cases[0], -1), cases[cases.length - 1]);
  assert.equal(BT.stepCase(DATA, v.region, v.year, null, 1), cases[0]);
  assert.equal(BT.stepCase(DATA, v.region, 2019, null, 1), null);
});

test("an insufficient-data day says so", () => {
  assert.match(BT.why({ level: "Insufficient data" }), /Not enough weather data/);
});

test("zone lists agree: sites, health rates, live and replay data cover the same 10 zones", () => {
  const AL = require("../alerts.js"), HS = require("../health.js");
  const replay = JSON.parse(fs.readFileSync(path.join(__dirname, "..", "data", "replay.json"), "utf8"));
  const live = JSON.parse(fs.readFileSync(path.join(__dirname, "..", "data", "live.json"), "utf8"));
  const keys = Object.keys(replay).sort();
  assert.equal(keys.length, 10);
  assert.deepEqual(Object.keys(AL.SITES).sort(), keys);
  assert.deepEqual(Object.keys(live.zones).sort(), keys);
  for (const k of keys) assert.ok(HS.simulate(k).counts.length > 0);
});

test("a no-alert day between the 50th and 60th percentile names the missing jump, not the percentile", () => {
  const t = BT.why({ level: "No alert", hi_f: 95, pctl: 55, jump_f: 1.2 });
  assert.match(t, /jump of only \+1\.2/);
  assert.match(t, /needs 3 °F/);
});

test("the fixed-trigger column says it counts days alerted, not case days caught", () => {
  const out = BT.html(DATA, BT.defaultView(DATA), s => String(s), d => d);
  assert.match(out, /Days alerted by the fixed 80 °F trigger/);
});
