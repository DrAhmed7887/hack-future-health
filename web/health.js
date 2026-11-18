"use strict";
// v4 health signal: simulated daily emergency-department heat-illness visits per zone, summer 2025, with an EARS C2 flag.
// PROPOSAL E1-E6 (docs/evidence_v3_signals.md), pending Dr Zayed's sign-off. Simulated, seeded; see docs/data_card_simulated.md.
// The flag is a statistical prompt to review, never a confirmed cluster, and it never changes the heat level.
(function (root) {
  const BASE_DAYS = 7, GUARD = 2, SD_FLOOR = 1.0, THRESHOLD = 3, MIN_COUNT = 3, SUPPRESS_BELOW = 5;   // E1-E5
  const START = "2025-04-21", END = "2025-09-30";   // 10 days of run-in before the May-September replay
  const RATE = { mussafah: 1.5, adcity: 1.2, ruwais: 0.6, alain: 1.0, taweelah: 0.9, wathbah: 0.7, sweihan: 0.4, madinatzayed: 0.5, ghayathi: 0.3, liwa: 0.4 };   // illustrative visits a day, not from any source
  const EPISODE_EXTRA = [5, 6, 4];                                        // illustrative extra visits on 3 consecutive days

  function rng(key) {
    let h = 2166136261;
    for (const c of key) { h ^= c.charCodeAt(0); h = Math.imul(h, 16777619); }
    let a = h >>> 0;
    return () => {
      a = (a + 0x6D2B79F5) >>> 0;
      let t = Math.imul(a ^ (a >>> 15), 1 | a);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }
  function poisson(lambda, r) {   // Knuth: fine for small rates
    const L = Math.exp(-lambda);
    let k = 0, p = 1;
    do { k += 1; p *= r(); } while (p > L);
    return k - 1;
  }
  function dayList(a, b) {
    const out = [];
    for (let t = Date.parse(a + "T00:00:00Z"); t <= Date.parse(b + "T00:00:00Z"); t += 864e5) out.push(new Date(t).toISOString().slice(0, 10));
    return out;
  }

  // EARS C2 at index t: baseline t-9..t-3 (7 days), guard band t-2..t-1, S = (y - mean) / max(sd, 1), flag if S > 3 and y >= 3.
  function c2(series, t) {
    const lo = t - GUARD - BASE_DAYS, hi = t - GUARD;
    const b = lo >= 0 ? series.slice(lo, hi).filter(Number.isFinite) : [];
    if (b.length < BASE_DAYS || !Number.isFinite(series[t])) return { flag: false, reason: "baseline", mu: NaN, s: NaN, S: NaN };
    const mu = b.reduce((x, y) => x + y, 0) / b.length;
    const s = Math.sqrt(b.reduce((x, y) => x + (y - mu) ** 2, 0) / (b.length - 1));
    const S = (series[t] - mu) / Math.max(s, SD_FLOOR);
    return { flag: S > THRESHOLD && series[t] >= MIN_COUNT, reason: null, mu, s, S };
  }

  const cache = {};
  function simulate(zone) {
    if (cache[zone]) return cache[zone];
    const dates = dayList(START, END), r = rng(zone + "|health"), lam = RATE[zone] ?? 1;
    const counts = dates.map(() => poisson(lam, r));
    // three episodes, one in each ~5-week window from 1 Jun, each 3 days long
    const first = dates.indexOf("2025-06-01"), episodes = [];
    for (let w = 0; w < 3; w += 1) {
      const start = first + w * 37 + Math.floor(r() * 30);
      EPISODE_EXTRA.forEach((x, i) => { counts[start + i] += x; });
      episodes.push({ start: dates[start], days: EPISODE_EXTRA.length });
    }
    cache[zone] = { zone, dates, counts, episodes };
    return cache[zone];
  }

  function healthDay(zone, date) {
    const sim = simulate(zone), t = sim.dates.indexOf(date);
    if (t < 0) return null;
    const r = c2(sim.counts, t), visits = sim.counts[t];
    return { date, visits, suppressed: visits < SUPPRESS_BELOW, expected: Math.round(r.mu * 10) / 10, S: Math.round(r.S * 10) / 10, flag: r.flag, baselineOk: r.reason === null };
  }

  // Detection of the injected episodes (flag on day 1 or 2) and flags on any other day, May-September.
  function evaluate(zones) {
    const zs = zones || Object.keys(RATE);
    let episodes = 0, detected = 0, falseFlags = 0, zoneDays = 0, lagSum = 0;
    for (const z of zs) {
      const sim = simulate(z);
      const inEp = new Set(), early = [];
      for (const e of sim.episodes) {
        const s = sim.dates.indexOf(e.start);
        for (let i = 0; i < e.days + 2; i += 1) inEp.add(s + i);   // episode days and the 2 days after (baseline carry-over)
        early.push([s, s + 1]);
      }
      for (let t = sim.dates.indexOf("2025-05-01"); t < sim.dates.length; t += 1) {
        zoneDays += 1;
        if (c2(sim.counts, t).flag && !inEp.has(t)) falseFlags += 1;
      }
      for (const [a, b] of early) {
        episodes += 1;
        const hit = [a, b].find(t => c2(sim.counts, t).flag);
        if (hit !== undefined) { detected += 1; lagSum += hit - a; }
      }
    }
    return { episodes, detected, falseFlags, zoneDays, meanLagDays: detected ? Math.round(lagSum / detected * 10) / 10 : null };
  }

  const api = { BASE_DAYS, GUARD, SD_FLOOR, THRESHOLD, MIN_COUNT, SUPPRESS_BELOW, c2, simulate, healthDay, evaluate };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else root.HealthSignal = api;
})(typeof window !== "undefined" ? window : globalThis);
