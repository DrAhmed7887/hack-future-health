"use strict";
// v3 alerts: one object per zone, day and kind, with the drivers behind it, an owner, an escalation chain and the actions.
// Pure and shared by the browser (window.AlertLogic) and the node tests (module.exports).
// The heat level is always the tested R4 tier from the data. Workplace and service signals never change it.
(function (root) {
  const H = typeof module !== "undefined" && module.exports ? require("./logic.js") : root.HeatLogic;

  // Simulated for the demo (labelled in the UI and in docs/data_card_simulated.md).
  const SITES = { mussafah: 12, adcity: 9, ruwais: 4, alain: 7 };
  const SUPPRESS_BELOW = 5;
  const PREP = { cooling: 0.75, acked: 0.8 };   // demo thresholds for a preparedness gap, our choice
  const JUMP_F = 3;                              // frozen R4 parameter a (results/frozen_params_r4.json)
  const P_HIGH = 60, P_LOW = 50, GATE_F = 80;    // frozen R4 parameters
  // Minutes from midnight on the alert day; the forecast is issued at 18:00 the evening before.
  const CLOCK = { evening: -360, shift: 390, mid: 540, end: 1080 };
  const ISSUE_TO_SHIFT_HOURS = 12;               // 18:00 to a 06:00 shift
  const RANK = { High: 0, Signal: 1, Elevated: 2, Gap: 3, Check: 4 };
  const TYPE_ORDER = { heat: 0, health: 1, dust: 2, prep: 3, notice: 4 };
  // Dust (D1-D6) and health (E1-E6) rules are proposals until Dr Zayed signs them; their drivers say so while this is false.
  const SIGNED = false;
  const DUST_ELEVATED = 150, DUST_HIGH = 250;   // same as heatwarn/dust.py
  function dustLevel(pm) {
    if (pm == null || !Number.isFinite(pm)) return "Insufficient data";
    return pm > DUST_HIGH ? "High" : pm > DUST_ELEVATED ? "Elevated" : "None";
  }

  // Seeded generator: FNV-1a hash of the key, then mulberry32.
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

  function simSignals(zone, date) {
    const sites = SITES[zone] || 0, r = rng(zone + "|" + date);
    return {
      sites,
      acked: Math.round(sites * (0.6 + 0.4 * r())),
      cooling: Math.round(sites * (0.4 + 0.6 * r())),
      newWorkerSites: Math.floor(sites * 0.35 * r()),
      heavySites: Math.round(sites * (0.3 + 0.5 * r())),
      notices3d: r() < 0.07 ? 1 : 0,
    };
  }

  const toC = f => Math.round((f - 32) * 5 / 9 * 10) / 10;
  const dC = f => Math.round(f * 5 / 9 * 10) / 10;
  const small = sim => sim.sites < SUPPRESS_BELOW;

  function heatDrivers(day, sim) {
    const d = [];
    if (day.tier === "Insufficient data") {
      d.push({ id: "data", group: "Environment", basis: "rule", role: "trigger", met: true,
        label: "The forecast is missing or older than 36 hours, so tomorrow is treated as Elevated" });
    } else {
      const p = day.percentile, thr = day.tier === "High" ? P_HIGH : P_LOW;
      d.push({ id: "rank", group: "Environment", basis: "tested", role: "trigger", value: p, threshold: thr, min: 0, max: 100, unit: "%", met: p >= thr,
        label: `Hotter than ${p}% of days here at this time of year (2015 to 2021); the alert starts at ${thr}%` });
      const jump = day.anomaly_f;
      if (jump != null) d.push({ id: "jump", group: "Environment", basis: "tested", role: day.tier === "Elevated" ? "trigger" : "context",
        value: dC(jump), threshold: dC(JUMP_F), min: -6, max: 8, unit: "°C", met: jump >= JUMP_F,
        label: `${jump >= 0 ? "+" : "−"}${Math.abs(dC(jump))} °C against the previous 14 days${day.tier === "Elevated" ? `; Elevated needs +${dC(JUMP_F)} °C` : ""}` });
      d.push({ id: "gate", group: "Environment", basis: "tested", role: "trigger", value: day.heat_index_c ?? toC(day.heat_index_f), threshold: toC(GATE_F), min: 20, max: 50, unit: "°C",
        met: day.heat_index_f >= GATE_F, label: `Peak heat index ${day.heat_index_c ?? toC(day.heat_index_f)} °C, above the ${toC(GATE_F)} °C floor` });
    }
    if (small(sim)) {
      d.push({ id: "newWorkers", group: "Workplace", basis: "guideline", simulated: true, role: "context", met: true,
        label: `Fewer than ${SUPPRESS_BELOW} sites in this zone, so site counts are hidden. Any site with new or returning workers plans one level higher.` });
      d.push({ id: "heavy", group: "Workplace", basis: "guideline", simulated: true, role: "context", met: true,
        label: "Site counts hidden: heavy-work steps apply to any site that plans heavy outdoor work." });
    } else {
      if (sim.newWorkerSites > 0) d.push({ id: "newWorkers", group: "Workplace", basis: "guideline", simulated: true, role: "context", value: sim.newWorkerSites, threshold: 1, min: 0, max: sim.sites, met: true,
        label: `${sim.newWorkerSites} of ${sim.sites} sites have new or returning workers: those site plans go one level higher (the zone level does not change)` });
      if (sim.heavySites > 0) d.push({ id: "heavy", group: "Workplace", basis: "guideline", simulated: true, role: "context", value: sim.heavySites, threshold: 1, min: 0, max: sim.sites, met: true,
        label: `${sim.heavySites} of ${sim.sites} sites plan heavy outdoor work` });
    }
    return d;
  }

  const DEFAULT_DUE = { rank: "Before the shift (06:00)", data: "Before the shift (06:00)", heavy: "When setting the shift plan, the evening before", newWorkers: "Day 1 of each new or returning worker" };

  function heatActions(level, day, sim, driverIds) {
    const hidden = small(sim);
    const crew = { newWorkers: hidden || sim.newWorkerSites > 0 ? "yes" : "no", heavy: hidden || sim.heavySites > 0 ? "yes" : "no" };
    return H.planSteps(level, crew, true, day.peak_hour).filter(s => s.because).map(s => {
      const [role, rest] = s.owner.split(" · ");
      const isSource = /ADPHC|NIOSH|ACSM/.test(rest || "");
      const because = driverIds.has(s.because) ? s.because : (driverIds.has("rank") ? "rank" : "data");
      const who = s.because === "newWorkers" ? `${role} at sites with new or returning workers` : role;
      return { text: s.text, owner: who, due: isSource ? DEFAULT_DUE[s.because] : rest, because,
        source: isSource ? rest : "Plan step based on guidelines; not tested on outcomes" };
    });
  }

  function heatAlert(zone, zoneName, day, sim, opts) {
    const level = day.tier === "Insufficient data" ? "Elevated" : day.tier;
    const health = opts.health && opts.health.flag ? opts.health : null;
    const drivers = [...heatDrivers(day, sim), ...(health ? [{ id: "visits", group: "Health", basis: "simulated", simulated: true, role: "context", met: true,
      label: "Heat-illness visits in this zone are above their baseline today (simulated; see the health alert)" }] : [])];
    const onset = level === "High" && opts.prevTier != null && opts.prevTier !== "High";
    const ids = new Set(drivers.map(x => x.id));
    const trigger = day.tier === "Insufficient data" ? "data" : day.tier === "High" ? "rank" : "rank+jump";
    const summary = trigger === "data" ? "No usable forecast. Plan as for an Elevated day until it updates."
      : trigger === "rank" ? `Hotter than ${day.percentile}% of days here at this time of year.`
      : `Warmer than usual here (${day.percentile}%)${day.anomaly_f != null ? " and rising fast against the last 14 days" : ""}.`;
    return {
      id: `${zone}|${day.date}|heat`, type: "heat", level, zone, zoneName, date: day.date, trigger, onset, firstOfSeason: onset && !!opts.firstHigh,
      title: trigger === "data" ? "Heat: no forecast (planned as Elevated)" : `Heat: ${level}${onset ? (opts.firstHigh ? " (first of the season)" : " (new today)") : ""}`,
      summary: onset ? `Newly High: the day before was ${opts.prevTier === "No escalation" ? "not an alert day" : opts.prevTier}. ${summary}` : summary,
      leadHours: ISSUE_TO_SHIFT_HOURS, drivers,
      owner: { role: "Site supervisors in the zone", due: "Acknowledge the plan by 06:30" },
      chain: [{ role: "OSH practitioner", at: CLOCK.shift }, { role: "ADPHC OSH zone officer", at: CLOCK.mid }],
      closeWhen: "Every site's plan is acknowledged and its cooling station confirmed, or the shift ends.",
      actions: heatActions(level, day, sim, ids),
    };
  }

  function prepAlert(zone, zoneName, day, sim, level) {
    const coolShort = sim.cooling / sim.sites < PREP.cooling, ackShort = sim.acked / sim.sites < PREP.acked;
    if (!coolShort && !ackShort) return null;
    const drivers = [
      { id: "heat", group: "Environment", basis: "tested", role: "trigger", met: true, label: `Heat alert for this zone: ${level}` },
      { id: "cooling", group: "Service", basis: "rule", simulated: true, role: "trigger", value: sim.cooling, threshold: Math.ceil(sim.sites * PREP.cooling), min: 0, max: sim.sites, met: coolShort,
        label: `${sim.cooling} of ${sim.sites} sites have a cooling station ready; the gap starts below ${Math.round(PREP.cooling * 100)}%` },
      { id: "acked", group: "Service", basis: "rule", simulated: true, role: "trigger", value: sim.acked, threshold: Math.ceil(sim.sites * PREP.acked), min: 0, max: sim.sites, met: ackShort,
        label: `${sim.acked} of ${sim.sites} site plans acknowledged; the gap starts below ${Math.round(PREP.acked * 100)}%` },
    ];
    const actions = [];
    if (coolShort) actions.push({ text: "Call the sites without a ready cooling station and confirm one is set up in the shade before work starts.", owner: "ADPHC OSH zone officer", due: "By 07:00", because: "cooling",
      source: "Cooling station step: ACSM 2023 heat illness consensus; ADPHC Technical Guideline, Safety in the Heat, section 4.5(c)" });
    if (ackShort) actions.push({ text: "Remind the sites whose plan is not acknowledged. At 06:30 their plans go to the OSH practitioner.", owner: "ADPHC OSH zone officer", due: "By 06:30", because: "acked",
      source: "This app's follow-up rule (demo)" });
    actions.push({ text: "Find which sites plan heavy work today and check each one has a cooling station; put any without one first on today's inspection list.", owner: "ADPHC OSH zone officer", due: "By 10:00", because: "heat",
      source: "This app's follow-up rule (demo); not tested on outcomes" });
    return {
      id: `${zone}|${day.date}|prep`, type: "prep", level: "Gap", zone, zoneName, date: day.date, trigger: "heat+service",
      title: "High risk, low preparation", summary: `${level === "Elevated" ? "An" : "A"} ${level} heat day with ${coolShort ? "too few cooling stations ready" : "too few plans acknowledged"} (simulated site data). The heat level stays ${level}.`,
      leadHours: ISSUE_TO_SHIFT_HOURS, drivers,
      owner: { role: "ADPHC OSH zone officer", due: "Contact the sites by 07:00" },
      chain: [{ role: "ADPHC OSH duty manager", at: CLOCK.mid }],
      closeWhen: "Every site has a cooling station ready and an acknowledged plan.",
      actions,
    };
  }

  function noticeAlert(zone, zoneName, day, sim) {
    const n = sim.notices3d;
    return {
      id: `${zone}|${day.date}|notice`, type: "notice", level: "Check", zone, zoneName, date: day.date, trigger: "notices",
      title: `${n} incident notice${n > 1 ? "s" : ""} in the last 3 days (simulated)`,
      summary: "Check that workplace. This does not change the heat level: using notices as a trigger failed its pre-registered test.",
      leadHours: ISSUE_TO_SHIFT_HOURS,
      drivers: [{ id: "notices", group: "Service", basis: "simulated", simulated: true, role: "trigger", value: n, met: true, label: `${n} incident notice${n > 1 ? "s" : ""} from this zone in the last 3 days (simulated)` }],
      owner: { role: "OSH practitioner for that site", due: "Within 24 hours" },
      chain: [{ role: "ADPHC OSH zone officer", at: CLOCK.end }],
      closeWhen: "The OSH practitioner records that the acclimatisation plan and rest breaks were checked.",
      actions: [{ text: "At the site that sent the notice: check the acclimatisation plan and rest breaks.", owner: "OSH practitioner for that site", due: "Within 24 hours", because: "notices",
        source: "README, What did not work: notices are a prompt to check, never a reason to raise the level" }],
    };
  }

  // PROPOSAL E1-E6: EARS C2 flag on simulated heat-illness visits (web/health.js). Counts under 5 are never shown.
  function healthAlert(zone, zoneName, day, hs, heatLevel) {
    // Counts under 5 are hidden; so are the expected level and the score, from which a hidden count could be worked out.
    const hidden = hs.suppressed;
    return {
      id: `${zone}|${day.date}|health`, type: "health", level: "Signal", chip: "Health", zone, zoneName, date: day.date, trigger: "c2",
      title: "Heat-illness visits above baseline (simulated)",
      summary: `${hidden ? "Fewer than 5 simulated heat-illness ED visits, above this zone's earlier 7-day baseline" : `${hs.visits} simulated heat-illness ED visits against about ${hs.expected} expected from the earlier 7-day baseline`} (2-day gap). A statistical flag on simulated data, not a confirmed cluster. Review conditions in the zone.`,
      leadHours: 0,
      drivers: [
        hidden
          ? { id: "visits", group: "Health", basis: "simulated", simulated: true, pending: !SIGNED, role: "trigger", value: null, met: true,
            label: "EARS C2 flag: visits are more than 3 baseline SDs above the expected level (SD floor 1, at least 3 visits). Count and score hidden: fewer than 5 visits" }
          : { id: "visits", group: "Health", basis: "simulated", simulated: true, pending: !SIGNED, role: "trigger", value: hs.S, threshold: 3, min: -2, max: 10, met: true,
            label: `EARS C2 score ${hs.S}: visits are ${hs.S} baseline SDs above the expected ${hs.expected} a day (SD floor 1); the flag starts above 3, with at least 3 visits` },
        { id: "heatctx", group: "Environment", basis: "tested", role: "context", met: heatLevel != null,
          label: heatLevel ? `Heat level in this zone today: ${heatLevel}` : "No heat alert in this zone today" },
      ],
      owner: { role: "ADPHC public health surveillance officer", due: "Review within 24 hours" },
      chain: [{ role: "ADPHC public health lead", at: CLOCK.end }],
      closeWhen: "The review records a likely cause (or none found) and the OSH zone officer has been told.",
      actions: [
        { text: "Review the visits with the reporting emergency departments: same employer, site or shift?", owner: "ADPHC public health surveillance officer", due: "Within 24 hours", because: "visits",
          source: "CDC Early Aberration Reporting System, C2 method (Hutwagner 2003); a statistical flag, not a diagnosis" },
        { text: "Tell the ADPHC OSH zone officer, so sites in the zone re-check cooling stations and rest breaks today.", owner: "ADPHC public health surveillance officer", due: "Same day", because: "visits",
          source: "This app's follow-up rule (demo)" },
        { text: "If the flag is still on tomorrow, raise it with the ADPHC public health lead.", owner: "ADPHC public health surveillance officer", due: "Next day", because: "visits",
          source: "This app's follow-up rule (demo)" },
      ],
    };
  }

  // PROPOSAL D1-D6: forecast daily mean PM10 (CAMS via Open-Meteo) against the UAE 24-hour standard. Not tested on outcomes.
  function dustAlert(zone, zoneName, day, dust) {
    const high = dust.level === "High";
    const drivers = [{ id: "pm10", group: "Environment", basis: "guideline", pending: !SIGNED, role: "trigger", value: dust.pm10, threshold: high ? 250 : 150, min: 0, max: 500, unit: "\u00b5g/m\u00b3", met: true,
      label: `Daily mean PM10 ${dust.pm10}\u00a0\u00b5g/m\u00b3: above ${high ? "250, where the UAE air quality index turns Unhealthy" : "150, the UAE 24-hour standard (Cabinet Decree 12/2006)"}` }];
    const actions = [
      { text: "Check official weather and dust announcements before the shift starts.", owner: "Site supervisor", due: "Before the shift (06:00)", because: "pm10",
        source: "Al Dhafra Municipality advice (Khaleej Times, 13 Mar 2021)" },
      { text: "Ask workers with asthma, COPD, heart disease, rhinitis, sinusitis or conjunctivitis to report symptoms, and reduce their time outdoors.", owner: "Site supervisor", due: "At the shift briefing", because: "pm10",
        source: "ADPHC at-risk groups for dust (The National, 2022)" },
      { text: "Make dust masks available. Public advice also mentions a damp cloth, which is not workplace respiratory protection: the OSH practitioner decides what protection the work needs.", owner: "Site supervisor", due: "Before the shift (06:00)", because: "pm10",
        source: "MoHAP public advice (Khaleej Times, 14 Aug 2022); public advice, not a workplace standard" },
    ];
    if (high) actions.push(
      { text: "Review outdoor tasks: move work indoors or to flexible hours where possible.", owner: "Site supervisor", due: "When setting the shift plan", because: "pm10",
        source: "MoHRE (Gulf News, 24 Mar 2026); WHO 2021 good-practice statement on sand and dust storms" },
      { text: "Follow the emirate's weather directives if issued, for example the wind-speed review of outdoor work.", owner: "Site supervisor", due: "During the shift", because: "pm10",
        source: "Abu Dhabi workplace directives (Gulf News, Dec 2024)" });
    return {
      id: `${zone}|${day.date}|dust`, type: "dust", level: dust.level, chip: high ? "Dust >250" : "Dust >150", zone, zoneName, date: day.date, trigger: "pm10",
      title: high ? "Dust: very high (PM10 above 250)" : "Dust: above the UAE standard (PM10 above 150)",
      summary: `Dusty air: daily mean PM10 ${dust.pm10}\u00a0\u00b5g/m\u00b3 (modelled, CAMS). We found no source that sets a PM10 level at which work must stop: official directives and the site's own assessment decide whether exposure must be cut or work stopped.`,
      leadHours: ISSUE_TO_SHIFT_HOURS, drivers,
      owner: { role: "Site supervisors in the zone", due: "Before the shift (06:00)" },
      chain: [{ role: "OSH practitioner", at: CLOCK.shift }],
      closeWhen: "The shift ends, or the next forecast drops below 150.",
      actions,
    };
  }

  // day: one replay or resolved live day.
  // opts: sim (overrides the seeded site simulation), prevTier and firstHigh (for onset), health (healthDay), dust ({pm10, level}).
  function buildAlerts(zone, zoneName, day, options) {
    if (!day) return [];
    const opts = options || {};
    const sim = opts.sim || simSignals(zone, day.date);
    const out = [];
    const hot = day.tier === "High" || day.tier === "Elevated" || day.tier === "Insufficient data";
    let heatLevel = null;
    if (hot) {
      const h = heatAlert(zone, zoneName, day, sim, opts);
      heatLevel = h.level;
      out.push(h);
      if (!small(sim) && day.tier !== "Insufficient data") { const g = prepAlert(zone, zoneName, day, sim, h.level); if (g) out.push(g); }
    }
    if (opts.health && opts.health.flag) out.push(healthAlert(zone, zoneName, day, opts.health, heatLevel));
    if (opts.dust && (opts.dust.level === "Elevated" || opts.dust.level === "High") && Number.isFinite(opts.dust.pm10)) out.push(dustAlert(zone, zoneName, day, opts.dust));
    if (sim.notices3d > 0 && !small(sim)) out.push(noticeAlert(zone, zoneName, day, sim));
    return out;
  }

  // Who holds the alert at a given time. Only an open (unacknowledged) alert escalates.
  function holder(alert, status, clock) {
    if (status !== "open") return { role: alert.owner.role, escalated: false };
    const passed = alert.chain.filter(c => clock >= c.at);
    return passed.length ? { role: passed[passed.length - 1].role, escalated: true } : { role: alert.owner.role, escalated: false };
  }

  function sortAlerts(list) {
    return [...list].sort((a, b) => (RANK[a.level] ?? 9) - (RANK[b.level] ?? 9) || (TYPE_ORDER[a.type] ?? 9) - (TYPE_ORDER[b.type] ?? 9)
      || Number(!!b.onset) - Number(!!a.onset) || a.zoneName.localeCompare(b.zoneName));
  }

  const api = { SITES, SUPPRESS_BELOW, PREP, CLOCK, SIGNED, simSignals, buildAlerts, holder, sortAlerts, dustLevel };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else root.AlertLogic = api;
})(typeof window !== "undefined" ? window : globalThis);
