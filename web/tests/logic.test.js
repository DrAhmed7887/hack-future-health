// Written before web/logic.js (Phase 3). Run: node --test web/tests/
const test = require("node:test");
const assert = require("node:assert");
const L = require("../logic.js");

test("unanswered or unsure counts as yes, only 'no' is no", () => {
  assert.equal(L.answeredYes(null), true);
  assert.equal(L.answeredYes("unsure"), true);
  assert.equal(L.answeredYes("yes"), true);
  assert.equal(L.answeredYes("no"), false);
});

test("new or returning workers raise the tier one level, in season only", () => {
  assert.deepEqual(L.effectiveTier("No escalation", { newWorkers: "yes" }), { tier: "Elevated", raised: true });
  assert.deepEqual(L.effectiveTier("Elevated", { newWorkers: null }), { tier: "High", raised: true });
  assert.deepEqual(L.effectiveTier("High", { newWorkers: "yes" }), { tier: "High", raised: false });
  assert.deepEqual(L.effectiveTier("Elevated", { newWorkers: "no" }), { tier: "Elevated", raised: false });
  assert.deepEqual(L.effectiveTier("Outside tested season", { newWorkers: "yes" }), { tier: "Outside tested season", raised: false });
});

test("insufficient data never lowers protection", () => {
  assert.equal(L.effectiveTier("Insufficient data", { newWorkers: "no" }).tier, "Elevated");
});

test("High with heavy work asks for OSH assessment and re-timing at the peak hour", () => {
  const s = L.planSteps("High", { newWorkers: "no", heavy: "yes" }, true, 14).map(x => x.text).join(" | ");
  assert.match(s, /OSH practitioner/);
  assert.match(s, /14:00/);
  assert.doesNotMatch(s, /20%/);
});

test("new workers always get the acclimatisation schedule, even outside the season", () => {
  const s = L.planSteps("Outside tested season", { newWorkers: "yes", heavy: "no" }, false, 14).map(x => x.text).join(" | ");
  assert.match(s, /20%/);
});

test("no step list is ever empty", () => {
  assert.ok(L.planSteps("No escalation", { newWorkers: "no", heavy: "no" }, true, 14).length >= 1);
});

test("a forecast older than 36 hours is stale", () => {
  const now = new Date("2026-11-09T12:00:00Z");
  assert.equal(L.isStale("2026-11-08 06:00", now), false);
  assert.equal(L.isStale("2026-11-07 23:00", now), true);
  assert.equal(L.isStale("not a date", now), true);
});

test("legal layer: midday break only 15 Jun to 15 Sep; 35 C trigger uses air temperature", () => {
  const jul = L.legalItems({ date: "2025-07-01", max_temp_c: 44 }, false).map(i => i.t).join(" ");
  const jun = L.legalItems({ date: "2025-06-14", max_temp_c: 34 }, true).map(i => i.t).join(" ");
  assert.match(jul, /12:30 to 15:00/);
  assert.match(jul, /reaches 44/);
  assert.match(jun, /not in force/);
  assert.match(jun, /peaked at 34/);
});

// Code review 7 Nov (HIGH 1-3, MEDIUM 10-11): tests written before the fix.
const NOW = new Date("2026-07-10T08:00:00Z");   // 12:00 in Dubai, 10 Jul 2026
const FRESH = "2026-07-09 14:00";

test("resolveDay: tomorrow's in-season forecast keeps its tier and says Tomorrow", () => {
  const r = L.resolveDay({ date: "2026-07-11", tier: "High" }, FRESH, NOW);
  assert.equal(r.tier, "High"); assert.equal(r.when, "Tomorrow");
});

test("resolveDay: a forecast for today says Today", () => {
  assert.equal(L.resolveDay({ date: "2026-07-10", tier: "Elevated" }, FRESH, NOW).when, "Today");
});

test("resolveDay: a forecast dated before today is stale even if recently generated", () => {
  const r = L.resolveDay({ date: "2026-07-09", tier: "No escalation" }, FRESH, NOW);
  assert.equal(r.tier, "Insufficient data"); assert.equal(r.stale, true);
});

test("resolveDay: old generation time is stale in season", () => {
  assert.equal(L.resolveDay({ date: "2026-07-11", tier: "No escalation" }, "2026-07-08 10:00", NOW).tier, "Insufficient data");
});

test("resolveDay: outside May-September the season label wins, even when stale or missing", () => {
  const dec = new Date("2026-12-10T08:00:00Z");
  assert.equal(L.resolveDay({ date: "2026-12-09", tier: "Insufficient data" }, "2026-12-01 10:00", dec).tier, "Outside tested season");
  assert.equal(L.resolveDay(null, "2026-12-09 14:00", dec).tier, "Outside tested season");
});

test("resolveDay: missing forecast in season is Insufficient data", () => {
  assert.equal(L.resolveDay(null, FRESH, NOW).tier, "Insufficient data");
});

test("legal layer never reassures when the temperature is unknown", () => {
  const s = L.legalItems({ date: "2026-07-11" }, false).map(i => i.t).join(" ");
  assert.doesNotMatch(s, /undefined|below the 35/);
  assert.match(s, /assume the 35/i);
});
