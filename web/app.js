"use strict";
// Heat Shift Planner. Reads data/*.json produced by scripts/build_web_data.py. No numbers are typed in by hand here.

const state = { zone: null, crew: { newWorkers: null, heavy: null }, replayDate: null, ackAt: null };
let DATA = { live: null, replay: null, evidence: null };

const SIM_SITES = { mussafah: 12, adcity: 9, ruwais: 4, alain: 7 };   // simulated, labelled in the UI
const SIM_NOTICES = { mussafah: 1, alain: 1 };                          // simulated incident notices, last 3 days
const SIM_COOLING = { mussafah: 7, adcity: 5, ruwais: 2, alain: 4 };     // simulated: sites with a cooling station ready (S7c)
const SUPPRESS_BELOW = 5;
const ZONE_NOTE = { mussafah: "Industrial area and workshops", adcity: "City construction sites", ruwais: "Industrial area, Al Dhafra, coastal", alain: "Inland, drier heat" };                                               // signed S6

function store(key, value) { try { localStorage.setItem(key, JSON.stringify(value)); } catch (e) { /* storage blocked: fine */ } }
function recall(key) { try { return JSON.parse(localStorage.getItem(key)); } catch (e) { return null; } }
function esc(s) { return String(s).replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c])); }
function fmtDate(iso) { return new Date(iso + "T12:00:00").toLocaleDateString("en-GB", { weekday: "short", day: "numeric", month: "short", year: "numeric" }); }
function pct(x) { return Math.round(x * 100) + "%"; }
function pct1(x) { return (Math.round(x * 1000) / 10).toFixed(1) + "%"; }   // one decimal, as in README
function pts1(x) { return (Math.round(x * 1000) / 10).toFixed(1).replace("-", "\u2212"); }

async function load() {
  const get = p => fetch(p, { cache: "no-store" }).then(r => { if (!r.ok) throw new Error(p + " " + r.status); return r.json(); });
  try {
    [DATA.live, DATA.replay, DATA.evidence] = await Promise.all([get("data/live.json"), get("data/replay.json"), get("data/evidence.json")]);
  } catch (e) {
    document.getElementById("app").innerHTML = `<h1>The forecast data did not load</h1><p>Reload the page. If it keeps failing, the data files are missing from this deployment (${esc(e.message)}).</p>${legalBlock({ date: HeatLogic.dubaiDate(new Date(), 1) })}`;
    return;
  }
  state.zone = recall("zone");
  if (!DATA.replay || !Object.prototype.hasOwnProperty.call(DATA.replay, state.zone)) state.zone = null;   // corrupt or old saved value
  window.addEventListener("hashchange", render);
  render();
}

function liveDay(zone) {
  return HeatLogic.resolveDay(DATA.live.zones[zone], DATA.live.generated_utc, new Date());
}

function currentDay() {
  if (!state.zone) return null;
  if (state.replayDate) return DATA.replay[state.zone].days.find(d => d.date === state.replayDate) || null;
  return liveDay(state.zone);
}

function legalBlock(day) {
  const items = HeatLogic.legalItems(day, !!state.replayDate).map(i => `<li>${esc(i.t)}<span class="src">${esc(i.s)}</span></li>`).join("");
  return `<section class="legal" aria-labelledby="law"><h2 id="law">Required by law, whatever the forecast</h2><ul>${items}</ul></section>`;
}

const TIERS = {
  "High": { cls: "high", word: "High", what: "Hotter than most days here at this time of year. Extra steps are in the plan." },
  "Elevated": { cls: "elevated", word: "Elevated", what: "Warmer than usual here and rising. Extra checks are in the plan." },
  "No escalation": { cls: "none", word: "No extra steps", what: "The forecast adds no steps. The law and the always-on protections still apply." },
  "Insufficient data": { cls: "none off", word: "Not enough data", what: "The forecast is missing or out of date. Treat tomorrow as Elevated until it updates." },
  "Outside tested season": { cls: "none off", word: "Outside tested season", what: "Alerts were tested for May to September only. The law and the always-on protections still apply." },
};
const legalItems = day => HeatLogic.legalItems(day, !!state.replayDate);

