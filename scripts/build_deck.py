"""Fill the official Future Health submission template (16 slides) with content from README and the business plan.
usage: python build_deck.py <template.pptx> <out.pptx> <path_to_pilot.png unused> ; numbers read from results/*.json.
Keeps every template slide and its prompt text; adds native text, tables and one chart in the empty body area."""
from __future__ import annotations

import json
import sys
from pathlib import Path

from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import XL_CHART_TYPE, XL_LABEL_POSITION, XL_LEGEND_POSITION
from pptx.enum.text import MSO_ANCHOR
from pptx.util import Inches, Pt

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE, OUT = sys.argv[1], sys.argv[2]
INK, MUTED, BLUE, RED, TINT, WHITE = (RGBColor.from_string(c) for c in ("1C2321", "4E5A57", "1D4E89", "B3261E", "EEF0EE", "FFFFFF"))
FONT = "Arial"
X0, Y0, W, H = 0.4, 1.5, 9.2, 3.95          # body area under each template prompt (inches)

ho = json.loads((ROOT / "results" / "holdout_results.json").read_text())
mv = json.loads((ROOT / "results" / "model_v4_results.json").read_text())
ev = json.loads((ROOT / "web" / "data" / "evidence.json").read_text())
DA = json.loads((ROOT / "results" / "dayahead_r4_results.json").read_text())
R4 = ho["rules"]["R4"]
SENS, CI, SHARE = R4["sensitivity"], R4["sensitivity_95ci"], R4["alert_fraction"]
EVENT_DAYS, REPORTS = ho["data"]["event_days"], ho["data"]["heat_reports"]
PER = {n: v["R4"] for n, v in ho["per_region"].items()}
CAUGHT = sum(v["caught"] for v in PER.values())
assert CAUGHT == round(SENS * EVENT_DAYS), "per-region caught must add up to the headline"
pc = lambda x, d=1: f"{x * 100:.{d}f} %"   # noqa: E731


def text(slide, x, y, w, h, paras, anchor=MSO_ANCHOR.TOP, fill=None, margin=0.05):
    """paras: list of (text, size, bold, color) or list of runs [(text, size, bold, color), ...]."""
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box.text_frame
    tf.word_wrap, tf.vertical_anchor = True, anchor
    for side in ("left", "right", "top", "bottom"):
        setattr(tf, f"margin_{side}", Inches(margin))
    if fill is not None:
        box.fill.solid(); box.fill.fore_color.rgb = fill
    for i, p in enumerate(paras):
        para = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        para.space_after = Pt(4)
        runs = p if isinstance(p, list) else [p]
        for t, size, bold, color in runs:
            r = para.add_run(); r.text = t
            r.font.size, r.font.bold, r.font.name, r.font.color.rgb = Pt(size), bold, FONT, color
    return box


def table(slide, x, y, w, rows, widths, size=9, head_fill=INK):
    shp = slide.shapes.add_table(len(rows), len(rows[0]), Inches(x), Inches(y), Inches(w), Inches(0.25 * len(rows)))
    tbl = shp.table
    for j, cw in enumerate(widths):
        tbl.columns[j].width = Inches(cw)
    for i, row in enumerate(rows):
        for j, val in enumerate(row):
            cell = tbl.cell(i, j)
            cell.margin_left = cell.margin_right = Inches(0.05)
            cell.margin_top = cell.margin_bottom = Inches(0.03)
            cell.fill.solid(); cell.fill.fore_color.rgb = head_fill if i == 0 else (WHITE if i % 2 else TINT)
            tf = cell.text_frame; tf.word_wrap = True
            r = tf.paragraphs[0].add_run(); r.text = val
            r.font.size, r.font.name = Pt(size), FONT
            r.font.bold = i == 0
            r.font.color.rgb = WHITE if i == 0 else INK
    return shp


def card(slide, x, y, w, h, head, body, color=INK, size=10):
    text(slide, x, y, w, h, [(head, size + 2, True, color)] + [(b, size, False, INK) for b in body], fill=TINT, margin=0.1)


p = Presentation(TEMPLATE)
S = list(p.slides)

# 1 Team name, size, problem
tb = next(sh for sh in S[0].shapes if sh.has_text_frame)
vals = ["Heat Shift Planner (working name), Ahmed Zayed", "1 (solo)",
        "[Population Health] Population and Workforce Health Early Warning. Abu Dhabi has heat rules, weather warnings "
        "and an awareness programme, but no free tool ranks tomorrow's forecast against that zone's own climate and "
        "turns it, with the crew, into a pre-shift plan the evening before."]
