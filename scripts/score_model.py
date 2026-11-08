"""Protocol v4: score the FROZEN model ONCE on the holdout regions, 2022-2025, against frozen R4.
Writes results/model_v4_results.json. Secondary: original regions 2022-2025, calibration, Abu Dhabi alert share."""
from __future__ import annotations

import json
import pickle
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from heatwarn.data import SEASON, WEATHER_DIR, holdout_regions  # noqa: E402
from heatwarn.features import FEATURES, daily_weather_features, spell_days  # noqa: E402
from heatwarn.metrics import block_bootstrap, confusion  # noqa: E402
from heatwarn.model import usable  # noqa: E402
from heatwarn.regions import REGIONS  # noqa: E402
from heatwarn.relative import RelParams, percentile_rank, r4_relative, r4_tier  # noqa: E402
from scripts.train_model import model_frame  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
TIER_ORDER = {"No escalation": 0, "Elevated": 1, "High": 2}


def predict(fr: pd.DataFrame, model, t_alert: float, t_high: float) -> pd.DataFrame:
    out = pd.DataFrame(index=fr.index)
    risk = pd.Series(np.nan, index=fr.index)
    ok = fr[FEATURES].notna().all(axis=1).to_numpy()
    risk[ok] = model.predict_proba(fr.loc[ok, FEATURES])[:, 1]
    out["risk"] = risk
    out["alert"] = (risk >= t_alert).astype("boolean")
    out.loc[risk.isna(), "alert"] = pd.NA
    out["tier"] = np.where(risk.isna(), "Insufficient data", np.where(risk >= t_high, "High", np.where(risk >= t_alert, "Elevated", "No escalation")))
    return out


def auc(y, s) -> float:
    ok = ~(pd.isna(s))
    y, s = np.asarray(y)[ok], np.asarray(s, dtype=float)[ok]
    return float(roc_auc_score(y, s)) if 0 < y.sum() < len(y) else float("nan")


def score(t: pd.DataFrame, names: dict) -> dict:
    res = {"rows": len(t), "event_days": int(t["event"].sum())}
    for k in ("M", "M2", "R4"):
        c = confusion(t[k], t["event"])
        c["sensitivity_95ci"] = list(block_bootstrap(t, lambda s, k=k: confusion(s[k], s["event"])["sensitivity"]))
        res[k] = c
    d = lambda s: confusion(s["M"], s["event"])["sensitivity"] - confusion(s["R4"], s["event"])["sensitivity"]  # noqa: E731
    res["primary_A_M_minus_R4_sensitivity"] = {"point": d(t), "95ci": list(block_bootstrap(t, d))}
    da = lambda s: auc(s["event"], s["M_risk"]) - auc(s["event"], s["R4_ord"])  # noqa: E731
    res["primary_B_auc"] = {"M": auc(t["event"], t["M_risk"]), "R4_tiers": auc(t["event"], t["R4_ord"]),
                            "M2": auc(t["event"], t["M2_risk"]), "difference_M_minus_R4": da(t), "difference_95ci": list(block_bootstrap(t, da))}
    per = {}
    for reg, g in t.groupby("region"):
        per[names[reg]] = {k: {"alert_share": confusion(g[k], g["event"])["alert_fraction"], "caught": confusion(g[k], g["event"])["tp"],
                               "event_days": int(g["event"].sum())} for k in ("M", "R4")}
    res["per_region"] = per
    res["alert_share_spread"] = {k: max(v[k]["alert_share"] for v in per.values()) - min(v[k]["alert_share"] for v in per.values()) for k in ("M", "R4")}
    return res


def calibration(t: pd.DataFrame) -> list:
    q = pd.qcut(t["M_risk"], 5, labels=False)
    return [{"fifth": int(i) + 1, "days": int((q == i).sum()), "mean_predicted": float(t["M_risk"][q == i].mean()),
             "observed_event_rate": float(t["event"][q == i].mean())} for i in range(5)]


def build(regions, frozen, models, p4) -> pd.DataFrame:
    fr, _ = model_frame(2025, regions)
    t = fr[fr.index.year >= 2022].copy()
    for role, col in (("primary", "M"), ("secondary", "M2")):
        pr = predict(t, models[role], frozen[role]["threshold_alert"], frozen[role]["threshold_high"])
        t[col], t[f"{col}_risk"], t[f"{col}_tier"] = pr["alert"], pr["risk"], pr["tier"]
    t["R4"] = r4_relative(t["h"], t["p"], t["a"], p4)
    t["R4_ord"] = r4_tier(t["h"], t["p"], t["a"], p4).map(TIER_ORDER)
    return t


