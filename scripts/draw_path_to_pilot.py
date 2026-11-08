"""Deck slide 12: path to pilot and scale. usage: python draw_path_to_pilot.py <fonts_dir> <out.png> (Barlow Condensed SemiBold, Atkinson Hyperlegible)."""
import sys
from PIL import Image, ImageDraw, ImageFont
FD, OUT = sys.argv[1], sys.argv[2]
F = lambda n, s: ImageFont.truetype(f"{FD}/{n}", s)
DISP, BODY, BODYB = "BarlowCondensed-SemiBold.ttf", "AtkinsonHyperlegible-Regular.ttf", "AtkinsonHyperlegible-Bold.ttf"
INK, MUTED, CONCRETE, PAPER, BLUE = "#1C2321", "#4E5A57", "#E9ECEA", "#FFFFFF", "#1D4E89"
W, H = 1920, 1080
im = Image.new("RGB", (W, H), CONCRETE); d = ImageDraw.Draw(im)
def wrap(t, f, w):
    out, cur = [], ""
    for x in t.split():
        c = (cur + " " + x).strip()
        if d.textlength(c, font=f) <= w: cur = c
        else: out.append(cur); cur = x
    return out + [cur]
d.text((80, 60), "Path to pilot and scale", font=F(DISP, 84), fill=INK)
d.text((80, 165), "The heat season (May to September) sets the clock: the first real test on Abu Dhabi outcomes is summer 2027.", font=F(BODY, 32), fill=MUTED)
stages = [
 ("Prototype", "Done, 20 Nov 2026", ["Live app, no login", "Tested on 2,628 US heat hospitalisations", "79.1 % of case days caught in 6 unseen regions"], "Submitted"),
 ("Pilot agreement", "Dec 2026 – Apr 2027", ["ADPHC + 3–5 volunteer sites in 4 zones", "Zone-day incident notices (ADOSH-SF)", "Plans in 5 worker languages"], "Success measure fixed in advance"),
 ("Shadow mode", "May – Sep 2027", ["App runs every evening", "Supervisors acknowledge; nothing enforced", "Log alerts, steps done, cases, site TWL"], "One full season of data"),
 ("Local recalibration", "Oct – Dec 2027", ["First score on Abu Dhabi outcomes", "Compare tiers with site TWL", "Retune only if the test supports it"], "ADPHC decides: scale or stop"),
 ("Scale", "2028 onwards", ["Free for all employers in the Safety in Heat toolkit", "Paid integrations for large employers", "Other emirates and Gulf states"], ""),
]
x0, y0, bw, bh, gap = 80, 240, 330, 620, 22
for i, (name, when, items, gate) in enumerate(stages):
    x = x0 + i * (bw + gap)
    done = i == 0
    d.rectangle([x, y0, x + bw, y0 + bh], fill=INK if done else PAPER, outline=INK, width=3)
    fg = PAPER if done else INK
    d.text((x + 24, y0 + 18), f"{i}", font=F(DISP, 56), fill=fg)
    y = y0 + 90
    for ln in wrap(name, F(DISP, 46), bw - 48): d.text((x + 24, y), ln, font=F(DISP, 46), fill=fg); y += 50
    d.text((x + 24, y + 4), when, font=F(BODYB, 26), fill=PAPER if done else BLUE); y += 56
    for it in items:
        for k, ln in enumerate(wrap(it, F(BODY, 24), bw - 70)):
            if k == 0: d.ellipse([x + 26, y + 11, x + 36, y + 21], fill=fg)
            d.text((x + 48, y), ln, font=F(BODY, 24), fill=fg); y += 31
        y += 10
    if gate:
        gy = y0 + bh - 104
        d.line([x + 24, gy, x + bw - 24, gy], fill=PAPER if done else MUTED, width=2)
        d.text((x + 24, gy + 12), "Gate", font=F(BODYB, 22), fill=PAPER if done else MUTED)
        for k, ln in enumerate(wrap(gate, F(BODYB, 24), bw - 48)):
            d.text((x + 24, gy + 40 + k * 30), ln, font=F(BODYB, 24), fill=fg)
    if i < len(stages) - 1:
        ax = x + bw + 2; ay = y0 + bh // 2
        d.polygon([(ax, ay - 12), (ax + gap - 4, ay), (ax, ay + 12)], fill=INK)
d.text((80, 895), "Who pays: ADPHC first, as the digital layer of its Safety in Heat programme (free to employers); paid integrations for large employers later.", font=F(BODY, 28), fill=INK)
d.text((80, 940), "No hardware, no personal data: a public forecast and three yes / no crew questions. Each zone's own climate sets its thresholds.", font=F(BODY, 28), fill=INK)
d.text((80, 1005), "Targets for stages 1–3 are proposals to agree with ADPHC. Rule tested on US outcomes; not yet validated in Abu Dhabi.", font=F(BODY, 24), fill=MUTED)
im.save(OUT); print("ok")