for para, v in zip(tb.text_frame.paragraphs, vals):
    ref = para.runs[0].font
    r = para.add_run(); r.text = v
    r.font.size, r.font.name = Pt(13 if len(v) > 60 else ref.size.pt if ref.size else 18), ref.name

# 2 Team members: one member; Ahmed confirms country and age before export
tblshape = next(sh for sh in S[1].shapes if sh.has_table)
t = tblshape.table
for j, v in enumerate(["", "Ahmed Zayed", "Spain (resident)", "Solo: clinical lead, data analysis, build",
                       "Independent; M.Sc. student, RWTH Aachen", "Confirmed: over 18"]):
    if not v:
        continue
    cell = t.cell(1, j)
    para = cell.text_frame.paragraphs[0]
    r = para.add_run(); r.text = v; r.font.size = Pt(9); r.font.name = FONT
for tr in list(t._tbl.tr_lst)[2:]:
    t._tbl.remove(tr)

# 3 Capability (<= 1,000 characters)
CAP = ("Ahmed Zayed, MB BCh (Alexandria University, 2010), is a physician with more than 12 years of clinical practice, "
       "including airport general practice in Sharm El Sheikh, now working as a clinical-AI specialist. He is studying "
       "for an M.Sc. in Applied Health Informatics and Digital Medicine at RWTH Aachen (2026 to 2028). He built "
       "SAFE-Triage, an emergency triage safety check (35 of 36 correct, no critical under-triage, on the MIETIC English "
       "set). For this entry he did everything himself: the clinical criteria and their sign-off, a pre-registered "
       "back-test on 2,628 US work heat hospitalisations (scored on 86 case days in 6 regions never used in tuning), the web app, and the emergency first-aid wording. His method: "
       "evidence first (every rule has a source), tests written before code (42 automated tests), and independent model "
       "reviews at each stage.")
assert len(CAP) <= 1000, len(CAP)
text(S[2], X0, Y0 + 0.1, W, 3.0, [(CAP, 13, False, INK)])
text(S[2], X0, 4.9, W, 0.4, [(f"{len(CAP)} of 1,000 characters", 9, False, MUTED)])

# 4 Architecture
IMG_H = 3.25
S[3].shapes.add_picture(str(ROOT / "docs" / "workflow.png"), Inches(X0), Inches(Y0), height=Inches(IMG_H))
nx = X0 + IMG_H * 16 / 9 + 0.15
text(S[3], X0, Y0 + IMG_H + 0.05, nx - X0 - 0.1, 0.7, [[("The rule: ", 8.5, True, INK), ("alert if the day's peak heat index is at least 80 °F and it is above the zone's 60th percentile for the date (High), or above the 50th and at least 3 °F above the previous 14 days (Elevated). Percentiles from each zone's own 2015–2021 May–September days. Crew: new or returning workers raise the tier one level and add acclimatisation steps; heavy work moves heavy tasks off the peak hours.", 8.5, False, INK)]])
text(S[3], nx, Y0, 9.6 - nx, H, [
    ("Also on every screen", 11, True, RED),
    ("A red emergency card: suspected heat stroke, cool first and call 998 at the same time (wording signed by the physician).", 9, False, INK),
    ("Stack", 11, True, INK),
    ("Prototype: static web app (HTML, JavaScript); GitHub Actions fetches the forecast daily; GitHub Pages hosts it. No server, no accounts, no personal data. Python back-test (pandas; scikit-learn for the offline model benchmark only).", 9, False, INK),
    ("Pilot adds", 11, True, INK),
    ("A small UAE-hosted store for plan acknowledgements (site, zone, date, tier; no worker data). The regulator and HSE views use simulated data until then.", 9, False, INK),
    ("Deterministic", 11, True, INK),
    ("Thresholds are versioned code, frozen before scoring. No language model sets a score or a threshold.", 9, False, INK),
])

