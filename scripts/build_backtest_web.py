"""Build web/data/backtest.json for the app's back-test explorer (v4).

The frozen R4 rule on the 6 US holdout regions, 2022-2025, each day with the weather that actually happened, next to the
days with a reported work heat hospitalisation (US OSHA Severe Injury Reports). Same frame and rule as
scripts/score_holdout.py; the totals are checked against results/holdout_results.json before the file is written.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from heatwarn.data import build_frame, holdout_regions  # noqa: E402
from heatwarn.relative import RelParams, r4_tier  # noqa: E402
from heatwarn.rules import r1_fixed  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
CODE = {"High": "H", "Elevated": "E", "No escalation": "N", "Insufficient data": "X"}


def main() -> None:
    p4 = RelParams(**json.loads((ROOT / "results" / "frozen_params_r4.json").read_text())["params"])
    regs = holdout_regions()
    full, _ = build_frame(last_year=2025, regions=regs)
    t = full[full.index.year >= 2022].copy()
    t["tier"] = r4_tier(t["h"], t["p"], t["a"], p4)
    t["R1"] = r1_fixed(t["h"])
    out = {"source": "Frozen R4 rule, 6 US holdout regions, 2022-2025, observed weather; events = days with a reported "
                     "work heat hospitalisation (US OSHA Severe Injury Reports)", "regions": {}}
    tp = ev = fixed_days = 0
    for r in regs:
        g = t[t["region"] == r.key].sort_index()
        tiers = "".join(CODE[x] for x in g["tier"])
        events = "".join("1" if e else "0" for e in g["event"].astype(bool))
        fixed = "".join("1" if bool(x) else "0" for x in g["R1"].fillna(False))
        out["regions"][r.key] = {
            "name": r.name, "dates": [d.strftime("%Y-%m-%d") for d in g.index], "tier": tiers, "event": events, "fixed": fixed,
            # rounded down, so a shown value never crosses a threshold the rule did not cross (79.6 °F shows as 79, not 80)
            "hi_f": [math.floor(x) for x in g["h"]], "pctl": [math.floor(x) for x in g["p"]],
            "jump_f": [math.floor(x * 10) / 10 for x in g["a"]], "reports": [int(x) for x in g["reports"]],
        }
        tp += sum(1 for a, e in zip(tiers, events) if e == "1" and a in "HE")
        ev += events.count("1")
        fixed_days += fixed.count("1")
    rules = json.loads((ROOT / "results" / "holdout_results.json").read_text())["rules"]
    ho = rules["R4"]
    assert fixed_days == rules["R1"]["alert_days"], f"fixed-rule alert days {fixed_days} vs {rules['R1']['alert_days']}"
    assert (tp, ev) == (ho["tp"], ho["tp"] + ho["fn"]), f"mismatch with holdout_results.json: {tp}/{ev} vs {ho['tp']}/{ho['tp'] + ho['fn']}"
    (ROOT / "web" / "data" / "backtest.json").write_text(json.dumps(out, separators=(",", ":")))
    print(f"caught {tp} of {ev} event days ({tp / ev:.1%}); matches results/holdout_results.json")


if __name__ == "__main__":
    main()