def abu_dhabi(frozen, model) -> dict:
    """Descriptive only (no outcomes): share of May-Sep 2025 days the frozen model would alert on, per zone."""
    out = {}
    for z in ("mussafah", "adcity", "ruwais", "alain"):
        w = pd.read_csv(WEATHER_DIR / f"weather_ad_{z}.csv", parse_dates=["time"], index_col="time")
        s = pd.read_csv(WEATHER_DIR / f"sunwind_ad_{z}.csv", parse_dates=["time"], index_col="time")
        d = daily_weather_features(w.join(s, how="left"))
        d = d[(d.index.month >= SEASON[0]) & (d.index.month <= SEASON[1])].copy()
        d["p"] = percentile_rank(d["h"])
        d["spell"] = 0
        for pos in d.groupby(d.index.year).indices.values():
            d.iloc[pos, d.columns.get_loc("spell")] = spell_days(d["p"].iloc[pos]).to_numpy()
        doy = d.index.day_of_year.to_numpy()
        d["season_sin"], d["season_cos"] = np.sin(2 * np.pi * doy / 365.25), np.cos(2 * np.pi * doy / 365.25)
        d["weekend"] = (d.index.day_of_week >= 5).astype(float)
        risk = model.predict_proba(usable(d)[FEATURES])[:, 1]
        r = pd.Series(risk, index=usable(d).index)
        ref = r[(r.index.year >= 2015) & (r.index.year <= 2021)].median()
        y25 = r[r.index.year == 2025]
        out[z] = {"alert_share_2025": float((y25 >= frozen["primary"]["threshold_alert"]).mean()),
                  "high_share_2025": float((y25 >= frozen["primary"]["threshold_high"]).mean()),
                  "relative_risk_2025_median": float((y25 / ref).median()), "relative_risk_2025_max": float((y25 / ref).max())}
    return out


def main() -> None:
    frozen = json.loads((ROOT / "results" / "frozen_model_v4.json").read_text())
    with (ROOT / "results" / "frozen_model_v4.pkl").open("rb") as f:
        models = pickle.load(f)
    p4 = RelParams(**json.loads((ROOT / "results" / "frozen_params_r4.json").read_text())["params"])
    hold = holdout_regions()
    t = build(hold, frozen, models, p4)
    res = {"protocol": "docs/protocol_v4_trained_model.md", "frozen": {r: {k: frozen[r][k] for k in ("family", "cfg")} for r in ("primary", "secondary")}}
    res["holdout"] = score(t, {r.key: r.name for r in hold})
    res["holdout"]["calibration_M"] = calibration(t)
    A = res["holdout"]["primary_A_M_minus_R4_sensitivity"]["point"]
    sp = res["holdout"]["alert_share_spread"]
    res["deployment_criterion_met"] = bool(A >= 0 and sp["M"] <= sp["R4"] + 0.05)
    o = build(REGIONS, frozen, models, p4)
    res["original_regions_2022_2025"] = score(o, {r.key: r.name for r in REGIONS})
    res["abu_dhabi_descriptive"] = abu_dhabi(frozen, models["primary"])
    (ROOT / "results" / "model_v4_results.json").write_text(json.dumps(res, indent=2, default=float))
    h = res["holdout"]
    for k in ("M", "M2", "R4"):
        print(k, f"sens {h[k]['sensitivity']:.1%} {[round(x*100,1) for x in h[k]['sensitivity_95ci']]} alert {h[k]['alert_fraction']:.0%}")
    print("A", round(A * 100, 1), [round(x * 100, 1) for x in h["primary_A_M_minus_R4_sensitivity"]["95ci"]])
    print("B", {k: (round(v, 3) if isinstance(v, float) else [round(x, 3) for x in v]) for k, v in h["primary_B_auc"].items()})
    print("spread", {k: round(v * 100, 1) for k, v in sp.items()}, "criterion met:", res["deployment_criterion_met"])
    for n, v in h["per_region"].items():
        print(" ", n, {k: (v[k]["caught"], v[k]["event_days"], round(v[k]["alert_share"], 2)) for k in v})
    oo = res["original_regions_2022_2025"]
    print("original 2022-25:", {k: f"{oo[k]['sensitivity']:.1%} @ {oo[k]['alert_fraction']:.0%}" for k in ("M", "R4")})
    print("calibration:", [(c["fifth"], round(c["mean_predicted"], 3), round(c["observed_event_rate"], 3)) for c in h["calibration_M"]])
    print("Abu Dhabi:", json.dumps(res["abu_dhabi_descriptive"], default=lambda x: round(x, 2)))


if __name__ == "__main__":
    main()
