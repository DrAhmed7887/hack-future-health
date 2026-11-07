"""Step 2: score the frozen rules ONCE on 2022-2025 and write results/test_results.json + results/test_results.md."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from heatwarn.data import build_frame, load_osha_heat  # noqa: E402
from heatwarn.metrics import block_bootstrap, confusion, episodes  # noqa: E402
from heatwarn.rules import Params, r0_calendar, r1_fixed, r2_weather, r3_weather_workplace  # noqa: E402
from heatwarn.signals import anomaly_by_block  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
FIRST_TEST_YEAR, LAST_YEAR = 2022, 2025
INDUSTRIES = {"construction (23)": {"23"}, "transport/warehousing (48-49)": {"48", "49"}, "admin/waste services (56)": {"56"}}


def alerts(df: pd.DataFrame, p2: Params, p3: Params) -> dict[str, pd.Series]:
    return {"R0 calendar": r0_calendar(df.index), "R1 heat index >= 80 F": r1_fixed(df["h"]),
            "R2 weather": r2_weather(df["h"], df["a"], p2), "R3 weather + workplace": r3_weather_workplace(df["h"], df["a"], df["w"], p3)}


def sens(alert_col: str):
    def f(s: pd.DataFrame) -> float:
        c = confusion(s[alert_col], s["event"])
        return c["sensitivity"]
    return f


def ep_total(df: pd.DataFrame, col: str) -> tuple[int, int]:
    n = longest = 0
    for (_, _), g in df.groupby(["region", df.index.year]):
        a, b = episodes(g[col]); n += a; longest = max(longest, b)
    return n, longest


def with_missing(df: pd.DataFrame, mask: pd.Series) -> pd.DataFrame:
    """Blank H on masked days and recompute the anomaly per region (missing days stay missing)."""
    out = df.copy()
    out.loc[mask, "h"] = np.nan
    out["a"] = anomaly_by_block(out).to_numpy()
    return out


def main() -> None:
    frozen = json.loads((ROOT / "results" / "frozen_params.json").read_text())
    p2, p3 = Params(**frozen["r2"]["params"]), Params(**frozen["r3"]["params"])
    full, stats = build_frame(last_year=LAST_YEAR)
    test = full[full.index.year >= FIRST_TEST_YEAR].copy()
    res: dict = {"frozen_params": {"r2": p2.__dict__, "r3": p3.__dict__}, "data": stats}
    res["data"] |= {"test_region_days": len(test), "test_event_days": int(test["event"].sum()),
                    "test_reports": int(test["reports"].sum()), "test_workers": float(test["workers"].sum())}

    rules = alerts(test, p2, p3)
    for k, v in rules.items():
        test[k] = v
    res["rules"] = {}
    for k in rules:
        c = confusion(test[k], test["event"]); n_ep, longest = ep_total(test, k)
        lo, hi = block_bootstrap(test, sens(k))
        res["rules"][k] = c | {"sensitivity_95ci": [lo, hi], "episodes": n_ep, "longest_run_days": longest}

    def diff(s):
        return sens("R3 weather + workplace")(s) - sens("R2 weather")(s)
    res["primary_r3_minus_r2_sensitivity"] = {"point": diff(test), "95ci": list(block_bootstrap(test, diff))}

    res["per_region"] = {r: {k: confusion(g[k], g["event"]) for k in ("R1 heat index >= 80 F", "R2 weather", "R3 weather + workplace")}
                         for r, g in test.groupby("region")}

    reports, _ = load_osha_heat(LAST_YEAR)
    reports = reports[reports["date"].dt.year >= FIRST_TEST_YEAR]
    res["subgroups"] = {}
    for name, codes in INDUSTRIES.items():
        days = reports[reports["naics2"].isin(codes)][["region", "date"]].drop_duplicates()
        keyset = set(zip(days["region"], days["date"]))
        ev = pd.Series([(r, d) in keyset for r, d in zip(test["region"], test.index)], index=test.index)
        res["subgroups"][name] = {k: confusion(test[k], ev) for k in ("R1 heat index >= 80 F", "R2 weather", "R3 weather + workplace")}

    rng = np.random.default_rng(20261107)
    miss = {}
    m_random = pd.Series(rng.random(len(test)) < 0.2, index=test.index)
    hottest = pd.Series(False, index=test.index)
    for (_, _), g in test.groupby(["region", test.index.year]):
        roll = g["h"].rolling(3).mean()
        end = roll.idxmax()
        sel = (test["region"] == g["region"].iloc[0]) & (test.index >= end - pd.Timedelta(days=2)) & (test.index <= end)
        hottest |= sel
    for label, mask in (("20 % of days missing at random", m_random), ("3-day outage in each season's hottest week", hottest)):
        t2 = with_missing(test, mask)
        miss[label] = {"R2 weather": confusion(r2_weather(t2["h"], t2["a"], p2), t2["event"]),
                       "R3 weather + workplace": confusion(r3_weather_workplace(t2["h"], t2["a"], t2["w"], p3), t2["event"])}
    no_w = test.copy(); no_w["w"] = 0
    miss["workplace feed unavailable (R3 falls back)"] = {"R3 weather + workplace": confusion(
        r3_weather_workplace(no_w["h"], no_w["a"], no_w["w"], p3), no_w["event"])}
    res["missing_inputs"] = miss

    (ROOT / "results" / "test_results.json").write_text(json.dumps(res, indent=2, default=float))
    lines = ["| Rule | Sensitivity (95 % CI) | Reported-event PPV | Alert days / region-days | Episodes | Longest run |", "|---|---|---|---|---|---|"]
    for k, v in res["rules"].items():
        lo, hi = v["sensitivity_95ci"]
        lines.append(f"| {k} | {v['sensitivity']:.1%} ({lo:.1%}–{hi:.1%}) | {v['reported_event_ppv']:.1%} | "
                     f"{v['alert_days']} / {v['days']} ({v['alert_fraction']:.0%}) | {v['episodes']} | {v['longest_run_days']} |")
    (ROOT / "results" / "test_results.md").write_text("\n".join(lines) + "\n")
    print(json.dumps({k: res[k] for k in ("data", "primary_r3_minus_r2_sensitivity")}, indent=2, default=float))
    print("\n".join(lines))
    print(json.dumps(res["missing_inputs"], indent=1, default=float)[:3000])
    print(json.dumps(res["subgroups"], default=float)[:2500])


if __name__ == "__main__":
    main()
