# Protocol v4 results: trained risk model (scored once, 8 Nov 2026)

Frozen model: logistic regression, C = 0.1 (`results/frozen_model_v4.json`, commit 24ff54a), chosen over monotonic gradient
boosting by leave-one-year-out log loss on 2015-2021 (0.1795 vs 0.1806). Thresholds matched to R4's training alert count
(3,672 of 8,568 days). Scored once by `scripts/score_model.py` (committed before running, 6eb21ed). Output:
`results/model_v4_results.json`.

## Holdout: 6 unseen US regions, 2022-2025 (86 event days)
| | Caught (95 % CI) | Days alerted |
|---|---|---|
| Trained model (logistic) | 77.9 % (65.8-87.6) | 40 % |
| Trained model (boosting, secondary) | 76.7 % (66.2-85.3) | 40 % |
| Relative rule R4 (in the app) | 79.1 % (69.6-87.9) | 49 % |

- **Primary A, sensitivity M - R4: -1.2 points (95 % CI -13.9 to +10.8).** Not statistically clear either way.
- **Primary B, discrimination: AUC 0.727 for the model vs 0.657 for R4's tiers; difference +0.070 (95 % CI +0.013 to +0.129).**
  The model ranks days better.
- **Alert-share spread across the 6 regions: 76 points for the model (5 % Pittsburgh area to 81 % McAllen) vs 25 for R4.**
- **Deployment criterion (A >= 0 and spread no more than 5 points wider than R4's): NOT met** on both parts. The app keeps R4.

## Why
The model leans on absolute heat: standardised weights h 0.86, night heat 0.43, sun 0.33, wind -0.30, weekend -0.58, but
local percentile 0.01 and 14-day jump 0.02. So it behaves like a well-ranked fixed threshold: few alerts in cool places, many
in hot ones. In Abu Dhabi (descriptive, 2025, no outcomes) it would alert on **93-100 % of May-September days** in all four
zones, the same failure that led to the relative rule.

## Secondary (descriptive)
- Original 8 regions, 2022-2025 (outcomes already seen; exploratory): model 88.9 % at 52 % alert days vs R4 76.4 % at 53 %.
  Where it was trained, it is better.
- Calibration on the holdout: predicted vs observed event rate by fifth of risk: 0.2/0.4 %, 1.0/0.8 %, 2.7/1.5 %, 6.6/3.7 %,
  18.2/5.3 %. It over-predicts at the top (fewer reports per hot day in the holdout cities): another reason not to show
  absolute probabilities.
- Day-ahead (protocol endpoint 5): not run in this pass.
- Expected results written before running: "within ±5 points of R4" (it was: -1.2); "AUC about 0.70-0.80, slightly above R4"
  (it was: 0.73 vs 0.66); "boosting no better than logistic" (it was not). Not expected: the 76-point spread.

## What this means for the entry
A trained model learns that hot places have more heat hospitalisations, which is true and useless for Abu Dhabi, where every
summer day is hot. Ranking against each place's own climate (R4) is what transfers. This is now shown with a trained model,
not only a fixed threshold.
