"""Build the Future Health demo film from phone stills + per-shot narration (docs/video_plan.md).
usage: python build_video.py <video_dir> <fonts_dir> <narr.json>
Writes <video_dir>/build/frames/*.png, video.txt, audio.txt, timeline.json."""
import json, re, subprocess, sys, pathlib
from PIL import Image, ImageDraw, ImageFont, ImageEnhance

V, FD, NJ = map(pathlib.Path, sys.argv[1:4])
ST, OUT = V / "stills", V / "build"; FR = OUT / "frames"; FR.mkdir(parents=True, exist_ok=True)
INK, MUTED, CONCRETE, PAPER, BLUE = "#1C2321", "#4E5A57", "#E9ECEA", "#FFFFFF", "#1D4E89"
W, H = 1920, 1080
F = lambda name, size: ImageFont.truetype(str(FD / name), size)
DISP, BODY, BODYB = "BarlowCondensed-SemiBold.ttf", "AtkinsonHyperlegible-Regular.ttf", "AtkinsonHyperlegible-Bold.ttf"
LEAD, GAP, END_HOLD = 0.4, 0.25, 1.6
MASKS = json.loads((ST / "masks.json").read_text()) if (ST / "masks.json").exists() else {}
narr = json.loads(NJ.read_text())

# Each shot: stills [(fraction_start, name)], label, beats [(fraction, kind, text)] cumulative.
SHOTS = {
 "S1": dict(stills=[(0, "S1_home")], label="Mussafah · Fri 1 Aug 2025 · real weather (ERA5)",
            beats=[(0.30, "big", "As hot as the hottest days here at this time of year (2015–2021)"),
                   (0.62, "big", "11 °C above the previous 14 days")]),
 "S2": dict(stills=[(0, "S2_header")], label="",
            beats=[(0.05, "title", "Heat Shift Planner (working name)"), (0.05, "small", "Ahmed Zayed, physician"), (0.05, "src", "Narration: synthetic voice (ElevenLabs), script by the author.")]),
 "S3": dict(stills=[(0, "S3_site")], label="Why a new rule was needed",
            beats=[(0.05, "big", "Fixed thresholds tuned on 8 US regions: top tier on every Abu Dhabi day, June to September"),
                   (0.05, "src", "Source: back-test, transfer check (README)")]),
 "S4": dict(stills=[(0, "v2_S4a_method"), (0.74, "v2_S4b_fact79")], label="How it was tested",
            beats=[(0.18, "big", "2,628 work-related heat hospitalisation reports · US OSHA · Jan 2015 – Nov 2025"),
                   (0.42, "big", "Tuned on 2015–2021 · frozen · scored once"),
                   (0.55, "big", "6 unseen US regions, 2022–2025 · 86 days with a reported case"),
                   (0.76, "big", "79.1 % caught (95 % CI 69.6–87.9) · 49 % of days alerted"),
                   (0.90, "src", "Gain over fixed thresholds +8.1 points (95 % CI −6.9 to +24.3): not statistically clear.")]),
 "S5": dict(stills=[(0, "v2_S5_fact84")], label="Forecast the evening before",
            beats=[(0.10, "big", "Same decision on 84 % of region-days · 8 US regions, 2024–2025"),
                   (0.50, "small", "The forecast ran warm: it alerted on 59 % vs 51 % of days.")]),
 "S6": dict(stills=[(0, "v3_S6_model")], label="We also trained a model (pre-registered, frozen, scored once)",
            beats=[(0.10, "big", "Ranked days better: AUC 0.73, against 0.66 for the rule"),
                   (0.38, "big", "Alert load swung with climate: 5 % to 81 % of days (rule: 36 % to 60 %)"),
                   (0.62, "big", "Abu Dhabi, May–Sep 2025: alerts on 93–100 % of days"),
                   (0.62, "src", "6 unseen US regions, 2022–2025. Caught 77.9 % vs 79.1 % of case days. Pass mark set before scoring: not met, so the app keeps the rule.")]),
 "S7": dict(stills=[(0, "S7_law")], label="Required by law",
            beats=[(0.08, "big", "Shown whatever the rule says"),
                   (0.08, "src", "UAE MoHRE midday break · ADPHC CoP 11.0 §3.1.1(e) · ADPHC Technical Guideline")]),
 "S8": dict(stills=[(0, "v2_S8a_plan_nono"), (0.20, "v2_S8b_plan_heavy"), (0.52, "v2_S8c_plan_new")],
            label="Same day, same weather",
            beats=[(0.0, "big", "The crew answers change the plan"),
                   (0.0, "chip", "Heavy work: No · New or returning workers: No"),
                   (0.20, "chip", "Heavy work: Yes · New or returning workers: No"),
                   (0.52, "chip", "Heavy work: Yes · New or returning workers: Yes"),
                   (0.52, "src", "Crew rules come from guidelines (NIOSH 2016; ADPHC). Not tested on outcomes.")]),
 "S9": dict(stills=[(0, "S9a_plan_none"), (0.45, "S9b_plan_raised")], label="Mussafah · Mon 7 Jul 2025 · replay",
            beats=[(0.0, "big", "Forecast: no extra steps. The law still applies."),
                   (0.45, "big", "New or returning workers raise the tier one level"),
                   (0.45, "src", "Our rule, based on guidelines, not tested on outcomes.")]),
 "S10": dict(stills=[(0, "S10_regulator"), (0.50, "S10b_regulator_ruwais")], label="SIMULATED: sites, acknowledgements, incident notices",
             beats=[(0.0, "big", "Zones, not people"),
                    (0.50, "small", "Below 5 sites, site counts are hidden. Incident notices never change the tier.")]),
 "S11": dict(stills=[(0, "S11_limits")], label="Limits",
             beats=[(0.0, "small", "US data, reported cases only"), (0.25, "small", "Not validated on Abu Dhabi outcomes"),
                    (0.45, "small", "Tested May to September only"), (0.65, "small", "Not a medical device. Never a clearance to work.")]),
 "S12": dict(stills=[(0, "S4b_fact79")], label="", beats=[], end=True),
}

