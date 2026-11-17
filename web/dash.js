"use strict";
// v3 risk map: map + alert feed + season timeline + alert detail (drivers, follow-up, prevention plan).
// Mounted by app.js on #map. Updates its own parts in place so the map is not rebuilt on every change.
(function (root) {
  const A = root.AlertLogic, H = root.HeatLogic;
  const LL = { mussafah: [24.35, 54.50], adcity: [24.47, 54.37], ruwais: [24.11, 52.73], alain: [24.21, 55.74] };   // scripts/abu_dhabi_tiers.py
  const DEFAULT_DATE = "2025-07-15";   // a replay day with every alert type (High, Elevated, gap, notice)
  const COLOUR = { High: "#B3261E", Elevated: "#F2B705", "Insufficient data": "#F2B705", "No escalation": "#9AA3A0", "Outside tested season": "#FFFFFF" };
  const WORD = { High: "High", Elevated: "Elevated", "Insufficient data": "No data", "No escalation": "No extra steps", "Outside tested season": "Off season" };
  const BASIS = { tested: "Tested on US outcomes", guideline: "From guidelines, not tested", rule: "App rule", simulated: "Simulated" };
  const SHORT = { rank: "heat rank against local climate", jump: "rise over the last 14 days", gate: "heat index floor", data: "missing forecast",
    newWorkers: "new or returning workers", heavy: "heavy work planned", heat: "heat alert", cooling: "cooling stations ready", acked: "plans acknowledged", notices: "incident notices" };
  const CLOCKS = [["evening", "18:00 the evening before"], ["shift", "06:30"], ["mid", "09:00"], ["end", "18:00 on the day"]];
  const STATUS_WORD = { open: "Open", acknowledged: "Acknowledged", done: "Actions done", closed: "Closed" };
  const KEY = "hsp.v3";

  let ctx = null, el = null, map = null, markers = {}, timer = null;
  const D = { mode: "replay", date: DEFAULT_DATE, zone: null, alertId: null, clock: "evening" };

  // Demo state, this browser only: { status: {alertId: "acknowledged"}, done: {"alertId#i": true} }
  function loadState() {
    let s = null;
    try { s = JSON.parse(localStorage.getItem(KEY)); } catch (e) { s = null; }
    const obj = v => (v && typeof v === "object" && !Array.isArray(v) ? v : {});
    return { status: obj(s && s.status), done: obj(s && s.done) };
  }
  function saveState(s) { try { localStorage.setItem(KEY, JSON.stringify(s)); } catch (e) { /* storage blocked: the demo still works for this view */ } }
  let S = loadState();
  const setStatus = (id, st) => { S = { ...S, status: { ...S.status, [id]: st } }; saveState(S); };
  const toggleDone = (k) => { S = { ...S, done: { ...S.done, [k]: !S.done[k] } }; saveState(S); };
  const statusOf = id => (Object.prototype.hasOwnProperty.call(STATUS_WORD, S.status[id]) ? S.status[id] : "open");

  const esc = s => ctx.esc(s);
  const zones = () => Object.entries(ctx.DATA.replay);
  const seasonDays = () => ctx.DATA.replay.mussafah.days.map(d => d.date);
  const liveInSeason = () => zones().some(([k]) => ctx.liveDay(k).tier !== "Outside tested season");

  function dayFor(k) {
    if (D.mode === "live") return ctx.liveDay(k);
    return ctx.DATA.replay[k].days.find(d => d.date === D.date) || null;
  }
  function alertsNow() {
    return A.sortAlerts(zones().flatMap(([k, v]) => A.buildAlerts(k, v.name, dayFor(k))));
  }

  function skeleton() {
    return `<section class="dash">
      <div class="dash-head">
        <h1>Heat risk across Abu Dhabi</h1>
        <div class="modes" role="group" aria-label="Which day to show">
          <button type="button" data-mode="live">Tomorrow (live forecast)</button>
          <button type="button" data-mode="replay">Replay summer 2025</button>
        </div>
        <p id="d-banner" class="banner"></p>
      </div>
      <div class="dash-left"><div class="dash-map">
        <div id="d-map" class="map" role="img" aria-label="Map of the four zones, coloured by heat level"></div>
        <div id="d-zones" class="zchips" role="group" aria-label="Zones"></div>
        <ul class="legend-keys" aria-label="Map key"><li><i style="background:#B3261E"></i>High</li><li><i style="background:#F2B705"></i>Elevated or no data</li><li><i style="background:#9AA3A0"></i>No extra steps</li><li><i class="off"></i>Outside tested season</li></ul>
      </div>
      <div class="dash-time" id="d-time"></div>
      <p class="small dash-note">Weather and the heat rule are real. Sites, crews, plan acknowledgements, cooling stations and incident notices are simulated (seeded, <a href="https://github.com/DrAhmed7887/hack-future-health/blob/main/docs/data_card_simulated.md">data card</a>). Statuses are stored only in this browser and no alert or personal data is sent anywhere. Zones, never people. The heat index on the map is the forecast or replay peak.</p></div>
      <div class="dash-side">
        <div class="clock" role="group" aria-label="Simulate the clock">
          <span class="small">Clock:</span>${CLOCKS.map(([k, t]) => `<button type="button" data-clock="${k}">${t}</button>`).join("")}
        </div>
        <div id="d-board" class="board"></div>
        <h2 id="d-feedh">Alerts</h2>
        <ol id="d-feed" class="feed"></ol>
        <div id="d-detail" class="detail"></div>
        <p id="d-say" class="vh" aria-live="polite"></p>
      </div>
    </section>`;
  }

  function initMap() {
    if (!root.L) { el.querySelector("#d-map").outerHTML = `<p class="small" id="d-map">The map library did not load. The zone buttons below work the same way.</p>`; return; }
    map = root.L.map("d-map", { scrollWheelZoom: false, attributionControl: true, zoomSnap: 0.25, dragging: !root.L.Browser.mobile, tap: false }).fitBounds([[23.5, 52.3], [24.8, 56.2]]);
    root.L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 12, attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    }).addTo(map);
    for (const [k, v] of zones()) {
      const m = root.L.circleMarker(LL[k], { radius: 16, weight: 2, color: "#1C2321", fillOpacity: 0.9 }).addTo(map);
      m.bindTooltip(esc(v.name), { permanent: true, direction: k === "adcity" ? "top" : "bottom", offset: [0, k === "adcity" ? -14 : 14], className: "ztip" });
      m.on("click", () => selectZone(k));
      markers[k] = m;
    }
  }

  function updateMap() {
    for (const [k, v] of zones()) {
      const day = dayFor(k), tier = day ? day.tier : "Insufficient data";
      if (markers[k]) {
        markers[k].setStyle({ fillColor: COLOUR[tier] || "#F2B705", dashArray: tier === "Insufficient data" ? "4 3" : null, weight: D.zone === k ? 5 : 2 });
        markers[k].setTooltipContent(`<strong>${esc(v.name)}</strong> ${esc(WORD[tier] || tier)}`);
      }
    }
    el.querySelector("#d-zones").innerHTML = zones().map(([k, v]) => {
      const day = dayFor(k), tier = day ? day.tier : "Insufficient data";
      const hi = day && Number.isFinite(day.heat_index_c) ? `, ${day.heat_index_c}\u00a0°C` : "";
      return `<button type="button" data-z="${esc(k)}" aria-pressed="${D.zone === k}"><i style="background:${COLOUR[tier] || "#F2B705"}"></i>${esc(v.name)}<span>${esc(WORD[tier] || tier)}${esc(hi)}</span></button>`;
    }).join("") + (D.zone ? `<button type="button" data-z="">All zones</button>` : "");
  }

  function banner() {
    if (D.mode === "live") {
      const d0 = ctx.liveDay("mussafah");
      const nums = zones().map(([k, v]) => { const d = ctx.liveDay(k); return Number.isFinite(d.heat_index_c) ? `${v.name} ${d.heat_index_c} °C` : null; }).filter(Boolean).join(", ");
      const off = !liveInSeason();
      return `<strong>${esc(d0.when || "Tomorrow")}, ${esc(ctx.fmtDate(d0.date))}.</strong> ${off ? "Outside the tested season: heat alerts run May to September, so none are raised. " : ""}${nums ? `Forecast peak heat index: ${esc(nums)}.` : "No usable forecast."} Issued ${esc(ctx.DATA.live.generated_utc)} UTC; next update 18:00 Abu Dhabi time.${off ? ` <button type="button" class="linkbtn" data-mode="replay">See a summer day</button>` : ""}`;
    }
    return `<strong>Replay: ${esc(ctx.fmtDate(D.date))}.</strong> Real weather for that day (ERA5), ranked against each zone's own 2015 to 2021 climate. Drag the timeline or press play.`;
  }

  function timeline() {
    const days = seasonDays(), i = Math.max(0, days.indexOf(D.date)), n = days.length;
    const rows = zones().map(([k, v], r) => v.days.map((d, j) => `<rect x="${j}" y="${r * 6}" width="1" height="5" fill="${COLOUR[d.tier] || "#F2B705"}" data-i="${j}"><title>${esc(v.name)}, ${esc(d.date)}: ${esc(WORD[d.tier] || d.tier)}</title></rect>`).join("")).join("");
    const months = [["May", 0], ["Jun", 31], ["Jul", 61], ["Aug", 92], ["Sep", 123]].map(([m, x]) => `<span style="left:${(x / n * 100).toFixed(2)}%">${m}</span>`).join("");
    const live = D.mode === "live";
    return `<fieldset ${live ? "disabled" : ""}><legend class="small">${live ? "Timeline (replay only)" : "Summer 2025, day by day"}</legend>
      <div class="trow"><button type="button" id="d-play" class="btn secondary">${timer ? "Pause" : "Play"}</button>
      <label for="d-range" class="vh">Replay date</label>
      <input id="d-range" type="range" min="0" max="${n - 1}" step="1" value="${i}" aria-valuetext="${esc(ctx.fmtDate(days[i]))}">
      <output for="d-range" id="d-out">${esc(ctx.fmtDate(days[i]))}</output></div>
      <div class="season"><svg viewBox="0 0 ${n} ${zones().length * 6 - 1}" preserveAspectRatio="none" role="img" aria-label="Heat level for each zone on every day of summer 2025">${rows}
        <rect id="d-cursor" x="${i - 0.5}" y="0" width="2" height="${zones().length * 6}" fill="none" stroke="#1C2321" stroke-width="0.6"/></svg>
        <div class="months">${months}</div>
        <div class="srows small">${zones().map(([, v]) => `<span>${esc(v.name)}</span>`).join("")}</div></div></fieldset>`;
  }

  function board(list) {
    const c = { open: 0, escalated: 0, acknowledged: 0, done: 0, closed: 0 };
    for (const a of list) {
      const st = statusOf(a.id), h = A.holder(a, st, A.CLOCK[D.clock]);
      c[h.escalated ? "escalated" : st] += 1;
    }
    return [["open", "Open"], ["escalated", "Escalated"], ["acknowledged", "Acknowledged"], ["done", "Actions done"], ["closed", "Closed"]]
      .map(([k, t]) => `<div class="${k}"><span class="n">${c[k]}</span>${t}</div>`).join("");
  }

  function feedItem(a) {
    const st = statusOf(a.id), h = A.holder(a, st, A.CLOCK[D.clock]);
    const who = h.escalated ? `<span class="esc">Escalated to ${esc(h.role)}</span>` : `With ${esc(h.role)} · ${esc(a.owner.due)}`;
    return `<li><button type="button" data-a="${esc(a.id)}" aria-pressed="${D.alertId === a.id}" class="lv-${a.level.toLowerCase()}">
      <span class="chip ${a.level.toLowerCase()}">${esc(a.level)}</span><strong>${esc(a.zoneName)}: ${esc(a.title)}</strong>
      <span class="sum">${esc(a.summary)}</span><span class="who">${who} · <em>${esc(STATUS_WORD[st])}</em></span></button></li>`;
  }

  function driverRow(d) {
    const bar = Number.isFinite(d.value) && Number.isFinite(d.min) && Number.isFinite(d.max) ? (() => {
      const pos = v => Math.min(100, Math.max(0, (v - d.min) / (d.max - d.min) * 100)).toFixed(1);
      return `<div class="bar" aria-hidden="true"><i style="width:${pos(d.value)}%" class="${d.met ? "met" : ""}"></i>${Number.isFinite(d.threshold) ? `<b style="left:${pos(d.threshold)}%"></b>` : ""}</div>`;
    })() : "";
    const tags = [`<span class="tag ${d.basis}">${esc(BASIS[d.basis] || d.basis)}</span>`, d.simulated && d.basis !== "simulated" ? `<span class="tag simulated">Simulated</span>` : "", d.role === "context" ? `<span class="tag ctx">Context</span>` : ""].join("");
    return `<li class="${d.met ? "met" : "unmet"}"><span class="dlabel">${d.met ? "●" : "○"} ${esc(d.label)}</span>${bar}<span class="tags">${tags}</span></li>`;
  }

  function detail(list) {
    const a = list.find(x => x.id === D.alertId);
    if (!a) {
      if (!list.length) return `<p class="empty">${D.mode === "live" && !liveInSeason() ? "No alerts: tomorrow is outside the tested season. The law and the always-on protections still apply." : "No alerts for this day. The law and the always-on protections still apply."}</p>`;
      return `<p class="empty">Select an alert to see why it fired, who follows up, and the prevention plan.</p>`;
    }
    const st = statusOf(a.id), h = A.holder(a, st, A.CLOCK[D.clock]);
    const groups = [...new Set(a.drivers.map(d => d.group))].map(g => `<h4>${esc(g)}</h4><ul class="drivers">${a.drivers.filter(d => d.group === g).map(driverRow).join("")}</ul>`).join("");
    const chain = [`<li><strong>${esc(a.owner.role)}</strong> · ${esc(a.owner.due)}</li>`, ...a.chain.map(c => `<li>If still open at ${esc(CLOCKS.find(([k]) => A.CLOCK[k] === c.at)?.[1] || "")}: <strong>${esc(c.role)}</strong></li>`)].join("");
    const btn = (s, t, off) => `<button type="button" data-st="${s}" aria-pressed="${st === s}" ${off ? "disabled" : ""}>${t}</button>`;
    const allTicked = a.actions.every((x, i) => S.done[`${a.id}#${i}`]);
    const acts = a.actions.map((x, i) => {
      const k = `${a.id}#${i}`;
      return `<li><label><input type="checkbox" data-done="${esc(k)}" ${S.done[k] ? "checked" : ""}><span class="atext">${esc(x.text)}</span></label>
        <span class="because">Because of: ${esc(SHORT[x.because] || x.because)}</span>
        <span class="owner">${esc(x.owner)} · ${esc(x.due)}</span><span class="src">${esc(x.source)}</span></li>`;
    }).join("");
    const law = a.type === "heat" ? `<h3>Required by law, whatever the forecast</h3><ul class="lawlist">${H.legalItems(dayFor(a.zone), D.mode === "replay").map(i => `<li>${esc(i.t)}<span class="src">${esc(i.s)}</span></li>`).join("")}</ul>` : "";
    return `<article class="card lv-${a.level.toLowerCase()}">
      <header><span class="chip ${a.level.toLowerCase()}">${esc(a.level)}</span><h3>${esc(a.zoneName)}: ${esc(a.title)}</h3>
      <p class="small">${esc(ctx.fmtDate(a.date))} · ${D.mode === "replay" ? `replay with that day's observed weather (a back-test, not a forecast). In live use the alert is issued at 18:00 the evening before, about ${a.leadHours} hours before a 06:00 shift` : `forecast issued 18:00 the evening before, about ${a.leadHours} hours before a 06:00 shift`}</p><p>${esc(a.summary)}</p></header>
      <h3>Why this alert</h3>${groups}
      <h3>Who follows up</h3>
      <p class="holder ${h.escalated ? "esc" : ""}">${h.escalated ? `Not acknowledged in time: now with <strong>${esc(h.role)}</strong>.` : `Now with <strong>${esc(h.role)}</strong>.`}</p>
      <ol class="chain">${chain}</ol><p class="small">Closes when: ${esc(a.closeWhen)}</p>
      <div class="sts" role="group" aria-label="Status">${btn("acknowledged", "Acknowledge")}${btn("done", "Actions done", !allTicked)}${btn("closed", "Close", !allTicked)}${st !== "open" ? btn("open", "Reopen") : ""}</div>
      <p class="small">${allTicked ? "Closing is the owner's own confirmation that the closing condition is met; this demo cannot check it." : "Tick every action in the prevention plan to mark actions done or close."}</p>
      <h3>Prevention plan</h3><ol class="plan">${acts}</ol>
      ${law}
      ${a.type === "heat" ? `<p><a href="#plan" data-open="${esc(a.zone)}">Open a site supervisor's plan for ${esc(a.zoneName)} →</a></p>` : ""}
    </article>`;
  }

  // Which control had focus, so it can get focus back after its part of the page is rebuilt.
  function focusKey() {
    const a = document.activeElement;
    if (!a || !el.contains(a)) return null;
    for (const k of ["z", "a", "st", "clock", "mode", "done"]) if (a.dataset && a.dataset[k] !== undefined) return `[data-${k}="${CSS.escape(a.dataset[k])}"]`;
    return a.id ? "#" + CSS.escape(a.id) : null;
  }

  function update(keepTime) {
    if (!el) return;
    const fk = focusKey();
    const list = alertsNow().filter(a => !D.zone || a.zone === D.zone);
    if (D.alertId && !list.some(a => a.id === D.alertId)) D.alertId = null;
    if (!D.alertId && list.length && root.matchMedia && root.matchMedia("(min-width: 900px)").matches) D.alertId = list[0].id;
    el.querySelectorAll("[data-mode]").forEach(b => b.setAttribute("aria-pressed", String(b.dataset.mode === D.mode)));
    el.querySelectorAll("[data-clock]").forEach(b => b.setAttribute("aria-pressed", String(b.dataset.clock === D.clock)));
    el.querySelector("#d-banner").innerHTML = banner();
    updateMap();
    if (!keepTime) el.querySelector("#d-time").innerHTML = timeline();
    else {   // dragging the slider: keep the input element, move only the cursor and the label
      const i = seasonDays().indexOf(D.date), r = el.querySelector("#d-range");
      if (Number(r.value) !== i) r.value = String(i);
      el.querySelector("#d-cursor").setAttribute("x", String(i - 0.5));
      el.querySelector("#d-out").textContent = ctx.fmtDate(D.date);
      r.setAttribute("aria-valuetext", ctx.fmtDate(D.date));
    }
    el.querySelector("#d-board").innerHTML = board(list);
    el.querySelector("#d-feedh").textContent = `Alerts${D.zone ? " for " + ctx.DATA.replay[D.zone].name : ""} (${list.length})`;
    el.querySelector("#d-feed").innerHTML = list.length ? list.map(feedItem).join("") : `<li class="small">None for this day.</li>`;
    el.querySelector("#d-detail").innerHTML = detail(list);
    if (fk) { const f = el.querySelector(fk); if (f && f !== document.activeElement) f.focus({ preventScroll: true }); }
  }

  function selectZone(k) { D.zone = k || null; D.alertId = null; update(); }
  function setIndex(i, keepTime) { const days = seasonDays(); D.date = days[Math.max(0, Math.min(days.length - 1, i))]; update(keepTime); }
  function stop() { if (timer) { clearInterval(timer); timer = null; } }

  function onClick(ev) {
    const t = ev.target.closest("button, a, rect, input");
    if (!t || !el.contains(t)) return;
    const ds = t.dataset;
    if (ds.mode) { stop(); D.mode = ds.mode; D.alertId = null; update(); }
    else if (ds.clock) { D.clock = ds.clock; update(); }
    else if (ds.z !== undefined) selectZone(ds.z);
    else if (ds.a) { D.alertId = ds.a; update(); if (!root.matchMedia("(min-width: 900px)").matches) el.querySelector("#d-detail").scrollIntoView({ block: "start" }); }
    else if (ds.st) { setStatus(D.alertId, ds.st); update(); el.querySelector("#d-say").textContent = `Status: ${STATUS_WORD[ds.st]}.`; }
    else if (ds.i !== undefined && D.mode === "replay") { stop(); setIndex(Number(ds.i)); }
    else if (ds.open) { ev.preventDefault(); ctx.openPlan(ds.open, D.mode === "replay" ? D.date : null); }
    else if (t.id === "d-play") {
      if (timer) { stop(); update(); return; }
      if (seasonDays().indexOf(D.date) >= seasonDays().length - 1) D.date = seasonDays()[0];
      timer = setInterval(() => { const i = seasonDays().indexOf(D.date) + 1; if (i >= seasonDays().length) { stop(); update(); } else setIndex(i, true); }, 450);
      update();
    }
  }
  function onSlide(ev) {
    if (ev.target.id !== "d-range") return;
    stop();
    const days = seasonDays();
    D.date = days[Math.max(0, Math.min(days.length - 1, Number(ev.target.value)))];
    update(true);
  }
  function onChange(ev) {
    if (ev.target.dataset.done) { toggleDone(ev.target.dataset.done); update(); }
  }

  function mount(target, context) {
    unmount();
    ctx = context; el = target;
    D.mode = liveInSeason() ? "live" : "replay";
    el.innerHTML = skeleton();
    el.addEventListener("click", onClick);
    el.addEventListener("input", onSlide);
    el.addEventListener("change", onChange);
    initMap();
    update();
  }
  function unmount() {
    stop();
    if (map) { map.remove(); map = null; markers = {}; }
    if (el) { el.removeEventListener("click", onClick); el.removeEventListener("input", onSlide); el.removeEventListener("change", onChange); }
    el = null;
  }

  root.Dash = { mount, unmount };
})(window);
