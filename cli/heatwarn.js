#!/usr/bin/env node
"use strict";
// heatwarn: the Heat Shift Planner in a terminal. It calls the app's own modules (web/logic.js, web/alerts.js,
// web/health.js, web/backtest.js) on the app's own data files, so it can never disagree with the risk map.
// No dependencies; Node 18 or later. Run `node cli/heatwarn.js help`.
const fs = require("node:fs");
const path = require("node:path");
const H = require("../web/logic.js");
const A = require("../web/alerts.js");
const HS = require("../web/health.js");
const BT = require("../web/backtest.js");

const SITE = "https://drahmed7887.github.io/hack-future-health/data/";
const FILES = { live: "live.json", replay: "replay.json", dust: "dust_replay.json", backtest: "backtest.json" };
const REPLAY_FROM = "2025-05-01", REPLAY_TO = "2025-09-30";
const PROMPT_FILE = path.join(__dirname, "..", "prompts", "supervisor_assistant.md");

const USAGE = `heatwarn: heat, dust and health alerts for outdoor work in Abu Dhabi (Heat Shift Planner)

  heatwarn zones    [--date YYYY-MM-DD] [--json]            every zone's level for tomorrow, or for a replay day
  heatwarn alerts   [--date YYYY-MM-DD] [--zone Z] [--json]  each alert with its reasons, owner, escalation and actions
  heatwarn backtest [--region h1..h6] [--year 2022..2025] [--day YYYY-MM-DD]
                                                            the US back-test against real OSHA case days
  heatwarn prompt   [--date YYYY-MM-DD] [--zone Z] [--question "..."]
                                                            a ready prompt for an AI assistant (pipe it to a model)
  heatwarn help

  --date   a summer 2025 replay day (${REPLAY_FROM} to ${REPLAY_TO}); without it, tomorrow's live forecast
  --remote read the data from the live site instead of this checkout's web/data/

Examples:
  heatwarn alerts --date 2025-06-26 --zone alain
  heatwarn prompt --date 2025-06-26 --zone alain --question "Can my crew pour concrete at noon?" | claude -p
  rwth-ask "Answer as the prompt says." < <(heatwarn prompt --zone mussafah)

Decision support for supervisors, not a medical device, never a clearance to work.
Suspected heat stroke: cool first and call 998 at the same time.`;

class UsageError extends Error {}

// ---------- data ----------
function loadLocal(dir) {
  const read = f => JSON.parse(fs.readFileSync(path.join(dir, f), "utf8"));
  const out = {};
  for (const [k, f] of Object.entries(FILES)) {
    try { out[k] = read(f); } catch (e) { if (k === "live" || k === "replay") throw new Error(`Cannot read ${path.join(dir, f)}: ${e.message}`); out[k] = null; }
  }
  return out;
}

// The live site's data files (fixed URL, no redirects, 20 s timeout, fetched in parallel). The code, the alert wording and the
// simulated health series still come from this checkout, so pull it to match the site.
async function loadRemote() {
  const get = async ([k, f]) => {
    const r = await fetch(SITE + f, { signal: AbortSignal.timeout(20000), redirect: "error" });
    if (!r.ok) { if (k === "live" || k === "replay") throw new Error(`${SITE + f}: HTTP ${r.status}`); return [k, null]; }
    return [k, await r.json()];
  };
  return Object.fromEntries(await Promise.all(Object.entries(FILES).map(get)));
}

// ---------- arguments ----------
const COMMANDS = new Set(["zones", "alerts", "backtest", "prompt", "help"]);
const VALUE = new Set(["--date", "--zone", "--region", "--year", "--day", "--question"]);

function checkDate(d, flag) {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(d) || Number.isNaN(Date.parse(d + "T00:00:00Z")) || new Date(d + "T00:00:00Z").toISOString().slice(0, 10) !== d) throw new UsageError(`${flag} must be a real date, YYYY-MM-DD (got "${d}")`);
  return d;
}

