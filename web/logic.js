"use strict";
// Pure plan logic, shared by the browser (window.HeatLogic) and the node tests (module.exports).
(function (root) {
  const RAISE = { "No escalation": "Elevated", "Elevated": "High", "High": "High", "Insufficient data": "High" };
  const STALE_HOURS = 36;

  function answeredYes(v) { return v !== "no"; }

  // Signed S4: new or returning workers raise the tier one level (our heuristic, labelled in the UI).
  // Insufficient data is never shown as lower than Elevated.
  function effectiveTier(base, crew) {
    if (base === "Outside tested season") return { tier: base, raised: false };
    const floor = base === "Insufficient data" ? "Elevated" : base;
    if (!answeredYes(crew.newWorkers)) return { tier: floor, raised: false };
    const up = RAISE[floor] || floor;
    return { tier: up, raised: up !== floor };
  }

  function planSteps(tier, crew, inSeason, peakHour) {
    const steps = [];
    const hot = tier === "Elevated" || tier === "High";
    if (hot) steps.push({ text: "Check every crew member before the shift: symptoms, sleep, fluids.", owner: "Supervisor · before the shift starts" });
    if (tier === "High") steps.push({ text: "Get a site heat assessment from your OSH practitioner before heavy outdoor work starts.", owner: "OSH practitioner · before heavy work" });
    if (hot && answeredYes(crew.heavy)) {
      const when = peakHour == null ? "" : ` (heat peaks around ${peakHour}:00)`;
      steps.push({ text: `Move heavy tasks away from the hottest hours${when}.`, owner: "Supervisor · when setting the shift plan" });
    }
    if (answeredYes(crew.newWorkers)) {
      steps.push({ text: "New or returning workers: no more than 20% of the usual heat exposure on day 1, adding 20% a day.", owner: "Supervisor · NIOSH 2016 criteria document" });
      steps.push({ text: "No unacclimatised worker in medium or high risk heat work.", owner: "Supervisor · ADPHC Technical Guideline, Safety in the Heat" });
    }
    if (!steps.length) steps.push({ text: inSeason ? "No extra steps from the forecast." : "No forecast-based steps outside May to September.", owner: "" });
    return steps;
  }

  function isStale(generatedUtc, now, maxHours) {
    const t = Date.parse(String(generatedUtc).replace(" ", "T") + "Z");
    if (Number.isNaN(t)) return true;
    return (now.getTime() - t) / 3.6e6 > (maxHours || STALE_HOURS);
  }

  function dubaiDate(now, plusDays) {
    const d = new Date(now.getTime() + (plusDays || 0) * 864e5);
    return new Intl.DateTimeFormat("en-CA", { timeZone: "Asia/Dubai", year: "numeric", month: "2-digit", day: "2-digit" }).format(d);
  }

  function inTestedSeason(isoDate) {
    const m = Number(String(isoDate).slice(5, 7));
    return m >= 5 && m <= 9;
  }

  // Live forecast for one zone -> what the app may show. Out-of-season wins; stale or missing never shows old numbers.
  function resolveDay(day, generatedUtc, now) {
    const today = dubaiDate(now, 0), tomorrow = dubaiDate(now, 1);
    const stale = !day || !day.date || day.date < today || isStale(generatedUtc, now);
    if (stale) {
      const tier = inTestedSeason(tomorrow) ? "Insufficient data" : "Outside tested season";
      return { name: day && day.name, date: tomorrow, tier, stale: true, when: "Tomorrow" };
    }
    const tier = inTestedSeason(day.date) ? day.tier : "Outside tested season";
    return Object.assign({}, day, { tier, stale: false, when: day.date === today ? "Today" : "Tomorrow" });
  }

  function legalItems(day, isReplay) {
    const d = new Date(day.date + "T12:00:00Z"), md = (d.getUTCMonth() + 1) * 100 + d.getUTCDate();
    const t = day.max_temp_c;
    return [
      md >= 615 && md <= 915
        ? { t: "Midday break: no outdoor work in direct sun from 12:30 to 15:00.", s: "UAE Ministry of Human Resources and Emiratisation, 15 June to 15 September" }
        : { t: "The midday break is not in force on this date. It runs 15 June to 15 September.", s: "UAE Ministry of Human Resources and Emiratisation" },
      !Number.isFinite(t)
        ? { t: "Forecast temperature unavailable. Check readings on site, and assume the 35\u00a0°C heat stress programme applies.", s: "ADPHC OSH Code of Practice 11.0, section 3.1.1(e)" }
        : t >= 35
        ? { t: `${isReplay ? "Air temperature reached" : "Forecast air temperature reaches"} ${t} °C. At 35 °C or more, your site's heat stress programme applies.`, s: "ADPHC OSH Code of Practice 11.0, section 3.1.1(e)" }
        : { t: `${isReplay ? "Air temperature peaked at" : "Forecast air temperature peaks at"} ${t} °C, below the 35 °C programme trigger. Check readings on site.`, s: "ADPHC OSH Code of Practice 11.0, section 3.1.1(e)" },
      { t: "Abu Dhabi's heat stress index (Thermal Work Limit) needs on-site readings. This app does not calculate it.", s: "ADPHC Technical Guideline, Safety in the Heat" },
    ];
  }

  const api = { answeredYes, effectiveTier, planSteps, isStale, legalItems, resolveDay, inTestedSeason, dubaiDate, STALE_HOURS };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else root.HeatLogic = api;
})(typeof window !== "undefined" ? window : globalThis);
