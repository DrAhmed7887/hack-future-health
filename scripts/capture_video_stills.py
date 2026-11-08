"""Capture phone stills for the Future Health video, per docs/video_plan.md section 3."""
import json, sys, pathlib
from playwright.sync_api import sync_playwright

BASE = "https://drahmed7887.github.io/hack-future-health/"
OUT = pathlib.Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
CTX = dict(viewport={"width": 360, "height": 640}, device_scale_factor=3, is_mobile=True, has_touch=True,
           locale="en-GB", timezone_id="Asia/Dubai", color_scheme="light", reduced_motion="reduce")
SEED = "localStorage.setItem('zone', JSON.stringify('mussafah'));"
log = []

def ready(pg):
    pg.wait_for_selector("#app h1, #app .tier")
    pg.evaluate("document.fonts.ready.then(()=>1)")
    pg.wait_for_timeout(150)

def go(pg, h):
    pg.evaluate("h => { location.hash = h; }", h); pg.wait_for_timeout(100); ready(pg)

def shot(pg, name, full=False):
    pg.screenshot(path=str(OUT / f"{name}.png"), animations="disabled", caret="hide", full_page=full)
    log.append(name)

def top(pg, sel, has_text=None):
    loc = pg.locator(sel, has_text=has_text).first if has_text else pg.locator(sel).first
    loc.evaluate("e => e.scrollIntoView({block:'start'})"); pg.wait_for_timeout(100)

def answer(pg, q, v):
    pg.click(f'label:has(input[name="{q}"][value="{v}"])')
    pg.wait_for_selector(f'input[name="{q}"][value="{v}"]:checked', state="attached"); ready(pg)

def text(pg): return pg.inner_text("#app")

def must(cond, msg):
    if not cond: raise SystemExit("ASSERT FAILED: " + msg)

with sync_playwright() as p:
    b = p.chromium.launch()
    # Session 1: Mussafah, Fri 1 Aug 2025
    ctx = b.new_context(**CTX); ctx.add_init_script(SEED); pg = ctx.new_page()
    pg.goto(BASE + "#replay"); ready(pg); pg.wait_for_timeout(300)
    must(pg.input_value("#rz") == "mussafah", "zone mussafah")
    pg.click('[data-day="2025-08-01"]'); pg.wait_for_function("location.hash === '#home'"); ready(pg)
    t = text(pg); must("High" in pg.inner_text(".tier"), "tier High"); must("11" in t and "hottest days" in t, "why line")
    top(pg, ".tier"); shot(pg, "S1_home"); shot(pg, "S1_home_full", True)
    pg.evaluate("scrollTo(0,0)"); shot(pg, "S2_header")
    go(pg, "#site"); shot(pg, "S3_site")
    go(pg, "#trust"); shot(pg, "S4a_trust_top"); shot(pg, "S4_trust_full", True)
    (OUT / "S4_trust.txt").write_text(text(pg))
    top(pg, ".facts > div"); shot(pg, "S4b_fact79")
    pg.locator(".facts > div").nth(3).evaluate("e => e.scrollIntoView({block:'start'})"); shot(pg, "S5_fact84")
    top(pg, "h2", "What did not work"); shot(pg, "S6_failed")
    top(pg, "h2", "Limits"); shot(pg, "S11_limits")
    go(pg, "#home"); top(pg, ".legal"); t = text(pg)
    for s in ["12:30 to 15:00", "45", "does not calculate it"]: must(s in t, "law: " + s)
    shot(pg, "S7_law")
    go(pg, "#crew"); answer(pg, "newWorkers", "no"); answer(pg, "heavy", "no"); shot(pg, "S8_crew_nono")
    go(pg, "#plan"); top(pg, ".layer.model"); shot(pg, "S8_plan_nono")
    go(pg, "#crew"); answer(pg, "heavy", "yes"); shot(pg, "S8a_crew_heavy")
    go(pg, "#plan"); must("Move heavy tasks away" in text(pg), "heavy step"); top(pg, ".layer.model"); shot(pg, "S8b_plan_heavy")
    go(pg, "#crew"); answer(pg, "newWorkers", "yes"); shot(pg, "S8c_crew_new")
    go(pg, "#plan"); t = text(pg); must("20% of the usual heat exposure" in t, "acclim step")
    top(pg, "li", "Move heavy tasks"); shot(pg, "S8d_plan_new"); shot(pg, "S8_plan_full", True)
    go(pg, "#regulator"); t = text(pg); must("1 Aug 2025" in t and "Fewer than 5 sites" in t, "regulator")
    shot(pg, "S10_regulator"); top(pg, "h3, h2, strong, div", "Abu Dhabi city"); shot(pg, "S10b_regulator_ruwais"); shot(pg, "S10_regulator_full", True); (OUT / "S10_regulator.txt").write_text(t)
    ctx.close()
    # Session 2: Mussafah, Mon 7 Jul 2025
    ctx = b.new_context(**CTX); ctx.add_init_script(SEED); pg = ctx.new_page()
    pg.goto(BASE + "#replay"); ready(pg); pg.wait_for_timeout(300)
    pg.fill("#rd", "2025-07-07"); pg.click(".cta .btn"); pg.wait_for_function("location.hash === '#home'"); ready(pg)
    tier7 = pg.inner_text(".tier")
    go(pg, "#crew"); answer(pg, "newWorkers", "no"); answer(pg, "heavy", "no")
    go(pg, "#plan"); t = text(pg); must("No extra steps from the forecast." in t, "no steps 7 Jul")
    top(pg, ".tier"); shot(pg, "S9a_plan_none"); shot(pg, "S9a_plan_full", True)
    go(pg, "#crew"); answer(pg, "newWorkers", "yes")
    go(pg, "#plan"); t = text(pg); must("Raised one level from No escalation" in t, "raised")
    top(pg, ".tier"); shot(pg, "S9b_plan_raised")
    ctx.close(); b.close()
print(json.dumps({"shots": log, "tier_7jul": tier7}))
