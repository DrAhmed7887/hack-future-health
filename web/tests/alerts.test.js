// v3 alerts (review feedback 17 Nov 2026). Written before web/alerts.js. Run: node --test web/tests/
const test = require("node:test");
const assert = require("node:assert");
const A = require("../alerts.js");

const HIGH = { date: "2025-08-01", heat_index_f: 108.2, percentile: 72, anomaly_f: 1.0, max_temp_c: 45.1, peak_hour: 14, tier: "High" };
const ELEV = { date: "2025-06-10", heat_index_f: 101.0, percentile: 55, anomaly_f: 3.6, max_temp_c: 42.0, peak_hour: 13, tier: "Elevated" };
const NONE = { date: "2025-06-11", heat_index_f: 99.0, percentile: 40, anomaly_f: -1.0, max_temp_c: 41.0, peak_hour: 13, tier: "No escalation" };
const OFF = { date: "2026-11-18", heat_index_f: 84.9, percentile: null, anomaly_f: -6.8, max_temp_c: 30.5, peak_hour: 14, tier: "Outside tested season" };
const MISSING = { date: "2026-07-11", tier: "Insufficient data", stale: true };

const heat = alerts => alerts.find(a => a.type === "heat");

test("simulated signals are seeded: same zone and day give the same numbers, within the site count", () => {
  const a = A.simSignals("mussafah", "2025-08-01"), b = A.simSignals("mussafah", "2025-08-01");
  assert.deepEqual(a, b);
  for (const k of ["acked", "cooling", "newWorkerSites", "heavySites"]) assert.ok(a[k] >= 0 && a[k] <= a.sites, k);
  assert.notDeepEqual(A.simSignals("mussafah", "2025-08-02"), a);
});

test("a High day gives a heat alert whose level is the tested tier, triggered by the rank", () => {
  const h = heat(A.buildAlerts("mussafah", "Mussafah", HIGH));
  assert.equal(h.level, "High");
  assert.equal(h.trigger, "rank");
  const rank = h.drivers.find(d => d.id === "rank");
  assert.equal(rank.value, 72); assert.equal(rank.threshold, 60); assert.equal(rank.met, true); assert.equal(rank.basis, "tested");
});

test("an Elevated day is explained by rank and the 14-day jump together", () => {
  const h = heat(A.buildAlerts("mussafah", "Mussafah", ELEV));
  assert.equal(h.level, "Elevated");
  assert.equal(h.trigger, "rank+jump");
  const jump = h.drivers.find(d => d.id === "jump");
  assert.equal(jump.met, true);
  assert.equal(h.drivers.find(d => d.id === "rank").threshold, 50);
});

test("no heat alert on a No escalation day or outside the tested season", () => {
  assert.equal(heat(A.buildAlerts("mussafah", "Mussafah", NONE)), undefined);
  assert.equal(heat(A.buildAlerts("mussafah", "Mussafah", OFF)), undefined);
});

test("missing data raises an Elevated heat alert that says the data is missing", () => {
  const h = heat(A.buildAlerts("mussafah", "Mussafah", MISSING));
  assert.equal(h.level, "Elevated");
  assert.ok(h.drivers.some(d => d.id === "data" && d.met));
});

test("every alert names an owner, a due time, an escalation chain and when it closes", () => {
  for (const day of [HIGH, ELEV, MISSING]) {
    for (const a of A.buildAlerts("mussafah", "Mussafah", day, { sim: { sites: 12, acked: 5, cooling: 3, newWorkerSites: 2, heavySites: 6, notices3d: 1 } })) {
      assert.ok(a.owner.role && a.owner.due, a.id);
      assert.ok(a.chain.length >= 1, a.id);
      assert.ok(a.closeWhen, a.id);
      assert.ok(a.leadHours > 0, a.id);
    }
  }
});

test("every action is linked to a driver of the same alert and has an owner and a source", () => {
  const all = A.buildAlerts("mussafah", "Mussafah", HIGH, { sim: { sites: 12, acked: 5, cooling: 3, newWorkerSites: 2, heavySites: 6, notices3d: 1 } });
  assert.ok(all.length >= 3);
  for (const a of all) {
    assert.ok(a.actions.length >= 1, a.id);
    const ids = new Set(a.drivers.map(d => d.id));
    for (const x of a.actions) {
      assert.ok(ids.has(x.because), `${a.id}: ${x.text} -> ${x.because}`);
      assert.ok(x.owner && x.source && x.due, x.text);
    }
  }
});