# 5 Target users and outcome
cw, gap = 2.15, 0.2
users = [
    ("Site supervisor (main user)", ["Gets tomorrow's plan the evening before: which tasks to move, which workers need a lighter day, who owns each step."]),
    ("Worker", ["Protected on unusually dangerous days and on the first days on the job. No personal data collected."]),
    ("Employer HSE manager", ["A daily record that the heat programme was applied, as ADPHC Code of Practice 11.0 already requires (pilot feature)."]),
    ("Regulator (ADPHC)", ["Sees risk and acknowledged plans by zone, never people, so inspections go where they matter (simulated in the demo)."]),
]
for i, (hd, body) in enumerate(users):
    card(S[4], X0 + i * (cw + gap), Y0, cw, 1.6, hd, body, color=BLUE if i == 0 else INK)
text(S[4], X0, Y0 + 1.85, W, 1.5, [
    ("Intended outcome", 12, True, INK),
    ("Fewer serious heat illnesses at work, by acting the evening before on the days that are unusual for each zone, protecting new and returning workers, and cooling on site at once if someone collapses. Proven so far: the alert rule on US outcomes (back-test). Not yet proven: any effect in Abu Dhabi; that is what the pilot measures.", 10, False, INK),
])

# 6 Success measures
text(S[5], X0, Y0, W, 0.3, [("Measured on the prototype (US data, back-test)", 11, True, INK)])
table(S[5], X0, Y0 + 0.3, W, [
    ["Measure", "Result", "Why it matters"],
    [f"Case days with an alert, 6 unseen US regions, 2022–2025 ({EVENT_DAYS} days)", f"{pc(SENS)} (95 % CI {pc(CI[0])}–{pc(CI[1])})", "Sensitivity on real outcomes"],
    ["Share of days alerted (the common fixed trigger: 82 %)", f"{pc(SHARE, 0)}", "Fewer alerts for the same protection"],
    ["Spread of alert load across regions", f"{round(ho['primary_B_alert_share_spread']['R4'] * 100)} points (fixed thresholds: {round(ho['primary_B_alert_share_spread']['R2'] * 100)})", "Does it transfer to a new climate?"],
    ["Case days caught using the evening-before forecast (8 tuning regions, 2024–25: the archived forecasts start in 2024)", f"{pc(DA['day_ahead']['sensitivity'])} (actual weather: {pc(DA['observed']['sensitivity'])})", "Works as a forecast, not only in hindsight"],
    ["Same decision from the evening-before forecast as from actual weather (same regions and years)", f"{pc(ev['dayahead_same_decision'], 0)}", "Forecast error changes few decisions"],
], [4.6, 2.0, 2.6], size=9)
text(S[5], X0, Y0 + 2.1, W, 0.3, [("Proposed for the Abu Dhabi pilot (to agree with ADPHC before the season; targets are not results)", 11, True, INK)])
table(S[5], X0, Y0 + 2.4, W, [
    ["Measure", "Proposed target"],
    ["Share of days with an alert, per zone", "30–60 % in every zone"],
    ["Heat cases on alert days / all cases, all Abu Dhabi zones (zone-day incident or ED counts; sites alone are too few)", "Not worse than 79 %, with a 95 % CI"],
    ["Plans acknowledged before the shift / cooling station ready on alert days", "≥ 80 % of site-evenings / baseline in 2027"],
    ["Heat cases per 1,000 workers, pilot sites vs others", "Measured, not promised (one season is too short)"],
], [5.6, 3.6], size=9)

# 7 Evidence
cd = CategoryChartData()
names = {"Mcallen, Texas": "McAllen TX", "Fort Lauderdale, Florida": "Ft Lauderdale FL", "Philadelphia, Pennsylvania": "Philadelphia PA",
         "Kennesaw, Georgia": "Kennesaw GA", "Braddock, Pennsylvania": "Braddock PA", "New Orleans, Louisiana": "New Orleans LA"}
