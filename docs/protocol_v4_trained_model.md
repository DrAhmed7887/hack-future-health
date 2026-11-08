# Protocol v4: trained risk model (pre-registration)

**Signed by Ahmed, 8 Nov 2026.** Nothing below has been fitted or scored. No sun or wind weather has been fetched
for any region. Once signed, this file, the feature code and the unit tests are committed before any model is fitted. The
fitted model is then frozen and committed before it is scored.

Reason: the frozen relative rule R4 (`docs/protocol_v3_relative.md`) is a threshold rule with three tuned cut-offs. Ahmed asked
(8 Nov) whether a trained model can predict better. No Gulf outcome data exists (`docs/data_search.md`), so the model learns
from the same US OSHA outcomes.

## What has already been seen (disclosure)
- All outcomes, 2015–2025, for the 8 original and 6 holdout regions, scored with R0–R4. We know R4 caught 79.1 % of holdout
  event days at a 49 % alert share. The model is new, but its authors are not blind to the holdout. This is mitigated by fixing
  every choice below before fitting, and by scoring once.
- Temperature and humidity (ERA5) for all regions. Sun and wind have not been fetched.

## Data
- **Unit:** region-day, May–September (the tested season), local time zone, as in v3.
- **Outcome:** at least one OSHA heat hospitalisation report (OIICS 531, 5310, 5311, 5312) assigned to the region that day.
  Same assignment rule (nearest centre within 100 km).
- **Training:** 8 original regions, 2015–2021 (8,568 days, 454 event days). Fitting refuses any row with year ≥ 2022.
- **Test:** 6 holdout regions, 2022–2025 (86 event days, already defined in `results/holdout_regions.json`). Secondary: the 8
  original regions, 2022–2025.

## Features (fixed; no region identity, so the model can be used in a new place)
All from ERA5 via Open-Meteo, using only that day's weather and the days before it:
1. H: daily maximum heat index (°F), as now.
2. P: local percentile of H (±15 days, 2015–2021 reference, own year left out in training), as in R4.
3. A: H minus the previous 14 days' mean, as in R4.
4. Night heat: the minimum heat index between 00:00 and 06:00 local time.
5. Spell: the number of consecutive previous days with P ≥ 60 (capped at 10).
6. Sun: the daily total of shortwave radiation (MJ/m²). New fetch.
7. Wind: the mean 10 m wind speed between 10:00 and 16:00 local time. New fetch.
8. Season: the day of year as a sine and cosine pair.
9. Weekend: Saturday or Sunday (fewer people work then, so there is less exposure).

Days with fewer than 18 valid hours are "Insufficient data", as now.

## Models
- **M-LR:** logistic regression, standardised features, L2 penalty, C ∈ {0.01, 0.1, 1, 10}.
- **M-GB:** gradient boosting (scikit-learn HistGradientBoostingClassifier). The predicted risk may only rise with H, P, A,
  night heat, spell and sun (monotonic constraints). Grid: max_depth {2, 3} × learning_rate {0.03, 0.1} × max_iter
  {100, 300} × min_samples_leaf {50, 200}.
- **Selection, training data only:** leave-one-year-out cross-validation over 2015–2021 (7 folds), by mean log loss. The
  single best configuration across both families becomes the **primary model M**. The other family's best is reported as
  secondary. Fixed random seed 20261108.
- **Operating point:** the risk threshold at which M alerts on exactly as many training days as R4 did (3,672 of 8,568). The
  two are then compared at the same alert load. The High tier threshold matches R4's training share of High days.

## Endpoints (scored once, holdout regions, 2022–2025)
1. **Primary A:** sensitivity of M minus sensitivity of frozen R4 (block bootstrap by region-season, 2,000 resamples, 95 % CI).
2. **Primary B:** discrimination, as the AUC of M's risk against the AUC of R4's ordered tiers (none < Elevated < High), with a
   bootstrap CI for the difference.
3. **Deployment criterion:** the app uses M in place of R4 only if Primary A's point estimate is ≥ 0 **and** M's alert-share
   spread across the 6 holdout regions is no more than 5 points wider than R4's. Otherwise the app keeps R4, and the README and
   film report the model as tested and not better.
4. **Secondary (descriptive):** calibration (observed vs predicted by fifth of risk), per-region results, alert-share spread,
   M on the original regions' 2022–2025, and the secondary model family.
5. **Day-ahead (secondary):** M from the evening-before forecast, 2024–2025, original regions, if the Previous Runs API archives
   sun and wind. If it doesn't, this is reported as not evaluable. Nothing is substituted.

## How the app would show it (only if the criterion is met)
"Relative risk": M's risk for tomorrow divided by the median risk of that zone's May–September 2015–2021 days, shown as "about
2× a typical summer day here", with the tier. It is labelled: trained on US outcome data, not validated on Abu Dhabi outcomes.
There is no absolute probability, because US reporting rates do not carry over to Abu Dhabi.

## Power warning (stated before running)
86 holdout event days. A sensitivity difference smaller than about 15 points will not be statistically clear. AUC intervals
will be wide.

## Expected results (written before running)
- M's sensitivity within ±5 points of R4's. Gradient boosting no better than logistic regression on cross-validated log loss.
- AUC for M about 0.70–0.80, slightly above R4's ordered tiers. Night heat and spell add a little, and sun and wind add little,
  because outcome timing is driven mostly by how unusual the heat is.

## Unit tests written before the code
- Every feature for day d uses only hourly data dated d or earlier (no future leakage).
- Fitting refuses any row with year ≥ 2022 (as `TrainingLeakError` does now).
- The percentile for a training day leaves its own year out.
- With monotonic constraints, raising H alone never lowers M's risk.
- The operating threshold reproduces R4's training alert count exactly (3,672).

## Sign-off
I approve this protocol, the feature list and the deployment criterion before any model is fitted.

Signed: Ahmed Zayed (in chat: "Yes, signed")   Date: 8 Nov 2026
