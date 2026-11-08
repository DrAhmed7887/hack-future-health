"""Protocol v4: select the model by leave-one-year-out CV on 2015-2021 (8 original regions), fit, set the operating
thresholds, and FREEZE. Writes results/frozen_model_v4.json and results/frozen_model_v4.pkl. Reads no 2022+ rows."""
from __future__ import annotations

import json
import pickle
import sys
from pathlib import Path

import pandas as pd
import sklearn

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from heatwarn.data import WEATHER_DIR, build_frame  # noqa: E402
from heatwarn.features import FEATURES, add_model_features, daily_weather_features  # noqa: E402
from heatwarn.metrics import confusion  # noqa: E402
from heatwarn.model import SEED, operating_threshold, select_and_fit, usable  # noqa: E402
from heatwarn.regions import REGIONS  # noqa: E402
from heatwarn.relative import RelParams, r4_tier  # noqa: E402
from heatwarn.tune import TRAIN_LAST_YEAR  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]


def hourly(key: str, last_year: int) -> pd.DataFrame:
    w = pd.read_csv(WEATHER_DIR / f"weather_{key}.csv", parse_dates=["time"], index_col="time")
    s = pd.read_csv(WEATHER_DIR / f"sunwind_{key}.csv", parse_dates=["time"], index_col="time")
    h = w.join(s, how="left")
    return h[h.index.year <= last_year]


def model_frame(last_year: int, regions) -> tuple[pd.DataFrame, dict]:
    frame, stats = build_frame(last_year, regions=regions)
    extras = {r.key: daily_weather_features(hourly(r.key, last_year)) for r in regions}
    return add_model_features(frame, extras), stats


def main() -> None:
    fr, stats = model_frame(TRAIN_LAST_YEAR, REGIONS)
    r4 = json.loads((ROOT / "results" / "frozen_params_r4.json").read_text())
    p4 = RelParams(**r4["params"])
    n_alert = int(r4["train"]["alert_days"])
    n_high = int((r4_tier(fr["h"], fr["p"], fr["a"], p4) == "High").sum())
    sel = select_and_fit(fr)
    tr = usable(fr)
    out = {"protocol": "docs/protocol_v4_trained_model.md", "seed": SEED, "sklearn": sklearn.__version__, "features": FEATURES,
           "train": {"rows_all": len(fr), "rows_usable": len(tr), "event_days": int(tr["event"].sum()), "data": stats},
           "matched_to_r4": {"alert_days": n_alert, "high_days": n_high}, "cv_table": sel["cv_table"]}
    for role in ("primary", "secondary"):
        r = sel[role]
        m = sel["models"][r["family"]]
        risk = m.predict_proba(tr[FEATURES])[:, 1]
        t_alert, t_high = operating_threshold(risk, n_alert), operating_threshold(risk, n_high)
        c = confusion(pd.Series(risk >= t_alert, index=tr.index).astype("boolean"), tr["event"])
        out[role] = {"family": r["family"], "cfg": r["cfg"], "cv_log_loss": r["cv_log_loss"],
                     "threshold_alert": t_alert, "threshold_high": t_high, "train_in_sample": c}
        if r["family"] == "logistic":
            lr = m[-1]
            out[role]["standardised_coefficients"] = dict(zip(FEATURES, map(float, lr.coef_[0])))
    (ROOT / "results" / "frozen_model_v4.json").write_text(json.dumps(out, indent=2, default=float))
    with (ROOT / "results" / "frozen_model_v4.pkl").open("wb") as f:
        pickle.dump({"primary": sel["models"][sel["primary"]["family"]],
                     "secondary": sel["models"][sel["secondary"]["family"]]}, f)
    print(json.dumps({k: out[k] for k in ("train", "matched_to_r4")}, indent=1, default=float))
    for role in ("primary", "secondary"):
        o = out[role]
        print(role, o["family"], o["cfg"], f"cv log loss {o['cv_log_loss']:.4f}",
              f"train sens {o['train_in_sample']['sensitivity']:.1%} alerts {o['train_in_sample']['alert_days']}")
        if "standardised_coefficients" in o:
            print("  coef", {k: round(v, 3) for k, v in o["standardised_coefficients"].items()})


if __name__ == "__main__":
    main()