function whySentence(day) {
  if (!Number.isFinite(day.max_temp_c)) return day.stale ? "The forecast is missing or out of date, so no numbers are shown." : "No forecast numbers are available for this day.";
  const peak = day.peak_hour != null ? ` Heat and humidity together peak around ${day.peak_hour}:00.` : "";
  const air = `Air temperature up to ${day.max_temp_c}\u00a0°C.${peak}`;
  if (day.tier === "Outside tested season" || day.percentile == null || day.anomaly_f == null) return air;
  const rank = day.percentile >= 99 ? "as hot as the hottest days here at this time of year in 2015 to 2021"
    : `hotter than ${day.percentile}% of days here at this time of year`;
  const d = Math.round(Math.abs(day.anomaly_f) * 5 / 9 * 10) / 10;
  return `${air} On that combined measure, it is ${rank}, and ${d}\u00a0°C ${day.anomaly_f >= 0 ? "above" : "below"} the previous 14 days.`;
}

// concrete grey -> warning yellow -> danger red (ISO 7010 colours), by position in the zone's summer
function heatColour(t) {
  const stops = [[233, 236, 234], [242, 183, 5], [179, 38, 30]];
  const [a, b, u] = t < 0.5 ? [stops[0], stops[1], t / 0.5] : [stops[1], stops[2], (t - 0.5) / 0.5];
  return `rgb(${a.map((x, i) => Math.round(x + (b[i] - x) * u)).join(",")})`;
}

function strip(day) {
  const days = DATA.replay[state.zone].days.map(d => d.heat_index_f).sort((a, b) => a - b);
  const lo = days[0], hi = days[days.length - 1], w = 300, n = days.length;
  const bars = days.map((v, i) => {
    const t = (v - lo) / (hi - lo || 1);
    return `<rect x="${(i / n * w).toFixed(2)}" y="8" width="${(w / n + 0.3).toFixed(2)}" height="30" fill="${heatColour(t)}"/>`;
  }).join("");
  const pos = Math.min(1, Math.max(0, (day.heat_index_f - lo) / (hi - lo || 1))) * w;
  return `<div class="strip" aria-label="Tomorrow's heat index compared with every day of summer 2025 in this zone">
    <svg viewBox="0 0 ${w} 46" preserveAspectRatio="none" role="img">${bars}
      <rect x="${(pos - 1.5).toFixed(1)}" y="0" width="3" height="46" fill="#1C2321"/></svg>
    <div class="legend"><span>Coolest day, summer 2025</span><span>Hottest</span></div></div>`;
}

function zoneBar() {
  const name = DATA.replay[state.zone].name;
  const replay = state.replayDate ? `<p class="small">Replay of a real day: ${esc(fmtDate(state.replayDate))}. <a href="#home" data-act="live">Back to tomorrow's forecast</a></p>` : "";
  return `<div class="zonebar"><strong>${esc(name)}</strong><a href="#site">Change site</a></div>${replay}`;
}

function cta(primaryHref, primaryText, secondary) {
  return `<div class="cta"><div>${secondary || ""}<a class="btn" href="${primaryHref}">${primaryText}</a></div></div>`;
}