test("new or returning workers add the acclimatisation actions; none when no site has them", () => {
  const withNew = heat(A.buildAlerts("mussafah", "Mussafah", HIGH, { sim: { sites: 12, acked: 12, cooling: 12, newWorkerSites: 2, heavySites: 0, notices3d: 0 } }));
  const without = heat(A.buildAlerts("mussafah", "Mussafah", HIGH, { sim: { sites: 12, acked: 12, cooling: 12, newWorkerSites: 0, heavySites: 0, notices3d: 0 } }));
  assert.ok(withNew.actions.some(x => /20%/.test(x.text)));
  assert.ok(!without.actions.some(x => /20%/.test(x.text)));
});

test("preparedness gap: only on hot days, only when cooling or acknowledgements are short", () => {
  const short = { sites: 12, acked: 6, cooling: 4, newWorkerSites: 0, heavySites: 3, notices3d: 0 };
  const ready = { sites: 12, acked: 12, cooling: 12, newWorkerSites: 0, heavySites: 3, notices3d: 0 };
  assert.ok(A.buildAlerts("mussafah", "Mussafah", HIGH, { sim: short }).some(a => a.type === "prep"));
  assert.ok(!A.buildAlerts("mussafah", "Mussafah", HIGH, { sim: ready }).some(a => a.type === "prep"));
  assert.ok(!A.buildAlerts("mussafah", "Mussafah", NONE, { sim: short }).some(a => a.type === "prep"));
});

test("small cells: a zone with fewer than 5 sites shows no site counts and no preparedness alert", () => {
  const sim = { sites: 4, acked: 1, cooling: 0, newWorkerSites: 1, heavySites: 2, notices3d: 1 };
  const all = A.buildAlerts("ruwais", "Ruwais", HIGH, { sim });
  assert.ok(!all.some(a => a.type === "prep"));
  const text = JSON.stringify(all);
  assert.doesNotMatch(text, /\b\d+ of 4\b/);
});

test("incident notices raise a check, never the heat level", () => {
  const sim = { sites: 12, acked: 12, cooling: 12, newWorkerSites: 0, heavySites: 0, notices3d: 2 };
  const all = A.buildAlerts("mussafah", "Mussafah", ELEV, { sim });
  assert.equal(heat(all).level, "Elevated");
  const n = all.find(a => a.type === "notice");
  assert.ok(n);
  assert.match(n.summary, /does not change/i);
  assert.ok(A.buildAlerts("mussafah", "Mussafah", NONE, { sim }).some(a => a.type === "notice"));
});

test("escalation: an open heat alert passes to the OSH practitioner at 06:30 and ADPHC at 09:00", () => {
  const h = heat(A.buildAlerts("mussafah", "Mussafah", HIGH));
  assert.equal(A.holder(h, "open", A.CLOCK.evening).escalated, false);
  assert.equal(A.holder(h, "open", A.CLOCK.evening).role, h.owner.role);
  assert.equal(A.holder(h, "open", A.CLOCK.shift).escalated, true);
  assert.match(A.holder(h, "open", A.CLOCK.shift).role, /OSH practitioner/);
  assert.match(A.holder(h, "open", A.CLOCK.mid).role, /ADPHC/);
});

test("escalation stops once the owner acknowledges", () => {
  const h = heat(A.buildAlerts("mussafah", "Mussafah", HIGH));
  for (const s of ["acknowledged", "done", "closed"]) {
    const r = A.holder(h, s, A.CLOCK.mid);
    assert.equal(r.escalated, false, s);
    assert.equal(r.role, h.owner.role, s);
  }
});

test("alerts sort High before Elevated before checks", () => {
  const sim = { sites: 12, acked: 5, cooling: 3, newWorkerSites: 0, heavySites: 3, notices3d: 1 };
  const list = A.sortAlerts([...A.buildAlerts("adcity", "Abu Dhabi city", ELEV, { sim }), ...A.buildAlerts("mussafah", "Mussafah", HIGH, { sim })]);
  assert.equal(list[0].level, "High");
  assert.equal(list[list.length - 1].type, "notice");
});

// Codex review 17 Nov (P1): simulated counts are labelled where they appear, not only in a page note.
test("notice and preparedness alerts label their simulated counts", () => {
  const sim = { sites: 12, acked: 5, cooling: 3, newWorkerSites: 0, heavySites: 3, notices3d: 1 };
  const all = A.buildAlerts("mussafah", "Mussafah", HIGH, { sim });
  assert.match(all.find(a => a.type === "notice").title, /simulated/);
  assert.match(all.find(a => a.type === "prep").summary, /simulated/);
});

