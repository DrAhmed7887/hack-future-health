"""NWS heat index (Rothfusz regression with NWS adjustments; Steadman simple formula below ~80 °F).

Source: NWS Weather Prediction Center, "The Heat Index Equation" (wpc.ncep.noaa.gov/html/heatindex_equation.shtml).
Regression error is about ±1.3 °F. This is not WBGT and ignores sun and wind.
"""
from __future__ import annotations

import numpy as np


def c_to_f(c):
    return np.asarray(c, dtype=float) * 9.0 / 5.0 + 32.0


def heat_index_f(t_f, rh):
    """Heat index in °F from air temperature (°F) and relative humidity (%). Vectorised; NaN in -> NaN out."""
    t = np.asarray(t_f, dtype=float)
    r = np.asarray(rh, dtype=float)
    simple = 0.5 * (t + 61.0 + (t - 68.0) * 1.2 + r * 0.094)
    full = (-42.379 + 2.04901523 * t + 10.14333127 * r - 0.22475541 * t * r - 0.00683783 * t * t
            - 0.05481717 * r * r + 0.00122874 * t * t * r + 0.00085282 * t * r * r - 0.00000199 * t * t * r * r)
    low_rh = (r < 13) & (t >= 80) & (t <= 112)
    adj_low = ((13 - r) / 4) * np.sqrt(np.clip((17 - np.abs(t - 95.0)) / 17, 0, None))
    full = np.where(low_rh, full - adj_low, full)
    high_rh = (r > 85) & (t >= 80) & (t <= 87)
    full = np.where(high_rh, full + ((r - 85) / 10) * ((87 - t) / 5), full)
    out = np.where((simple + t) / 2 >= 80, full, simple)
    return out.item() if out.ndim == 0 else out
