"""v2 stills after the video-director review: masked evidence crops (S4-S6) and outlined plan lines (S8).
Writes <out>/masks.json: {still: css_y} — the build paints the phone blank below that y."""
import json, sys, pathlib
from playwright.sync_api import sync_playwright

BASE = "https://drahmed7887.github.io/hack-future-health/"
OUT = pathlib.Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
CTX = dict(viewport={"width": 360, "height": 640}, device_scale_factor=3, is_mobile=True, has_touch=True,
           locale="en-GB", timezone_id="Asia/Dubai", color_scheme="light", reduced_motion="reduce")
masks = {}
OUTLINE = "outline:3px solid #1C2321;outline-offset:4px;"

def ready(pg):
    pg.wait_for_selector("#app h1, #app .tier"); pg.evaluate("document.fonts.ready.then(()=>1)"); pg.wait_for_timeout(150)

def go(pg, h):
    pg.evaluate("h => { location.hash = h; }", h); pg.wait_for_timeout(100); ready(pg)

def to_top(pg, js):  # js: expression returning the element
    pg.evaluate(f"(() => {{ const e = {js}; e.scrollIntoView({{block:'start'}}); }})()"); pg.wait_for_timeout(120)

def bottom(pg, js):
    return pg.evaluate(f"(() => {{ const e = {js}; return e.getBoundingClientRect().bottom + 12; }})()")

def shot(pg, name, mask_js=None):
    pg.screenshot(path=str(OUT / f"{name}.png"), animations="disabled", caret="hide")
    if mask_js: masks[name] = round(bottom(pg, mask_js), 1)

def answer(pg, q, v):
    pg.click(f'label:has(input[name="{q}"][value="{v}"])')
    pg.wait_for_selector(f'input[name="{q}"][value="{v}"]:checked', state="attached"); ready(pg)

def li(text):
    return f"[...document.querySelectorAll('#app li')].find(e => e.textContent.includes({json.dumps(text)}))"

def outline(pg, text):
    pg.evaluate(f"(() => {{ {li(text)}.style.cssText += {json.dumps(OUTLINE)}; }})()")

H2 = lambda t: f"[...document.querySelectorAll('#app h2')].find(e => e.textContent.includes({json.dumps(t)}))"
P_2628 = "[...document.querySelectorAll('#app p')].find(e => e.textContent.includes('2,628'))"

with sync_playwright() as p:
    b = p.chromium.launch()
    ctx = b.new_context(**CTX); ctx.add_init_script("localStorage.setItem('zone', JSON.stringify('mussafah'));")
    pg = ctx.new_page(); pg.goto(BASE + "#replay"); ready(pg); pg.wait_for_timeout(300)
    pg.click('[data-day="2025-08-01"]'); pg.wait_for_function("location.hash === '#home'"); ready(pg)
    go(pg, "#trust"); pg.evaluate("scrollTo(0,0)"); pg.wait_for_timeout(100)
    shot(pg, "v2_S4a_method", P_2628)
    card = lambda i: f"document.querySelectorAll('#app .facts > div')[{i}]"
    to_top(pg, card(0)); assert "79.1" in pg.evaluate(f"{card(0)}.textContent"); shot(pg, "v2_S4b_fact79", card(0))
    to_top(pg, card(3)); assert "84" in pg.evaluate(f"{card(3)}.textContent"); shot(pg, "v2_S5_fact84", card(3))
    to_top(pg, H2("What did not work")); shot(pg, "v2_S6_failed", f"{H2('What did not work')}.nextElementSibling")
    go(pg, "#crew"); answer(pg, "newWorkers", "no"); answer(pg, "heavy", "no")
    go(pg, "#plan"); to_top(pg, "document.querySelector('#app .layer.model')"); shot(pg, "v2_S8a_plan_nono")
    go(pg, "#crew"); answer(pg, "heavy", "yes"); go(pg, "#plan")
    outline(pg, "Move heavy tasks"); to_top(pg, "document.querySelector('#app .layer.model')"); shot(pg, "v2_S8b_plan_heavy")
    go(pg, "#crew"); answer(pg, "newWorkers", "yes"); go(pg, "#plan")
    outline(pg, "no more than 20%"); outline(pg, "No unacclimatised"); to_top(pg, li("Move heavy tasks")); shot(pg, "v2_S8c_plan_new")
    ctx.close(); b.close()
(OUT / "masks.json").write_text(json.dumps(masks, indent=1)); print(json.dumps(masks))