order = sorted(PER, key=lambda n: -PER[n]["event_days"])
cd.categories = [names.get(n, n) for n in order]
cd.add_series("Case days", [PER[n]["event_days"] for n in order])
cd.add_series("Caught (alert that day)", [PER[n]["caught"] for n in order])
ch = S[6].shapes.add_chart(XL_CHART_TYPE.BAR_CLUSTERED, Inches(X0), Inches(Y0 + 0.5), Inches(4.3), Inches(3.4), cd).chart
ch.has_title = False
ch.plots[0].has_data_labels = True
ch.plots[0].data_labels.font.size, ch.plots[0].data_labels.font.name = Pt(8), FONT
ch.plots[0].data_labels.position = XL_LABEL_POSITION.OUTSIDE_END
ch.series[0].format.fill.solid(); ch.series[0].format.fill.fore_color.rgb = RGBColor.from_string("BFC5C3")
ch.series[1].format.fill.solid(); ch.series[1].format.fill.fore_color.rgb = INK
ch.has_legend = True; ch.legend.position = XL_LEGEND_POSITION.BOTTOM; ch.legend.include_in_layout = False; ch.legend.font.size = Pt(8); ch.legend.font.name = FONT
ch.category_axis.tick_labels.font.size = Pt(8); ch.category_axis.tick_labels.font.name = FONT
ch.category_axis.reverse_order = True
ch.value_axis.visible = False; ch.value_axis.has_major_gridlines = False
text(S[6], X0, Y0, 4.3, 0.3, [(f"Back-test: {CAUGHT} of {EVENT_DAYS} real case days caught ({pc(SENS)}), regions never used in tuning", 10, True, INK)])
text(S[6], X0 + 4.5, Y0, W - 4.5, H, [
    ("Why relative thresholds", 10, True, BLUE),
    ("Heat-health risk depends on what is usual locally (Anderson & Bell 2009, PMID 19194300; Gasparrini 2015, PMID 26003380). A US-tuned fixed threshold would put every Abu Dhabi day June–September in its top tier.", 9, False, INK),
    ("Why the crew matters", 10, True, BLUE),
    ("In US enforcement cases, 9 of 13 heat deaths were in a worker's first 3 days (Arbury, MMWR 2014, PMID 25102413).", 9, False, INK),
    ("Why it can work in Abu Dhabi", 10, True, BLUE),
    ("Abu Dhabi's heat programme cut cases at one company from 15.3 to 1.16 per 1,000 workers (Joubert, AJPH 2011, PMID 21307373).", 9, False, INK),
    ("Prior testing, all pre-registered", 10, True, BLUE),
    (f"Tuned on 2015–2021, frozen, scored once. {REPORTS:,} reports matched to each day's actual weather; {EVENT_DAYS} case days in the unseen regions. Two ideas failed and are reported: incident reports as a trigger (−11.6 points) and a trained model (slide 15). No US test region is hyper-arid like Al Ain or Al Dhafra: local recalibration is part of the pilot.", 9, False, INK),
])

# 8 Data sources and rights
table(S[7], X0, Y0, W, [
    ["Source", "Type", "Owner", "Sensitivity", "Permission", "Personal data?"],
    ["OSHA Severe Injury Reports, Jan 2015–Nov 2025", "Work injury records (back-test outcomes)", "US Dept of Labor, OSHA", "Public; has employer names and narratives (not shown or published by the app)", "US government public data", "No worker names; app shows region totals only"],
    ["Open-Meteo Historical Weather (ERA5)", "Weather reanalysis", "Open-Meteo; Copernicus C3S", "Public", "CC BY 4.0, attributed", "No"],
    ["Open-Meteo Forecast and Previous Runs APIs", "Weather forecasts", "Open-Meteo", "Public", "CC BY 4.0 data; API terms for pilot use to check (or use NCM data)", "No"],
    ["ADPHC CoP 11.0 and TG Safety in the Heat v4.0; MoHRE midday break; NIOSH 2016", "Guidance, quoted with citation", "ADPHC; MoHRE; CDC/NIOSH", "Public", "Quoted with source", "No"],
    ["Crew answers in the app", "Yes / no / not sure", "Supervisor; stays on the device", "Low", "Entered by the user", "No: no names or health data"],
    ["Sites, acknowledgements, notices, cooling stations", "Demo data", "Author", "Simulated, labelled", "—", "No"],
], [2.2, 1.45, 1.35, 1.75, 1.15, 1.3], size=8)

# 9 Risks and safeguards
table(S[8], X0, Y0, W, [
    ["Risk", "Safeguard"],
    ["Privacy", "No worker names, health data or job histories collected. Regulator view by zone; counts hidden below 5 sites."],
    ["Security", "Prototype: static site, no server, accounts or database. Pilot: a small UAE-hosted, access-controlled store for plan acknowledgements only (site, zone, date, tier; no worker data)."],
    ["Bias", "Outcomes are US reported cases (under-reported). Transfer tested in 6 unseen regions; not validated in Abu Dhabi, so the pilot runs in shadow mode first."],
    ["Explainability", "Each tier shows why (how unusual the day is locally, change over 14 days). Each step shows an owner and a source."],
    ["Misuse", "Written ban on employment or disciplinary use. Never a clearance to work. Incident notices never raise a tier."],
    ["Human oversight", "The supervisor decides and acknowledges. The legal layer is shown whatever the rule says. Crew rules are labelled untested."],
    ["Failure modes", "Missing or stale forecast: 'Not enough data', treated as Elevated. Out of season: says so. Heat index used only to rank days (NWS validity limits). Thermal Work Limit not computed."],
    ["Clinical safety", "Emergency card: call 998 and cool at once, follow the call-taker. Wording signed by the physician; alignment with UAE ambulance protocols is a pilot item."],
], [1.6, 7.6], size=9)