// v4 (second review, 18 Nov): newly-High onset, health signal and dust. Written before the code.
const FLAG = { date: "2025-08-01", visits: 7, suppressed: false, expected: 1.4, S: 5.2, flag: true, baselineOk: true };
const FLAG_SMALL = { ...FLAG, visits: 4, suppressed: true, S: 3.4 };
const READY = { sites: 12, acked: 12, cooling: 12, newWorkerSites: 0, heavySites: 0, notices3d: 0 };

test("a High day after a non-High day is marked as new; repeat High days are not", () => {
  assert.equal(heat(A.buildAlerts("mussafah", "Mussafah", HIGH, { sim: READY, prevTier: "No escalation" })).onset, true);
  assert.match(heat(A.buildAlerts("mussafah", "Mussafah", HIGH, { sim: READY, prevTier: "No escalation" })).title, /new/i);
  assert.equal(heat(A.buildAlerts("mussafah", "Mussafah", HIGH, { sim: READY, prevTier: "High" })).onset, false);
  assert.equal(heat(A.buildAlerts("mussafah", "Mussafah", HIGH, { sim: READY })).onset, false);
});

test("a health flag raises its own alert, worded as a flag on simulated data, and never changes the heat level", () => {
  const all = A.buildAlerts("mussafah", "Mussafah", ELEV, { sim: READY, health: FLAG });
  const h = all.find(a => a.type === "health");
  assert.ok(h);
  assert.equal(h.level, "Signal");
  assert.match(h.summary, /simulated/i);
  assert.match(h.summary, /not a confirmed cluster/i);
  assert.doesNotMatch(JSON.stringify(h), /outbreak/i);
  assert.equal(heat(all).level, "Elevated");
  assert.ok(heat(all).drivers.some(d => d.group === "Health"));
  assert.ok(A.buildAlerts("mussafah", "Mussafah", NONE, { sim: READY, health: FLAG }).some(a => a.type === "health"));
  assert.ok(!A.buildAlerts("mussafah", "Mussafah", ELEV, { sim: READY, health: { ...FLAG, flag: false } }).some(a => a.type === "health"));
});

test("health counts under 5 are never shown", () => {
  const h = A.buildAlerts("mussafah", "Mussafah", NONE, { sim: READY, health: FLAG_SMALL }).find(a => a.type === "health");
  assert.doesNotMatch(JSON.stringify(h), /\b4 visits\b|"value":4\b/);
  assert.match(h.summary, /fewer than 5/i);
});

test("dust above the UAE standard raises a dust alert with sourced actions and never says stop work", () => {
  for (const [lv, pm] of [["Elevated", 180], ["High", 300]]) {
    const d = A.buildAlerts("alain", "Al Ain", NONE, { sim: READY, dust: { pm10: pm, level: lv } }).find(a => a.type === "dust");
    assert.ok(d, lv);
    assert.equal(d.level, lv);
    assert.match(d.title, /dust/i);
    for (const x of d.actions) { assert.ok(x.source && x.owner && x.due, x.text); assert.doesNotMatch(x.text, /stop work/i); }
  }
  assert.ok(!A.buildAlerts("alain", "Al Ain", NONE, { sim: READY, dust: { pm10: 90, level: "None" } }).some(a => a.type === "dust"));
  assert.ok(!A.buildAlerts("alain", "Al Ain", NONE, { sim: READY, dust: { pm10: null, level: "Insufficient data" } }).some(a => a.type === "dust"));
});

test("new alert types also carry owner, chain, closing condition and linked actions", () => {
  const all = A.buildAlerts("mussafah", "Mussafah", HIGH, { sim: READY, prevTier: "Elevated", health: FLAG, dust: { pm10: 300, level: "High" } });
  for (const a of all.filter(x => x.type === "health" || x.type === "dust")) {
    assert.ok(a.owner.role && a.owner.due && a.chain.length && a.closeWhen, a.id);
    const ids = new Set(a.drivers.map(d => d.id));
    for (const x of a.actions) assert.ok(ids.has(x.because), `${a.id}: ${x.because}`);
  }
});

// Code review 18 Nov (HIGH): a hidden count must not be recoverable from expected + score.
test("a suppressed health count shows neither the expected level nor the C2 score", () => {
  const h = A.buildAlerts("mussafah", "Mussafah", NONE, { sim: READY, health: { ...FLAG_SMALL, expected: 0.9, S: 3.1 } }).find(a => a.type === "health");
  const text = JSON.stringify(h);
  assert.doesNotMatch(text, /0\.9|3\.1/);
  assert.equal(h.drivers.find(d => d.id === "visits").value, null);
});

test("D1-D6 and E1-E6 are signed (docs/signoff.md S8), so no driver carries the pending tag", () => {
  const AL = require("../alerts.js");
  assert.equal(AL.SIGNED, true);
});