function parseArgs(argv) {
  const [first = "help", ...rest] = argv;
  const cmd = first === "--help" || first === "-h" ? "help" : first;
  if (!COMMANDS.has(cmd)) throw new UsageError(`Unknown command "${cmd}". Run: heatwarn help`);
  const o = { cmd };
  for (let i = 0; i < rest.length; i += 1) {
    const a = rest[i];
    if (a === "--json") { o.json = true; continue; }
    if (a === "--remote") { o.remote = true; continue; }
    if (!VALUE.has(a)) throw new UsageError(`Unknown option "${a}". Run: heatwarn help`);
    const v = rest[i + 1];
    if (v === undefined || v.startsWith("--")) throw new UsageError(`${a} needs a value`);
    o[a.slice(2)] = v; i += 1;
  }
  if (o.date) {
    checkDate(o.date, "--date");
    if (o.date < REPLAY_FROM || o.date > REPLAY_TO) throw new UsageError(`--date must be a replay day, ${REPLAY_FROM} to ${REPLAY_TO}; leave it out for tomorrow's forecast`);
  }
  if (o.day) checkDate(o.day, "--day");
  if (o.year !== undefined) { o.year = Number(o.year); if (!Number.isInteger(o.year) || o.year < 2022 || o.year > 2025) throw new UsageError("--year must be 2022, 2023, 2024 or 2025"); }
  return o;
}

function checkZone(data, zone) {
  if (zone && !Object.prototype.hasOwnProperty.call(data.replay, zone)) throw new UsageError(`Unknown zone "${zone}". Zones: ${Object.keys(data.replay).join(", ")}`);
  return zone;
}

// ---------- the same day and options as the risk map (web/dash.js dayFor / optsFor) ----------
function dayAndOpts(data, k, opts) {
  if (!opts.date) {
    const day = H.resolveDay(data.live.zones[k], data.live.generated_utc, opts.now || new Date());
    const pm = Number.isFinite(day.pm10_mean) ? day.pm10_mean : null;
    return { day, options: { dust: day.stale ? null : { pm10: pm, level: A.dustLevel(pm) } } };
  }
  const days = data.replay[k].days, i = days.findIndex(d => d.date === opts.date);
  const day = i >= 0 ? days[i] : null;
  if (!day) return { day: null, options: {} };
  const raw = data.dust && data.dust.zones && data.dust.zones[k] ? data.dust.zones[k][opts.date] : null;
  const pm = Number.isFinite(raw) ? raw : null;
  return { day, options: {
    prevTier: i > 0 ? days[i - 1].tier : null,
    firstHigh: !days.slice(0, i).some(d => d.tier === "High"),
    health: HS.healthDay(k, opts.date),
    dust: data.dust ? { pm10: pm, level: A.dustLevel(pm) } : null,
  } };
}

const zoneKeys = (data, zone) => Object.keys(data.replay).filter(k => !zone || k === zone);

function alertsFor(data, opts) {
  return A.sortAlerts(zoneKeys(data, opts.zone).flatMap(k => {
    const { day, options } = dayAndOpts(data, k, opts);
    return day ? A.buildAlerts(k, data.replay[k].name, day, options) : [];
  }));
}

function zoneRows(data, opts) {
  return zoneKeys(data, opts.zone).map(k => {
    const { day, options } = dayAndOpts(data, k, opts);
    return {
      zone: k, name: data.replay[k].name, date: day ? day.date : null, level: day ? day.tier : "Insufficient data",
      heat_index_c: day && !day.stale && Number.isFinite(day.heat_index_c) ? day.heat_index_c : null,
      percentile: day && !day.stale && Number.isFinite(day.percentile) ? day.percentile : null,
      pm10: options.dust && Number.isFinite(options.dust.pm10) ? Math.round(options.dust.pm10) : null,
      health_flag: options.health ? options.health.flag : null,
    };
  });
}

