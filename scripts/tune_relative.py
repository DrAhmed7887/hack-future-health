"""Tune relative rule R4 on the original 8 regions, 2015-2021 only; freeze to results/frozen_params_r4.json."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from heatwarn.data import build_frame  # noqa: E402
from heatwarn.metrics import confusion  # noqa: E402
from heatwarn.relative import tune_relative  # noqa: E402
from heatwarn.rules import r1_fixed  # noqa: E402
from heatwarn.tune import TRAIN_LAST_YEAR  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    frame, stats = build_frame(last_year=TRAIN_LAST_YEAR)
    r1_days = confusion(r1_fixed(frame["h"]), frame["event"])["alert_days"]
    out = tune_relative(frame, r1_alert_days=r1_days) | {"data": stats, "r1_train_alert_days": r1_days}
    (ROOT / "results" / "frozen_params_r4.json").write_text(json.dumps(out, indent=2, default=float))
    print(json.dumps(out, indent=2, default=float))


if __name__ == "__main__":
    main()
