"""Protocol v4 trained risk model: logistic regression and monotonic gradient boosting, chosen by
leave-one-year-out log loss on 2015-2021 only."""
from __future__ import annotations

import itertools

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import log_loss
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from heatwarn.features import FEATURES, MONOTONIC_UP
from heatwarn.tune import TRAIN_LAST_YEAR, TrainingLeakError

SEED = 20261108
LR_GRID = [{"C": c} for c in (0.01, 0.1, 1, 10)]
GB_GRID = [dict(zip(("max_depth", "learning_rate", "max_iter", "min_samples_leaf"), v))
           for v in itertools.product((2, 3), (0.03, 0.1), (100, 300), (50, 200))]


def fit_lr(X: pd.DataFrame, y: pd.Series, cfg: dict):
    return make_pipeline(StandardScaler(), LogisticRegression(C=cfg["C"], max_iter=5000)).fit(X, y.astype(int))


def fit_gb(X: pd.DataFrame, y: pd.Series, cfg: dict):
    cst = [1 if f in MONOTONIC_UP else 0 for f in X.columns]
    return HistGradientBoostingClassifier(monotonic_cst=cst, early_stopping=False, random_state=SEED, **cfg).fit(X, y.astype(int))


FAMILIES = {"logistic": (fit_lr, LR_GRID), "boosting": (fit_gb, GB_GRID)}


def usable(frame: pd.DataFrame) -> pd.DataFrame:
    """Rows with every feature present (others are 'Insufficient data')."""
    return frame[frame[FEATURES].notna().all(axis=1)]


def cv_log_loss(frame: pd.DataFrame, fit, cfg: dict) -> float:
    years = sorted(set(frame.index.year))
    losses = []
    for y in years:
        tr, te = frame[frame.index.year != y], frame[frame.index.year == y]
        m = fit(tr[FEATURES], tr["event"], cfg)
        losses.append(log_loss(te["event"].astype(int), m.predict_proba(te[FEATURES])[:, 1], labels=[0, 1]))
    return float(np.mean(losses))


def select_and_fit(frame: pd.DataFrame) -> dict:
    if (frame.index.year > TRAIN_LAST_YEAR).any():
        raise TrainingLeakError("training frame contains test years (>= 2022)")
    fr = usable(frame)
    table = []
    for family, (fit, grid) in FAMILIES.items():
        for cfg in grid:
            table.append({"family": family, "cfg": cfg, "cv_log_loss": cv_log_loss(fr, fit, cfg)})
    best_by_family = {f: min((r for r in table if r["family"] == f), key=lambda r: r["cv_log_loss"]) for f in FAMILIES}
    primary = min(best_by_family.values(), key=lambda r: r["cv_log_loss"])
    secondary = next(r for f, r in best_by_family.items() if f != primary["family"])
    fitted = {r["family"]: FAMILIES[r["family"]][0](fr[FEATURES], fr["event"], r["cfg"]) for r in (primary, secondary)}
    return {"primary": primary, "secondary": secondary, "models": fitted, "cv_table": table, "train_rows": len(fr)}


def operating_threshold(scores: np.ndarray, n_alerts: int) -> float:
    """Risk threshold at which exactly n_alerts scores are >= it."""
    s = np.sort(np.asarray(scores))[::-1]
    t = s[n_alerts - 1]
    if n_alerts < len(s) and s[n_alerts] == t:
        raise ValueError("tied scores at the threshold; alert count cannot be matched exactly")
    return float(t)
