"""Operating-point selection on training years only (protocol v2)."""
from __future__ import annotations

import itertools

import pandas as pd

from heatwarn.metrics import confusion
from heatwarn.rules import Params, r1_fixed, r2_weather, r3_weather_workplace

TRAIN_LAST_YEAR = 2021
GRID_T_LOW = (80, 85, 90)
GRID_T_HIGH = (95, 100, 103)
GRID_A = (3, 5, 7, 9)
BUDGET_FRACTION = 0.5  # signed: alert days <= 50 % of R1's training alert days


class TrainingLeakError(ValueError):
    pass


def tune(frame: pd.DataFrame) -> dict:
    """frame: daily rows (DatetimeIndex) with columns region, h, a, w, event. Returns chosen Params for R2 and R3."""
    if (frame.index.year > TRAIN_LAST_YEAR).any():
        raise TrainingLeakError("tuning frame contains test years (>= 2022)")
    budget = BUDGET_FRACTION * confusion(r1_fixed(frame["h"]), frame["event"])["alert_days"]
    chosen = {}
    for name in ("r2", "r3"):
        best = None
        for t_low, t_high, a in itertools.product(GRID_T_LOW, GRID_T_HIGH, GRID_A):
            p = Params(t_low, t_high, a)
            alert = (r2_weather(frame["h"], frame["a"], p) if name == "r2"
                     else r3_weather_workplace(frame["h"], frame["a"], frame["w"], p))
            c = confusion(alert, frame["event"])
            if c["alert_days"] > budget:
                continue
            key = (c["sensitivity"], -c["alert_days"])
            if best is None or key > best[0]:
                best = (key, p, c)
        if best is None:
            raise RuntimeError(f"no grid point within budget for {name}")
        chosen[name] = {"params": best[1].__dict__, "train": best[2]}
    chosen["budget_alert_days"] = budget
    return chosen
