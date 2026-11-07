"""Confusion counts, alert episodes and region-season block bootstrap."""
from __future__ import annotations

import numpy as np
import pandas as pd


def confusion(alert: pd.Series, event: pd.Series) -> dict:
    ok = alert.notna()
    al, ev = alert[ok].astype(bool), event[ok].astype(bool)
    tp = int((al & ev).sum()); fp = int((al & ~ev).sum()); fn = int((~al & ev).sum()); tn = int((~al & ~ev).sum())
    return {
        "days": int(ok.sum()), "insufficient": int((~ok).sum()), "event_days": tp + fn, "alert_days": tp + fp,
        "tp": tp, "fp": fp, "fn": fn, "tn": tn,
        "sensitivity": tp / (tp + fn) if tp + fn else float("nan"),
        "reported_event_ppv": tp / (tp + fp) if tp + fp else float("nan"),
        "alert_fraction": (tp + fp) / ok.sum() if ok.sum() else float("nan"),
    }


def episodes(alert: pd.Series) -> tuple[int, int]:
    """Number of runs of consecutive alert days and the longest run (NA counts as no alert)."""
    a = alert.fillna(False).astype(bool).to_numpy()
    n = longest = run = 0
    for x in a:
        if x:
            run += 1
            if run == 1:
                n += 1
            longest = max(longest, run)
        else:
            run = 0
    return n, longest


def block_bootstrap(frame: pd.DataFrame, stat, reps: int = 2000, seed: int = 20261107) -> tuple[float, float]:
    """95 % percentile interval of stat(frame) resampling whole (region, season) blocks with replacement."""
    rng = np.random.default_rng(seed)
    # positional indices: dates repeat across regions, so label lookups would mix regions
    blocks = list(frame.groupby(["region", frame.index.year]).indices.values())
    vals = []
    for _ in range(reps):
        pick = rng.integers(0, len(blocks), len(blocks))
        sample = frame.iloc[np.concatenate([blocks[i] for i in pick])]
        v = stat(sample)
        if not np.isnan(v):
            vals.append(v)
    return float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))