# 10 Hardware
text(S[9], X0, Y0, W, 1.0, [("Not applicable. Software only: no wearable, sensor or device. Runs in any phone or laptop browser.", 13, False, INK)])

# 11 Access
text(S[10], X0, Y0, W, 1.3, [
    [("No login needed. Every feature is open to guests:  ", 12, True, INK), ("https://drahmed7887.github.io/hack-future-health/", 12, True, BLUE)],
    ("Pick a zone, see tomorrow's tier and the legal layer, answer two crew questions, get the plan, open the red emergency card. Also: Replay a day (real summer 2025 weather), Regulator view, Evidence.", 10, False, INK),
    ("Alerts are tested for May to September only. Outside the season, use Replay a day to see alerts at work (screens below: Mussafah, 1 Aug 2025).", 10, False, MUTED),
])

STILLS = Path(sys.argv[3]) if len(sys.argv) > 3 else None
if STILLS:
    from PIL import Image
    shots = [("S1_home.png", "Tomorrow at a glance"), ("v2_S8c_plan_new.png", "The crew plan"), ("v4_S9c_help.png", "Emergency card")]
    for i, (f, cap) in enumerate(shots):
        jpg = Path(OUT).with_name(f"shot_{i}.jpg")
        Image.open(STILLS / f).convert("RGB").resize((540, 960)).save(jpg, quality=80)
        x = X0 + i * 1.75
        pic = S[10].shapes.add_picture(str(jpg), Inches(x), Inches(2.85), height=Inches(2.35))
        pic.line.color.rgb = INK; pic.line.width = Pt(0.75)
        text(S[10], x, 5.2, 1.4, 0.3, [(cap, 8, False, MUTED)])

# 12 Path to pilot and scale
stages = [("0 Prototype", "Done, Nov 2026", "Live app; US back-test; pre-registered protocols"),
          ("1 Pilot agreement", "Dec 2026–Apr 2027", "ADPHC + 3–5 volunteer sites; outcome definition fixed in advance; plans in Arabic, Urdu, Hindi, Bengali, Tagalog"),
          ("2 Shadow mode", "May–Sep 2027", "Runs every evening; nothing enforced; log alerts, steps, cases, site TWL"),
          ("3 Recalibrate", "Oct–Dec 2027", "First score on Abu Dhabi outcomes across all zones; ADPHC decides: scale or stop"),
          ("4 Scale", "2028 onwards", "Free for all employers via Safety in Heat; other emirates and Gulf states")]
sw = (W - 4 * 0.12) / 5
for i, (a, b, c) in enumerate(stages):
    text(S[11], X0 + i * (sw + 0.12), Y0, sw, 1.6, [(a, 11, True, WHITE if i == 0 else INK), (b, 9, True, WHITE if i == 0 else BLUE), (c, 9, False, WHITE if i == 0 else INK)],
         fill=INK if i == 0 else TINT, margin=0.08)
cols = [("Stakeholders", "ADPHC (target pilot partner, no agreement yet); employer HSE teams; site supervisors; National Ambulance / SEHA for the emergency card."),
        ("Integration", "Web app, no install, plus a small store for acknowledgements. Outcomes by zone and day: ADOSH-SF Mechanism 11.0 notifications or ED heat-illness visits (ICD-10 T67). Sites give process measures."),
        ("Regulatory", "ADOSH-SF CoP 11.0 and MoHRE midday break shown as is. Ethics review if outcome data are used. Decision support, not a medical device."),
        ("Sustainability", "Runs on free hosting today. Regulator-led free tier; paid integrations for large employers later. Thresholds per zone, so it transfers.")]
