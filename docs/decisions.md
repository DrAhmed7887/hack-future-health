# Decisions log

- **7 Nov 2026, G0:** Challenge 06 (Population and Workforce Health Early Warning), solo. Idea: early heat warning for outdoor workers, with new/returning workers as a higher-risk group, back-tested on real heat hospitalisations (OSHA Severe Injury Reports 2015–Nov 2025) joined to ERA5 heat and archived forecasts, against a calendar rule and a fixed heat-index rule; runs live on Abu Dhabi forecasts. Chosen over a fully simulated back-test because simulated outcomes only test the generator. Ideas came from five independent models (Qwen, GPT-6 Sol, Gemini, Kimi, Muse Spark) with anonymous cross-review.
- **7 Nov 2026:** individual days-on-job cannot be validated on OSHA data (2 of 2,628 narratives mention it) → kept as a labelled guideline rule; a population-level relative-heat term is tested instead.
- **7 Nov 2026:** Abu Dhabi's official index is TWL; no verified algorithm and no globe temperature in weather data → shown as "not computed" until verified.
- Working name "HeatShield"; final name: Ahmed's call.
