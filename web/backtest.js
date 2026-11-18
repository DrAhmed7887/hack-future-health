"use strict";
// v4 back-test explorer: every day of the frozen R4 rule on the 6 US holdout regions (2022-2025, observed weather) next to the
// days with a reported work heat hospitalisation (US OSHA Severe Injury Reports). Data: web/data/backtest.json, built by
// scripts/build_backtest_web.py, which checks its totals against results/holdout_results.json.
(function (root) {
  const LEVEL = { H: "High", E: "Elevated", N: "No alert", X: "Insufficient data" };
  const MONTHS = [5, 6, 7, 8, 9];
  const NAMES = { 5: "May", 6: "June", 7: "July", 8: "August", 9: "September" };

  function years(data) {
    const ys = new Set();
    for (const r of Object.values(data.regions)) for (const d of r.dates) ys.add(Number(d.slice(0, 4)));
    return [...ys].sort((a, b) => a - b);
  }

  function summary(data, region, year) {
    const out = { days: 0, alertDays: 0, high: 0, events: 0, caught: 0, fixedAlertDays: 0, missed: [] };
    for (const [k, r] of Object.entries(data.regions)) {
      if (region && k !== region) continue;
      r.dates.forEach((d, i) => {
        if (year && Number(d.slice(0, 4)) !== year) return;
        const alert = r.tier[i] === "H" || r.tier[i] === "E";
        out.days += 1;
        if (alert) out.alertDays += 1;
        if (r.tier[i] === "H") out.high += 1;
        if (r.fixed[i] === "1") out.fixedAlertDays += 1;
        if (r.event[i] === "1") { out.events += 1; if (alert) out.caught += 1; else out.missed.push(d); }
      });
    }
    return out;
  }

  function at(r, i) {
    return { date: r.dates[i], level: LEVEL[r.tier[i]], event: r.event[i] === "1", fixed: r.fixed[i] === "1",
      hi_f: r.hi_f[i], pctl: r.pctl[i], jump_f: r.jump_f[i], reports: r.reports[i] };
  }

  function day(data, region, date) {
    const r = data.regions[region], i = r ? r.dates.indexOf(date) : -1;
    return i < 0 ? null : at(r, i);
  }

  // The frozen R4 reason in words: heat index at least 80 °F, then percentile >= 60 (High) or >= 50 with a >= 3 °F jump (Elevated).
  function why(d) {
    if (d.level === "Insufficient data") return "Not enough weather data for this day, so the rule gave no level.";
    const ord = n => n + (n % 100 >= 11 && n % 100 <= 13 ? "th" : ["th", "st", "nd", "rd"][n % 10] || "th");
    const jump = `${d.jump_f >= 0 ? "+" : "−"}${Math.abs(d.jump_f).toFixed(1)} °F against the previous 14 days`;
    if (d.level === "High") return `Heat index ${d.hi_f} °F, the ${ord(d.pctl)} percentile of this place's own summers (High from the 60th).`;
    if (d.level === "Elevated") return `Heat index ${d.hi_f} °F at the ${ord(d.pctl)} percentile, with a jump of ${jump} (Elevated: 50th percentile and a 3 °F jump).`;
    if (d.hi_f < 80) return `Heat index ${d.hi_f} °F, below 80 °F, so no alert.`;
    if (d.pctl >= 50) return `Heat index ${d.hi_f} °F at the ${ord(d.pctl)} percentile, but a jump of only ${jump} (Elevated needs 3 °F; High needs the 60th percentile), so no alert.`;
    return `Heat index ${d.hi_f} °F, but only the ${ord(d.pctl)} percentile of this place's own summers (alerts start at the 50th), so no alert.`;
  }

  function months(data, region, year) {
    const r = data.regions[region], idx = new Map(r.dates.map((d, i) => [d, i]));
    return MONTHS.map(m => {
      const n = new Date(Date.UTC(year, m, 0)).getUTCDate();
      const days = [];
      for (let k = 1; k <= n; k += 1) {
        const date = `${year}-${String(m).padStart(2, "0")}-${String(k).padStart(2, "0")}`;
        days.push(idx.has(date) ? at(r, idx.get(date)) : null);
      }
      return { month: m, name: NAMES[m], days };
    });
  }

  // Start where the cases are: the region with the most case days, its busiest year, its first case day.
  function defaultView(data) {
    const regs = Object.keys(data.regions);
    const region = regs.reduce((a, b) => (summary(data, b).events > summary(data, a).events ? b : a));
    const year = years(data).reduce((a, b) => (summary(data, region, b).events > summary(data, region, a).events ? b : a));
    return { region, year, date: firstCase(data, region, year) };
  }

  function firstCase(data, region, year) {
    const r = data.regions[region], i = r.dates.findIndex((d, k) => d.startsWith(String(year)) && r.event[k] === "1");
    return i >= 0 ? r.dates[i] : null;
  }

  const pc = (a, b) => (b ? Math.round(100 * a / b) + "%" : "\u2014");
  const CLS = { High: "h", Elevated: "e", "No alert": "n", "Insufficient data": "x" };

  function detailHtml(data, v, esc, fmtDate) {
    const d = v.date && day(data, v.region, v.date);
    if (!d) return `<p class="small">Tap a day to see its level and why.</p>`;
    const rep = d.reports ? `<strong>${d.reports} reported work heat hospitalisation${d.reports > 1 ? "s" : ""}</strong> (OSHA). ${d.level === "High" || d.level === "Elevated" ? "The rule had alerted." : "The rule missed this day."}` : "No hospitalisation reported.";
    return `<p><strong>${esc(fmtDate(d.date))}</strong> <span class="chip ${CLS[d.level] === "h" ? "high" : CLS[d.level] === "e" ? "elevated" : "none"}">${esc(d.level)}</span></p>
      <p>${esc(why(d))}</p><p>${rep}</p>
      <p class="small">The fixed 80 \u00b0F trigger ${d.fixed ? "would also have alerted" : "would not have alerted"}.</p>`;
  }

  function html(data, v, esc, fmtDate) {
    const s = summary(data, v.region, v.year), regs = Object.entries(data.regions);
    const opts = regs.map(([k, r]) => `<option value="${esc(k)}" ${k === v.region ? "selected" : ""}>${esc(r.name)}</option>`).join("");
    const yrs = years(data).map(y => `<button data-bty="${y}" aria-pressed="${y === v.year}">${y}</button>`).join("");
    const focus = v.date || `${v.year}-05-01`;   // one tab stop for the whole calendar; arrow keys move between days
    const grid = months(data, v.region, v.year).map(m => `<div class="btm"><span class="btl">${m.name}</span><div class="btr">${m.days.map(d => {
      if (!d) return `<span class="c x"></span>`;
      const alert = d.level === "High" || d.level === "Elevated";
      const ev = d.event ? (alert ? " ev" : " ev miss") : "";
      const label = `${d.date}: ${d.level}${d.event ? ", case day" + (alert ? "" : ", missed") : ""}`;
      return `<button class="c ${CLS[d.level]}${ev}" data-btd="${esc(d.date)}" tabindex="${d.date === focus ? 0 : -1}" aria-pressed="${d.date === v.date}" aria-label="${esc(label)}" title="${esc(label)}"></button>`;
    }).join("")}</div></div>`).join("");
    const rows = regs.map(([k, r]) => {
      const t = summary(data, k);
      return `<tr${k === v.region ? ' class="sel"' : ""}><td>${esc(r.name)}</td><td class="num">${t.caught} of ${t.events}</td><td class="num">${pc(t.alertDays, t.days)}</td><td class="num">${pc(t.fixedAlertDays, t.days)}</td></tr>`;
    }).join("");
    const all = summary(data);
    return `<label for="btr" class="small">US region (never used to set the rule)</label><select id="btr">${opts}</select>
      <div class="modes bty" role="group" aria-label="Year">${yrs}</div>
      <p class="btsum"><strong>${s.caught} of ${s.events}</strong> case days had an alert in ${v.year}. It alerted on ${pc(s.alertDays, s.days)} of days; the fixed 80 \u00b0F trigger, on ${pc(s.fixedAlertDays, s.days)}.</p>
      <div class="btcal" role="group" aria-label="May to September ${v.year}, one square a day. Arrow keys move between days.">${grid}</div>
      <div class="modes btnav"><button data-btcase="-1">Previous case day</button><button data-btcase="1">Next case day</button></div>
      <p class="legend-keys small"><span><i class="kh"></i> High</span> <span><i class="ke"></i> Elevated</span> <span><i class="kn"></i> No alert</span> <span><i class="kev"></i> Case day, alerted</span> <span><i class="kmiss"></i> Case day, missed</span></p>
      <div class="btday" aria-live="polite">${detailHtml(data, v, esc, fmtDate)}</div>
      <table><thead><tr><th>Region, 2022 to 2025</th><th>Case days with an alert</th><th>Days alerted</th><th>Fixed 80 \u00b0F trigger</th></tr></thead>
      <tbody>${rows}<tr class="total"><td>All 6</td><td class="num">${all.caught} of ${all.events}</td><td class="num">${pc(all.alertDays, all.days)}</td><td class="num">${pc(all.fixedAlertDays, all.days)}</td></tr></tbody></table>`;
  }

  // The case day before or after `date` in this region and year (wraps round); null when the year has none.
  function stepCase(data, region, year, date, dir) {
    const r = data.regions[region];
    const cases = r.dates.filter((d, k) => d.startsWith(String(year)) && r.event[k] === "1");
    if (!cases.length) return null;
    const i = cases.indexOf(date);
    if (i < 0) return dir > 0 ? (cases.find(d => !date || d > date) || cases[0]) : ([...cases].reverse().find(d => !date || d < date) || cases[cases.length - 1]);
    return cases[(i + dir + cases.length) % cases.length];
  }

  const api = { LEVEL, years, summary, day, why, months, defaultView, firstCase, stepCase, html, detailHtml };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else root.Backtest = api;
})(typeof window !== "undefined" ? window : globalThis);