const VIEWS = {
  site() {
    const z = Object.entries(DATA.replay).map(([k, v]) => `<button data-zone="${esc(k)}">${esc(v.name)}<span>${esc(ZONE_NOTE[k] || "")}</span></button>`).join("");
    return `<h1>Where does your crew work?</h1><p>Each zone's days are ranked against its own weather in 2015 to 2021. The cut-offs were tested on US data.</p><div class="zones">${z}</div>`;
  },
  home() {
    if (!state.zone) return VIEWS.site();
    const day = currentDay();
    if (!day) return `${zoneBar()}<h1>No data for this day</h1><p>Use the law and the always-on protections.</p>${legalBlock({ date: state.replayDate || HeatLogic.dubaiDate(new Date(), 1) })}`;
    const t = TIERS[day.tier] || TIERS["Insufficient data"];
    const when = state.replayDate ? "That day" : `${day.when || "Tomorrow"}, ${esc(fmtDate(day.date))}`;
    const issued = state.replayDate ? "Real weather for that day (ERA5 reanalysis)." : `Forecast issued ${esc(DATA.live.generated_utc)} UTC. Next update scheduled for 18:00 Abu Dhabi time.`;
    const off = day.tier === "Outside tested season" && !state.replayDate ? `<p><a href="#replay">Replay a real summer day</a> to see how alerts work.</p>` : "";
    return `${zoneBar()}
      <section class="tier ${t.cls}" aria-live="polite"><p class="small">${when}</p><p class="word">${t.word}</p><p class="what">${t.what}</p></section>
      <p class="why">${esc(whySentence(day))}</p>${Number.isFinite(day.heat_index_f) ? strip(day) : ""}
      <p class="small">${issued} <a href="#trust">How was this tested?</a></p>${off}
      ${legalBlock(day)}
      ${cta("#crew", state.replayDate ? "Plan that day's crew" : "Plan tomorrow's crew")}`;
  },
  crew() {
    if (!state.zone) return VIEWS.site();
    const q = (key, text, help) => {
      const v = state.crew[key];
      const opt = (val, label) => `<label><input type="radio" name="${key}" value="${val}" ${v === val ? "checked" : ""}><span>${label}</span></label>`;
      return `<fieldset><legend>${text}</legend><div class="seg">${opt("yes", "Yes")}${opt("no", "No")}${opt("unsure", "Not sure")}</div><p class="small">${help}</p></fieldset>`;
    };
    return `${zoneBar()}<h1>Who is working, doing what?</h1>
      <p>Two answers. No names are collected.</p>
      ${q("newWorkers", "Does the crew include new or returning workers?", "New: in their first 5 days. Returning: back after more than 14 days away.")}
      ${q("heavy", "Is heavy outdoor work planned?", "For example a concrete pour, manual lifting or digging.")}
      <p class="small">"Not sure", or no answer, is treated as yes.</p>
      ${cta("#plan", "See the plan", `<a class="btn secondary" href="#home">Back</a>`)}`;
  },
  plan() {
    if (!state.zone) return VIEWS.site();
    const day = currentDay();
    if (!day) return VIEWS.home();
    const inSeason = HeatLogic.inTestedSeason(day.date) && day.tier !== "Outside tested season";
    const { tier, raised } = HeatLogic.effectiveTier(day.tier, state.crew);
    const li = (text, owner) => `<li>${esc(text)}<span class="owner">${esc(owner)}</span></li>`;
    const law = legalItems(day).map(i => li(i.t, i.s)).join("");
    const always = [
      li("Drinking water at the work area: at least 2 litres every 2 to 3 hours for each worker.", "Employer · ADPHC OSH Code of Practice 11.0"),
      li("Shade and cooling shelters for everyone working outside in the summer months.", "Employer · ADPHC OSH Code of Practice 11.0, section 3.2(b)(vii)"),
      li("Nobody works alone in heat stress areas.", "Supervisor · ADPHC OSH Code of Practice 11.0, section 3.2(e)"),
      li("Anyone with heat symptoms stops work now: rest in a cool, shaded place, drink water, cool down. If confused, collapsed or not improving, call an ambulance on 998 and start cooling at once: see the red emergency card at the top of every screen.", "Everyone on site · ADPHC Technical Guideline, Safety in the Heat, sections 4.4(c) and 4.5(c); ambulance 998 (u.ae)"),
    ].join("");
    const steps = HeatLogic.planSteps(tier, state.crew, inSeason, day.peak_hour).map(x => li(x.text, x.owner));
    const t = TIERS[tier] || TIERS["Insufficient data"];
    const note = raised ? `<p class="status">Raised one level from ${esc(day.tier === "Insufficient data" ? "Elevated" : day.tier)} because the crew may include new or returning workers. This is our rule, based on guidelines, not tested on outcomes.</p>` : "";
    const ack = state.ackAt
      ? `<div class="ack" role="status"><strong>Plan acknowledged at ${esc(state.ackAt)}.</strong><p>Plans not acknowledged by 06:30 would go to the OSH practitioner (this demo sends nothing). Next forecast scheduled for 18:00 Abu Dhabi time.</p></div>`
      : `<p class="small">Plans not acknowledged by 06:30 would go to the OSH practitioner (this demo sends nothing).</p>`;
    return `${zoneBar()}<h1>${state.replayDate ? "The plan for that day" : "Tomorrow's plan"}</h1>
      <section class="tier ${t.cls}"><p class="word">${t.word}</p></section>${note}
      <section class="layer law"><h2>Required by law</h2><ul class="actions">${law}</ul></section>
      <section class="layer"><h2>Always on</h2><ul class="actions">${always}</ul></section>
      <section class="layer model"><h2>Because of the forecast and your crew</h2><p class="status">Based on guidelines and a heat rule tested on US data. Not yet validated in Abu Dhabi.</p><ul class="actions">${steps.join("")}</ul></section>
      ${ack}
      ${cta("#plan", state.ackAt ? "Acknowledged" : "Acknowledge plan", `<a class="btn secondary" href="#crew">Edit crew</a>`)}`;
  },
  trust() {
    const e = DATA.evidence, h = e.holdout;
    return `<h1>How was this tested?</h1>
      <p>There is no public data on heat illness at work in Abu Dhabi. So the rule was tested on the closest real record we could find: the work-related heat hospitalisations reported to US federal OSHA from January 2015 to November 2025 (${e.reports_total.toLocaleString()} reports), matched with the weather on that day.</p>
      <div class="facts">
        <div><span class="big">${pct1(h.r4_sensitivity)}</span><p>of days with a reported heat hospitalisation got an alert, in ${h.regions} US regions the rule had never seen (${h.event_days} such days; 95% interval ${pct1(h.r4_ci[0])} to ${pct1(h.r4_ci[1])}). It alerted on ${pct(h.r4_alert_share)} of days.</p></div>
        <div><span class="big">${pct(e.fixed_80f_alert_share)}</span><p>of days in the same unseen regions would get an alert under the common fixed trigger (heat index 80 °F). An alert that rarely switches off is easy to ignore.</p></div>
        <div><span class="big">${Math.round(h.spread_r4 * 100)} vs ${Math.round(h.spread_r2 * 100)}</span><p>points of spread in alert load between cool and hot cities: thresholds set from each place's own climate, against fixed thresholds.</p></div>
        <div><span class="big">${pct(e.dayahead_same_decision)}</span><p>of days got the same decision from the forecast made the evening before as from the weather that actually happened (8 US regions, 2024 to 2025). The forecast ran warm, so it alerted on more days (${pct(e.dayahead_alert_share)} against ${pct(e.observed_alert_share_same_days)}).</p></div>
      </div>
      <h2>What did not work</h2>
      <p>We expected recent incident reports nearby to improve the alert. A rule that also used them as a trigger, tuned to the same training alert budget, caught ${pts1(Math.abs(e.workplace_trigger.r3_minus_r2))} percentage points ${e.workplace_trigger.r3_minus_r2 < 0 ? "fewer" : "more"} heat days than a weather-only rule tuned separately (earlier fixed-threshold rules, 8 US regions, 2022 to 2025; difference ${pts1(e.workplace_trigger.r3_minus_r2)}, 95% interval ${pts1(e.workplace_trigger.ci[0])} to ${pts1(e.workplace_trigger.ci[1])}). So here they are a prompt to check that workplace, not a reason to raise the alert.</p>
      <h2>We also trained a model</h2>
      <p>A risk model trained on the same years with more inputs (night-time heat, days in a row of unusual heat, sunshine, wind) ranked days better than this rule (AUC ${e.trained_model.auc.toFixed(2)} against ${e.trained_model.auc_rule.toFixed(2)}) and caught ${pct1(e.trained_model.sensitivity)} of case days in the unseen regions. But it learned that hot places have more cases, not which days are unusual: its alert load swung by ${Math.round(e.trained_model.spread * 100)} points between cities, and in Abu Dhabi it would alert on ${pct(e.trained_model.abu_dhabi_alert_share[0])} to ${pct(e.trained_model.abu_dhabi_alert_share[1])} of summer days. It missed the pass mark we set before scoring, so the app keeps the rule.</p>
      <h2>Limits</h2>
      <p>US data, reported cases only, and most cases go unreported. Not validated on Abu Dhabi outcomes. Tested for May to September only. It does not calculate the Thermal Work Limit. The heat index is used only to rank days: the US weather service says its formula "is not valid for extreme temperature and relative humidity conditions", conditions Abu Dhabi summers can reach. The crew rules come from guidelines and were not tested. It is decision support for supervisors, not a diagnosis, and never a clearance to work.</p>
      ${cta("#home", "Back to the plan")}`;
  },
  replay() {
    const zone = state.zone || "mussafah";
    const days = DATA.replay[zone].days;
    const by = f => days.reduce((a, b) => (f(b) > f(a) ? b : a));
    const firstHigh = days.find(d => d.tier === "High");
    const sorted = [...days].sort((a, b) => a.percentile - b.percentile);
    const picks = [
      ["Hottest day", by(d => d.heat_index_f)], ["Biggest jump", by(d => d.anomaly_f ?? -99)],
      ["First High of the season", firstHigh], ["A normal summer day", sorted[Math.floor(sorted.length / 2)]],
    ].filter((p, i, all) => p[1] && all.findIndex(q => q[1] && q[1].date === p[1].date) === i);
    const zones = Object.entries(DATA.replay).map(([k, v]) => `<option value="${k}" ${k === zone ? "selected" : ""}>${esc(v.name)}</option>`).join("");
    return `<h1>Replay a real day</h1>
      <p>Alerts run May to September. Pick a day from summer 2025 to see what the app would have shown, using that day's real weather.</p>
      <label for="rz" class="small">Site</label><select id="rz">${zones}</select>
      <div class="picks">${picks.map(([label, d]) => `<button data-day="${d.date}">${label}: ${esc(fmtDate(d.date))}</button>`).join("")}</div>
      <label for="rd" class="small" style="display:block;margin-top:14px">Or any date</label>
      <input id="rd" type="date" min="2025-05-01" max="2025-09-30" value="2025-07-15">
      ${cta("#home", "Show this day", "")}`;
  },
  help() {
    const steps = HeatLogic.EMERGENCY_STEPS.map(x => `<li>${esc(x)}</li>`).join("");
    return `<h1>Suspected heat stroke: cool first</h1>
      <p>Confused, collapsed or acting strangely while working in heat? Treat it as heat stroke. Cooling on site, straight away, is what saves lives.</p>
      <a class="btn call" href="tel:998">Call 998</a>
      <ol class="sos-steps">${steps}</ol>
      <p class="small">${esc(HeatLogic.EMERGENCY_SOURCES)}. First aid for a supervisor, not a diagnosis. Follow the ambulance call-taker's instructions.</p>
      ${cta("#home", "Back to the plan")}`;
  },
  regulator() {
    const rows = Object.entries(DATA.replay).map(([k, v]) => {
      const day = state.replayDate ? v.days.find(d => d.date === state.replayDate) : liveDay(k);
      const t = TIERS[day?.tier] || TIERS["Insufficient data"];
      const n = SIM_SITES[k];
      const head = `<div class="zrow"><strong>${esc(v.name)}</strong><span class="chip ${t.cls}">${t.word}</span></div>`;
      if (n < SUPPRESS_BELOW) return `<li>${head}<p class="small">Fewer than ${SUPPRESS_BELOW} sites in this zone, so site counts are hidden.</p></li>`;
      const notice = SIM_NOTICES[k] ? `<p><strong>${SIM_NOTICES[k]} incident notice in the last 3 days.</strong> Check that site's acclimatisation plan and rest breaks. This does not change the tier.</p>` : `<p class="small">No incident notices in the last 3 days.</p>`;
      const hot = day && (day.tier === "Elevated" || day.tier === "High");
      const cooling = hot ? `<p>Cooling station ready: ${SIM_COOLING[k]} of ${n} sites</p>` : "";
      return `<li>${head}<p>Plans acknowledged: ${Math.floor(n * 0.75)} of ${n} sites</p>${cooling}${notice}</li>`;
    }).join("");
    return `<h1>Regulator view</h1>
      <p>Zones, not people. ${state.replayDate ? esc(fmtDate(state.replayDate)) + " (replay)." : "Tomorrow's forecast."}</p>
      <ul class="zlist">${rows}</ul>
      <p class="small">Sites, acknowledgements, cooling stations and incident notices are simulated for the demo. No individual worker data is collected. Not for employment or disciplinary use.</p>
      ${cta("#home", "Back to the site view")}`;
  },
};