// ---------- text output ----------
const hhmm = min => `${String(Math.floor(((min % 1440) + 1440) % 1440 / 60)).padStart(2, "0")}:${String(((min % 60) + 60) % 60).padStart(2, "0")}`;
const WORD = { "Insufficient data": "No data", "No escalation": "No extra steps", "Outside tested season": "Off season" };   // as on the map
const word = t => WORD[t] || t;
// Text from data files never carries terminal control codes or closes the prompt's tags.
const clean = s => String(s).replace(/[\u0000-\u0008\u000b-\u001f\u007f-\u009f]/g, "");
const TAG = { tested: "tested on US outcomes", guideline: "from guidelines, not tested", rule: "app rule", simulated: "simulated" };

function formatAlert(a) {
  const lines = [`${a.level.toUpperCase()}${a.onset ? " (NEW)" : ""}  ${clean(a.zoneName)}: ${a.title}  [${a.date}]`, `  ${a.summary}`, "  Why:"];
  for (const d of a.drivers.filter(x => x.met)) {
    const tags = [TAG[d.basis] || d.basis, d.simulated && d.basis !== "simulated" ? "simulated" : null, d.role === "context" ? "context" : null].filter(Boolean);
    lines.push(`   - ${d.label}  ${tags.map(t => `[${t}]`).join(" ")}`);
  }
  lines.push(`  Owner: ${a.owner.role}. ${a.owner.due}.`);
  if (a.chain && a.chain.length) lines.push(`  Escalates if not acknowledged: ${a.chain.map(c => `${c.role} at ${hhmm(c.at)}`).join(", then ")}.`);
  if (a.closeWhen) lines.push(`  Closes when: ${a.closeWhen}`);
  if (a.actions && a.actions.length) {
    lines.push("  Actions:");
    for (const x of a.actions) lines.push(`   - ${x.text} (${x.owner}, ${x.due}. Source: ${x.source})`);
  }
  return lines.join("\n");
}

function zonesText(rows, opts, data) {
  const head = opts.date ? `Replay ${opts.date}: real weather (ERA5), real modelled dust (CAMS), simulated health visits.` : `Tomorrow's forecast, issued ${data.live.generated_utc} UTC.`;
  const body = rows.map(r => [
    clean(r.name).padEnd(18), word(r.level).padEnd(16),
    r.heat_index_c == null ? "heat index -" : `heat index ${r.heat_index_c} °C`,
    r.percentile == null ? "" : `, hotter than ${r.percentile}% of days here`,
    r.pm10 == null ? "" : `, PM10 ${r.pm10} µg/m³${r.pm10 > 150 ? " (above the UAE standard)" : ""}`,
    r.health_flag ? ", heat-illness visits above baseline (simulated)" : "",
  ].join("")).join("\n");
  return `${head}\n${body}\nHeat levels run May to September only. Not validated on Abu Dhabi outcomes.`;
}

function backtestText(data, opts) {
  if (!data.backtest) throw new Error("backtest.json is missing");
  const b = data.backtest, regs = Object.keys(b.regions);
  if (opts.region && !regs.includes(opts.region)) throw new UsageError(`Unknown region "${opts.region}". Regions: ${regs.map(k => `${k} (${b.regions[k].name})`).join(", ")}`);
  const pc = (x, n) => (n ? Math.round(100 * x / n) + "%" : "-");
  const line = (label, s) => `${label.padEnd(30)} ${String(s.caught).padStart(3)} of ${String(s.events).padEnd(3)} case days alerted   alerts on ${pc(s.alertDays, s.days).padStart(4)} of days   fixed 80 °F trigger ${pc(s.fixedAlertDays, s.days).padStart(4)}`;
  const out = [b.source + ".", ""];
  const show = opts.region ? [opts.region] : regs;
  for (const k of show) out.push(line(b.regions[k].name + (opts.year ? ` ${opts.year}` : ""), BT.summary(b, k, opts.year)));
  if (!opts.region) out.push(line("All 6 regions" + (opts.year ? ` ${opts.year}` : ""), BT.summary(b, null, opts.year)));
  if (opts.day) {
    const r = opts.region || regs[0], d = BT.day(b, r, opts.day);
    out.push("", d ? `${b.regions[r].name}, ${d.date}: ${d.level}. ${BT.why(d)} ${d.reports ? `${d.reports} reported work heat hospitalisation(s).` : "No hospitalisation reported."}` : `No back-test day ${opts.day} for ${b.regions[r].name} (May to September 2022-2025 only).`);
  }
  return out.join("\n");
}

