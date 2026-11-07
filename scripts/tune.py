"""Step 1: tune on 2015-2021 only and freeze the operating points to results/frozen_params.json."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from heatwarn.data import build_frame  # noqa: E402
from heatwarn.tune import TRAIN_LAST_YEAR, tune  # noqa: E402

OUT = Path(__file__).resolve().parents[1] / "results"


def main() -> None:
    frame, stats = build_frame(last_year=TRAIN_LAST_YEAR)
    chosen = tune(frame)
    chosen["data"] = stats | {"region_days": len(frame), "years": [int(frame.index.year.min()), int(frame.index.year.max())]}
    OUT.mkdir(exist_ok=True)
    (OUT / "frozen_params.json").write_text(json.dumps(chosen, indent=2, default=float))
    print(json.dumps(chosen, indent=2, default=float))


if __name__ == "__main__":
    main()