def wrap(d, text, font, width):
    lines, cur = [], ""
    for w in text.split():
        t = (cur + " " + w).strip()
        if d.textlength(t, font=font) <= width: cur = t
        else: lines.append(cur); cur = w
    return lines + ([cur] if cur else [])

def phone(name, dim=False):
    im = Image.open(ST / f"{name}.png").convert("RGB").resize((540, 960), Image.LANCZOS)
    if name in MASKS:
        ImageDraw.Draw(im).rectangle([0, int(MASKS[name] * 1.5), 540, 960], fill=PAPER)
    return ImageEnhance.Brightness(im).enhance(0.2) if dim else im

def sentences(text):
    safe = text.strip().replace("p.m.", "P_M_")  # "2 p.m. peak" is one sentence
    return [s.replace("P_M_", "p.m.") for s in re.split(r"(?<=[.?!])\s+", safe) if s]

def frame(still, label, items, caption, end=False):
    c = Image.new("RGB", (W, H), CONCRETE); d = ImageDraw.Draw(c)
    c.paste(phone(still, dim=end), (140, 60)); d.rectangle([139, 59, 680, 1020], outline=INK, width=2)
    x, maxw = 780, 1020
    if end:
        d.text((x, 200), "79.1 %", font=F(DISP, 200), fill=INK)
        y = 450
        for line in wrap(d, "of reported-case days caught · 6 US regions it had never seen · 49 % of days alerted", F(BODY, 40), maxw):
            d.text((x, y), line, font=F(BODY, 40), fill=INK); y += 54
        d.text((x, y + 30), "Not yet validated in Abu Dhabi.", font=F(BODYB, 44), fill=INK)
        d.text((x, 860), "drahmed7887.github.io/hack-future-health", font=F(BODYB, 34), fill=BLUE)
        d.text((x, 915), "Narration: synthetic voice (ElevenLabs).", font=F(BODY, 26), fill=MUTED)
        return c
    y = 80
    if label:
        d.text((x, y), label, font=F(BODYB, 28), fill=MUTED); y += 70
    for kind, text in items:
        if kind == "title":
            d.text((x, y), text, font=F(DISP, 78), fill=INK); y += 100; continue
        if kind == "chip":
            cf = F(BODYB, 30); tw = d.textlength(text, font=cf)
            d.rectangle([x, y, x + tw + 36, y + 56], fill=INK); d.text((x + 18, y + 10), text, font=cf, fill=PAPER); y += 80; continue
        font, gap, col = {"big": (F(DISP, 54), 62, INK), "small": (F(BODY, 34), 46, INK), "src": (F(BODY, 26), 36, MUTED)}[kind]
        if kind == "big": d.rectangle([x, y + 8, x + 6, y + 8 + gap * len(wrap(d, text, font, maxw - 30)) - 14], fill=INK); tx = x + 26
        else: tx = x
        for line in wrap(d, text, font, maxw - (tx - x)):
            d.text((tx, y), line, font=font, fill=col); y += gap
        y += 22
    if caption:
        cf = F(BODY, 36); lines = wrap(d, caption, cf, maxw); cy = 1000 - 50 * len(lines)
        d.rectangle([x - 20, cy - 16, x + maxw + 20, 1012], fill=PAPER)
        for line in lines: d.text((x, cy), line, font=cf, fill=INK); cy += 50
    return c