function render() {
  const route = (location.hash || "#home").slice(1);
  const view = VIEWS[route] || VIEWS.home;
  const app = document.getElementById("app");
  app.innerHTML = view();
  bind(route);
  app.focus({ preventScroll: true });
  window.scrollTo(0, 0);
}

function bind(route) {
  document.querySelectorAll("[data-zone]").forEach(b => b.addEventListener("click", () => {
    state.zone = b.dataset.zone; store("zone", state.zone); location.hash = "#home"; render();
  }));
  document.querySelectorAll("[data-act=live]").forEach(a => a.addEventListener("click", () => { state.replayDate = null; state.ackAt = null; }));
  document.querySelectorAll("input[type=radio]").forEach(r => r.addEventListener("change", () => { state.crew[r.name] = r.value; state.ackAt = null; render(); }));
  if (route === "plan") {
    const btn = document.querySelector(".cta .btn:not(.secondary)");
    if (btn) btn.addEventListener("click", ev => { ev.preventDefault(); if (!state.ackAt) { state.ackAt = new Date().toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit" }); render(); } });
  }
  if (route === "replay") {
    const rz = document.getElementById("rz"), rd = document.getElementById("rd");
    rz.addEventListener("change", () => { state.zone = rz.value; store("zone", state.zone); render(); });
    document.querySelectorAll("[data-day]").forEach(b => b.addEventListener("click", () => { state.zone = rz.value; state.replayDate = b.dataset.day; state.ackAt = null; location.hash = "#home"; }));
    document.querySelector(".cta .btn").addEventListener("click", ev => {
      ev.preventDefault(); state.zone = rz.value; store("zone", state.zone);
      state.replayDate = rd.value && rd.value >= "2025-05-01" && rd.value <= "2025-09-30" ? rd.value : "2025-07-15";
      state.ackAt = null; location.hash = "#home";
    });
  }
}

load();
