"""Score frozen R2 and R4 ONCE on the holdout regions, 2022-2025 (protocol v3). Writes results/holdout_results.json."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from heatwarn.data import build_frame, holdout_regions  # noqa: E402
from heatwarn.metrics import block_bootstrap, confusion, episodes  # noqa: E402
from heatwarn.relative import RelParams, r4_relative  # noqa: E402
from heatwarn.rules import Params, r0_calendar, r1_fixed, r2_weather  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    p2 = Params(**json.loads((ROOT / "results" / "frozen_params.json").read_text())["r2"]["params"])
    p4 = RelParams(**json.loads((ROOT / "results" / "frozen_params_r4.json").read_text())["params"])
    regs = holdout_regions()
    full, stats = build_frame(last_year=2025, regions=regs)
    t = full[full.index.year >= 2022].copy()
    t["R0"], t["R1"] = r0_calendar(t.index), r1_fixed(t["h"])
    t["R2"], t["R4"] = r2_weather(t["h"], t["a"], p2), r4_relative(t["h"], t["p"], t["a"], p4)
    names = {r.key: r.name for r in regs}
    res = {"frozen": {"R2": p2.__dict__, "R4": p4.__dict__}, "data": stats | {
        "region_days": len(t), "event_days": int(t["event"].sum()), "reports": int(t["reports"].sum())}}
    res["rules"] = {}
    for k in ("R0", "R1", "R2", "R4"):
        c = confusion(t[k], t["event"])
        c["sensitivity_95ci"] = list(block_bootstrap(t, lambda s, k=k: confusion(s[k], s["event"])["sensitivity"]))
        c["episodes"] = sum(episodes(g[k])[0] for _, g in t.groupby(["region", t.index.year]))
        res["rules"][k] = c
    diff = lambda s: confusion(s["R4"], s["event"])["sensitivity"] - confusion(s["R2"], s["event"])["sensitivity"]  # noqa: E731
    res["primary_A_r4_minus_r2_sensitivity"] = {"point": diff(t), "95ci": list(block_bootstrap(t, diff))}
    per = {}
    for reg, g in t.groupby("region"):
        per[names[reg]] = {k: {"alert_share": confusion(g[k], g["event"])["alert_fraction"],
                               "caught": confusion(g[k], g["event"])["tp"], "event_days": int(g["event"].sum())}
                           for k in ("R2", "R4")}
    res["per_region"] = per
    spread = {k: max(v[k]["alert_share"] for v in per.values()) - min(v[k]["alert_share"] for v in per.values()) for k in ("R2", "R4")}
    res["primary_B_alert_share_spread"] = spread
    a = res["primary_A_r4_minus_r2_sensitivity"]["point"]
    res["success_criterion_met"] = bool(a >= -0.05 and spread["R4"] < spread["R2"])
    (ROOT / "results" / "holdout_results.json").write_text(json.dumps(res, indent=2, default=float))
    print(json.dumps({k: res[k] for k in ("data", "primary_A_r4_minus_r2_sensitivity", "primary_B_alert_share_spread", "success_criterion_met")}, indent=1, default=float))
    for k, v in res["rules"].items():
        print(k, f"sens {v['sensitivity']:.1%} {[round(x*100,1) for x in v['sensitivity_95ci']]} ppv {v['reported_event_ppv']:.1%} alert {v['alert_fraction']:.0%} episodes {v['episodes']}")
    for n, v in per.items():
        print(n, {k: (v[k]['caught'], v[k]['event_days'], round(v[k]['alert_share'], 2)) for k in v})


if __name__ == "__main__":
    main()