// ---------- prompt for an AI assistant ----------
function compactAlert(a) {
  return {
    zone: a.zoneName, level: a.level, new_today: Boolean(a.onset), title: a.title, summary: a.summary,
    why: a.drivers.filter(d => d.met).map(d => `${d.label} [${TAG[d.basis] || d.basis}${d.simulated && d.basis !== "simulated" ? ", simulated" : ""}]`),
    owner: `${a.owner.role}: ${a.owner.due}`,
    escalation: (a.chain || []).map(c => `${c.role} at ${hhmm(c.at)}`),
    actions: (a.actions || []).map(x => ({ text: x.text, owner: x.owner, due: x.due, source: x.source })),
  };
}

function buildPrompt(data, opts) {
  let rules;
  try { rules = fs.readFileSync(PROMPT_FILE, "utf8").trim(); } catch (e) { throw new Error(`Cannot read the prompt rules at ${PROMPT_FILE}`); }
  const rows = zoneRows(data, opts);
  const payload = {
    date: opts.date || (rows[0] && rows[0].date),
    mode: opts.date ? "replay of a real summer 2025 day: answer as if this is the day the user asks about" : `tomorrow's forecast, issued ${data.live.generated_utc} UTC`,
    zones: rows, alerts: alertsFor(data, opts).map(compactAlert),
    emergency_card: H.EMERGENCY_STEPS, emergency_sources: H.EMERGENCY_SOURCES,
    limits: ["Heat rule tested on US OSHA data, not validated on Abu Dhabi outcomes", "Heat levels run May to September only",
      "Sites, crews, acknowledgements, cooling stations, incident notices and heat-illness visits are simulated for the demo",
      "Dust is modelled (CAMS), not measured; dust and health thresholds are signed by a physician but not tested on outcomes"],
  };
  const question = clean(opts.question || "Give me today's briefing for my site: what to do, who does it, and by when.").replace(/</g, "\u2039");
  return `${rules}\n\n<data>${JSON.stringify(payload).replace(/</g, "\\u003c")}</data>\n\n<question>${question}</question>\n`;
}

// ---------- main ----------
async function main(argv) {
  const o = parseArgs(argv);
  if (o.cmd === "help") { process.stdout.write(USAGE + "\n"); return 0; }
  const data = o.remote ? await loadRemote() : loadLocal(path.join(__dirname, "..", "web", "data"));
  checkZone(data, o.zone);
  let out;
  if (o.cmd === "zones") { const rows = zoneRows(data, o); out = o.json ? JSON.stringify(rows, null, 1) : zonesText(rows, o, data); }
  if (o.cmd === "alerts") {
    const list = alertsFor(data, o);
    out = o.json ? JSON.stringify(list, null, 1) : (list.length ? list.map(formatAlert).join("\n\n") : "No alerts for this day. The always-on basics still apply: water, shade, rest, and cool first if anyone is confused or collapses.");
  }
  if (o.cmd === "backtest") out = backtestText(data, o);
  if (o.cmd === "prompt") out = buildPrompt(data, o);
  process.stdout.write(out + "\n");
  return 0;
}

if (require.main === module) {
  process.stdout.on("error", e => { if (e.code === "EPIPE") process.exit(0); throw e; });   // heatwarn ... | head
  main(process.argv.slice(2)).then(code => { process.exitCode = code; }, e => {
    process.stderr.write(`heatwarn: ${e.message}\n`);
    process.exitCode = e instanceof UsageError ? 2 : 1;
  });
}

module.exports = { loadLocal, loadRemote, parseArgs, checkZone, alertsFor, zoneRows, formatAlert, zonesText, backtestText, buildPrompt, UsageError };
