// v4 simulated health signal + EARS C2 (proposal E1-E6, docs/evidence_v3_signals.md). Written before web/health.js.
const test = require("node:test");
const assert = require("node:assert");
const HS = require("../health.js");

const base = [1, 2, 1, 0, 1, 2, 1];   // t-9 .. t-3
const series = (y, guard = [0, 0]) => [...base, ...guard, y];   // index 9 is t

test("C2 uses the 7 days t-9..t-3, an SD floor of 1, and flags above 3 SD", () => {
  const r = HS.c2(series(5), 9);
  assert.equal(Math.round(r.mu * 1000) / 1000, 1.143);
  assert.ok(r.s < 1);                       // sample SD 0.69, floored to 1
  assert.equal(Math.round(r.S * 100) / 100, 3.86);
  assert.equal(r.flag, true);
  assert.equal(HS.c2(series(4), 9).flag, false);   // S = 2.86
});

test("C2 ignores the 2-day guard band", () => {
  assert.deepEqual(HS.c2(series(5, [40, 40]), 9), HS.c2(series(5), 9));
});

test("C2 never flags without 7 baseline days, or below 3 visits", () => {
  const r = HS.c2([1, 1, 5], 2);
  assert.equal(r.flag, false); assert.equal(r.reason, "baseline");
  const zeros = [0, 0, 0, 0, 0, 0, 0, 0, 0];
  assert.equal(HS.c2([...zeros, 3], 9).flag, false);   // S = 3, not above 3
  assert.equal(HS.c2([...zeros, 4], 9).flag, true);
  assert.equal(HS.c2([...base.map(() => 0), 0, 0, 2], 9).flag, false);   // under the 3-visit minimum
});

test("simulated visits are seeded, whole and non-negative, with 3 injected episodes per zone", () => {
  const a = HS.simulate("mussafah"), b = HS.simulate("mussafah");
  assert.deepEqual(a, b);
  assert.ok(a.counts.every(n => Number.isInteger(n) && n >= 0));
  assert.equal(a.episodes.length, 3);
  assert.equal(a.dates[0], "2025-04-21"); assert.equal(a.dates[a.dates.length - 1], "2025-09-30");
});

test("healthDay suppresses counts under 5 and reports the expected level", () => {
  const sim = HS.simulate("mussafah");
  for (const d of sim.dates.slice(9)) {
    const h = HS.healthDay("mussafah", d);
    assert.equal(h.suppressed, h.visits < 5);
    assert.ok(Number.isFinite(h.expected));
  }
  assert.equal(HS.healthDay("mussafah", "2026-11-18"), null);   // no simulated series outside summer 2025
});

test("on its own simulation, C2 catches most injected episodes within 2 days", () => {
  const ev = HS.evaluate();
  assert.equal(ev.episodes, 12);
  assert.ok(ev.detected >= 9, `detected ${ev.detected}`);
  assert.ok(ev.falseFlags >= 0 && Number.isInteger(ev.falseFlags));
  assert.ok(ev.zoneDays > 500);
});