def dur(p): return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)], capture_output=True, text=True).stdout)

vlist, alist, timeline, t0, n = [], [], [], 0.0, 0
sil = lambda s: OUT / f"sil_{int(round(s*1000))}.wav"
def make_sil(s):
    p = sil(s)
    if not p.exists(): subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "anullsrc=r=48000:cl=mono", "-t", f"{s:.3f}", str(p)], check=True)
    return p
alist.append(make_sil(LEAD))
keys = list(SHOTS)
for k in keys:
    sh = SHOTS[k]; wav = OUT / f"{k}.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(V / "narration" / f"{k}.mp3"), "-ar", "48000", "-ac", "1", str(wav)], check=True)
    speech = dur(wav); tail = END_HOLD if sh.get("end") else GAP
    lead = LEAD if k == "S1" else 0.0
    total = lead + speech + tail
    alist += [wav, make_sil(tail)]
    # caption timing: sentences proportional to characters over the speech span
    sents = sentences(narr[k]["narr"]); chars = max(1, sum(len(s) for s in sents)); acc = 0; caps = []
    for s in sents: caps.append((lead + speech * acc / chars, s)); acc += len(s)
    events = sorted({0.0} | {lead + f * speech for f, _ in sh["stills"]} | {lead + f * speech for f, *_ in sh["beats"]} | {c for c, _ in caps})
    for i, e in enumerate(events):
        nxt = events[i + 1] if i + 1 < len(events) else total
        if nxt - e < 0.04: continue
        still = [nm for f, nm in sh["stills"] if (0 if f == 0 else lead + f * speech) <= e + 1e-6][-1]
        items = [(kind, txt) for f, kind, txt in sh["beats"] if lead + f * speech <= e + 1e-6]
        chips = [it for it in items if it[0] == "chip"]
        items = [it for it in items if it[0] != "chip"] + chips[-1:]
        cap = [s for c, s in caps if c <= e + 1e-6]; cap = cap[-1] if cap and e < lead + speech else ""
        img = frame(still, sh["label"], items, cap, end=sh.get("end", False))
        fp = FR / f"{n:04d}_{k}.png"; img.save(fp); n += 1
        vlist.append((fp, nxt - e))
    timeline.append({"shot": k, "start": round(t0, 2), "end": round(t0 + total, 2), "speech": round(speech, 2)}); t0 += total

(OUT / "video.txt").write_text("".join(f"file '{p}'\nduration {d:.3f}\n" for p, d in vlist) + f"file '{vlist[-1][0]}'\n")
(OUT / "audio.txt").write_text("".join(f"file '{p}'\n" for p in alist))
(OUT / "timeline.json").write_text(json.dumps(timeline, indent=1))
print(json.dumps({"frames": n, "total_s": round(t0, 2)}))