cw2 = (W - 3 * 0.15) / 4
for i, (hd, body) in enumerate(cols):
    text(S[11], X0 + i * (cw2 + 0.15), Y0 + 1.75, cw2, 2.1, [(hd, 10, True, BLUE), (body, 9, False, INK)])

# 13 IP and third-party materials
table(S[12], X0, Y0, W, [
    ["Item", "Ownership or licence", "Restrictions"],
    ["App code, back-test code, protocols, documents, film script", "Ahmed Zayed (solo author); no open-source licence yet (all rights reserved)", "Code shared with organisers for evaluation (repo public at submission)"],
    ["Python libraries: numpy, pandas, scikit-learn", "BSD-3-Clause", "None"],
    ["Weather data: Open-Meteo (incl. ERA5, Copernicus)", "CC BY 4.0", "Attribution (shown in the app footer)"],
    ["OSHA Severe Injury Reports", "US government public data", "Raw file not redistributed; SHA-256 recorded"],
    ["Fonts: Atkinson Hyperlegible, Barlow Condensed", "SIL Open Font License", "None"],
    ["Film narration and music bed", "Generated with ElevenLabs (author's Student plan); disclosed on screen", "Synthetic voice labelled"],
    ["AI assistance", "Claude Code (coding, drafting); GPT-6, Gemini and Qwen as independent reviewers", "All numbers come from the author's scripts; clinical wording signed by the author"],
], [2.9, 3.6, 2.7], size=8)
text(S[12], X0, 5.05, W, 0.35, [("The organiser's terms give a 6-month right of first refusal; the author accepts it as stated in the challenge terms.", 8, False, MUTED)])

# 14 Conflict of interest
text(S[13], X0, Y0, W, H, [
    ("None. No member of our team has a conflict of interest to declare.", 14, True, INK),
    ("Solo entrant. Not employed by or contracted to the Department of Health – Abu Dhabi, Future Health, Microsoft, Inception42, MBZUAI or Hack2skill. No family or close personal relationship with a judge, organiser or collaborator. No financial interest in an organisation running or judging the challenge. No access to non-public information about the challenge or its evaluation.", 11, False, INK),
])

# 15 Additional: medical edge + the model we did not deploy
P = mv["holdout"]
prompt = next(sh for sh in S[14].shapes if sh.has_text_frame and "Additional" in sh.text_frame.text)
prompt.top = Inches(0.94)   # the template puts this prompt at the bottom; align it with the other slides
card(S[14], X0, Y0, 4.45, 3.0, "From warning to survival", [
    "Heat stroke kills when cooling is late. A red card on every screen: move to shade, call 998, start cooling at once without waiting for the ambulance (immersion in cold water up to the neck, or whole-body sheets soaked in ice water), keep cooling until medics take over.",
    "On Elevated and High days the plan adds a cooling station before the shift, with a named person in charge.",
    "Evidence: labourers 3.0–3.7 times less likely to die of heat stroke in US states whose ambulance guidelines include cold-water immersion and cooling first (Tishukaj 2024, PMID 39183116; state-level). Rapid total-body cooling is 'essential for survival' (ACSM 2023, PMID 37036463).",
    "Wording signed by Dr Ahmed Zayed (physician). Not tested by this app.",
], color=RED, size=9)
card(S[14], X0 + 4.75, Y0, W - 4.75, 3.0, "A trained model we chose not to deploy", [
    f"Logistic regression with more inputs (night heat, hot spells, sun, wind), pre-registered, frozen, scored once on the same unseen regions.",
    f"It ranked days better (AUC {P['primary_B_auc']['M']:.2f} vs {P['primary_B_auc']['R4_tiers']:.2f}) and caught {pc(P['M']['sensitivity'])} of case days vs {pc(P['R4']['sensitivity'])}.",
    f"But its alert load swung {round(P['alert_share_spread']['M'] * 100)} points across cities (rule: {round(P['alert_share_spread']['R4'] * 100)}): it learned 'hot place', not 'unusual day'. In Abu Dhabi it would alert on {min(z['alert_share_2025'] for z in mv['abu_dhabi_descriptive'].values()) * 100:.0f}–{max(z['alert_share_2025'] for z in mv['abu_dhabi_descriptive'].values()) * 100:.0f} % of summer days.",
    "It missed the pass mark set before scoring, so the app keeps the relative rule: a governance decision, reported in full.",
], color=BLUE, size=9)

p.save(OUT)
print("saved", OUT, "capability chars", len(CAP))
