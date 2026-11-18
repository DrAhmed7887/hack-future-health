# Evidence pack v3: dust / PM10 signal and baseline-deviation (EARS C2) signal

Compiled 17 Nov 2026. Project: Heat Shift Planner (Abu Dhabi outdoor-worker heat early warning, static web app).
Status: D1–D6 and E1–E6 **signed by Ahmed Zayed, 18 Nov 2026** (in chat: "Sign as proposed"; the more cautious D3-alt pair was not chosen). Built in v4: `heatwarn/dust.py`, `web/health.js`, `web/alerts.js`. Signed means the physician accepts the rules for the demo; they are still not tested on outcomes.

Reading guide
- Each bullet: claim, exact quote or number, source, verified (yes / partial / no).
- "verified yes" = I opened the primary document (or an official copy) in this session and copied the quote. "partial" = the number reached me only through a secondary document, a news report, or an abstract without the formula. "NOT VERIFIED" = I could not confirm it; nothing is guessed.
- My own arithmetic is labelled "computed here".
- Sources opened this session (scratch, not in repo): WHO Global Air Quality Guidelines 2021 PDF (WHO IRIS, 9789240034228); UAE Cabinet Decree 12 of 2006 PDF (FAOLEX copy, page 63 read as an image); NCM "Emirati Air Quality Index" guideline PDF (2023); Open-Meteo docs, terms and licence pages; PubMed records via NCBI E-utilities; two arXiv/JBMS papers describing EARS.

---

## 1. Topic 1: air quality / desert dust

### 1.1 Data source: Open-Meteo Air Quality API (CAMS)
Source for all of 1.1: https://open-meteo.com/en/docs/air-quality-api (fetched 17 Nov 2026), https://open-meteo.com/en/terms, https://open-meteo.com/en/licence, plus one live API call (computed here).

- Variables — hourly "Particulates: PM10 and PM2.5, in μg/m³"; "Aerosols and dust: aerosol optical depth is dimensionless. Dust is in μg/m³." (docs table, as rendered by the page fetch). Live call for Abu Dhabi (24.47, 54.37) with `hourly=pm10,pm2_5,dust` returned `hourly_units` `pm10: μg/m³`, `pm2_5: μg/m³`, `dust: μg/m³`. — verified yes
- Forecast horizon — docs: five days by default, extendable to seven with `forecast_days` (0–7); `past_days` 0–92. Live call with `forecast_days=7` (17 Nov 2026) returned 168 hourly slots to 23 Nov 23:00 but only 125 non-null values per variable (computed here: about 5.2 days). So the usable horizon over Abu Dhabi is about 5 days, not 7; treat nulls as "no data". — verified yes
- Model behind it — docs: "CAMS European Air Quality Forecast: 0.1° (~11 km), hourly, 4 days, updated every 24 hours" and "CAMS Global Atmospheric Composition Forecasts: 0.4° (~45 km), 3-hourly, 5 days, updated every 12 hours" (docs, as summarised by the page fetch). Abu Dhabi is outside the European domain, so it is served by the global product (my inference from the live 5.2-day horizon; not stated by Open-Meteo for this location). — partial
- Free without key — docs: the `apikey` parameter is "Only required to commercial use to access reserved API resources for customers." Terms: "Less than 10'000 API calls per day, 5'000 per hour and 600 per minute." Non-commercial examples: "Private or non-profit websites or apps that do not have subscriptions or advertising." Commercial: "Websites or apps that have subscriptions or display advertisements." — verified yes
- Licence — licence page: "API data are offered under Attribution 4.0 International (CC BY 4.0)"; "You must give appropriate credit, provide a link to the licence, and indicate if changes were made"; "You must include a link next to any location Open-Meteo data are displayed, for example: <a href="https://open-meteo.com/">Weather data by Open-Meteo.com</a>" (link text as printed on the page; check exact markup before shipping). — verified yes
- Air-quality attribution — docs: "All users of Open-Meteo data must provide a clear attribution to [CAMS ENSEMBLE data provider] as well as a reference to Open-Meteo." with a long citation ending "(2022): CAMS European air quality forecasts, ENSEMBLE data. Copernicus Atmosphere Monitoring Service (CAMS) Atmosphere Data Store (ADS). (Updated twice daily)." (that citation is the European product; the global product's own CAMS citation was NOT VERIFIED). — partial
- How accurate CAMS forecast PM10 is over Abu Dhabi against EAD monitors: NOT VERIFIED. No validation was found or run. The thresholds below are applied to a model forecast, not a monitor reading.

### 1.2 WHO Global Air Quality Guidelines 2021
Source: WHO (2021). WHO global air quality guidelines: particulate matter (PM2.5 and PM10), ozone, nitrogen dioxide, sulfur dioxide and carbon monoxide. ISBN 978-92-4-003422-8. https://www.who.int/publications/i/item/9789240034228 ; PDF https://iris.who.int/server/api/core/bitstreams/551b515e-2a32-4e1a-a58c-cdaecd395b19/content (opened, text-extracted).

Table 0.1 "Recommended AQG levels and interim targets" (24-hour rows, µg/m³):

| Pollutant | Averaging time | IT-1 | IT-2 | IT-3 | IT-4 | AQG level |
|---|---|---|---|---|---|---|
| PM2.5 | 24-hour^a | 75 | 50 | 37.5 | 25 | 15 |
| PM10 | 24-hour^a | 150 | 100 | 75 | 50 | 45 |

Footnote printed in the table: "a 99th percentile (i.e. 34 exceedance days per year)." — verified yes (Table 0.1, p. xvii)

- Dust is a named topic — "Table 0.3. Summary of good practice statements" row SDS, statement 1: "Maintain suitable air quality management and dust forecasting programmes. These should include early warning systems and short-term air pollution action plans to alert the population to stay indoors and take personal measures to minimize exposure and subsequent short-term health effects during SDS incidents with high levels of PM." (SDS = sand and dust storms). — verified yes
- SDS statement 2 — "Maintain suitable air quality monitoring programmes and reporting procedures, including source apportionment activities to quantify and characterize PM composition and the percentage contribution of SDS to the overall ambient concentration of PM." — verified yes
- Dust raises PM10 and PM2.5 — Section 4.4: "desert dust events have coincided with substantial increases in measured concentrations of both the PM10 and PM2.5 size fractions." — verified yes
- No numeric dust level — the SDS statements give no concentration at which to act ("incidents with high levels of PM" is undefined). The WHO 24-hour values apply to PM from all sources; WHO does not set a separate dust-day level. (Absence confirmed by reading section 4.4 and Table 0.3; I did not read every page of the 300-page document.) — partial
- Evidence on dust health effects is mixed — Section 4.4: the systematic review "summarized the evidence from 93 studies conducted worldwide. The studies indicate an overall effect of desert dust on cardiovascular mortality and respiratory morbidity, but the evidence is still inconsistent when accounting for sources of PM in different geographical areas". And: "The summary of the evidence of the systematic review on desert dust indicated inconsistent results". — verified yes

### 1.3 UAE national ambient standard for PM10
- Federal standard — UAE Cabinet Decree (12) of 2006, "Regulation Concerning Protection of Air from Pollution", Annex (8) "Ambient Air Quality Standards (Air Pollutants Limits in the Ambient Air)", table row: "Particulate Matter (with 10 microns or less in diameter) | PM10 | 150 | 24 hour", units "µg/Nm3". Same table also lists "Total Suspended Particles TSP 230 (24 hour), 90 (1 year)". There is no PM2.5 row and no annual PM10 row. Note 3: "'Nm3' means normal cubic meter, being that amount of gas which when dry, occupies a cubic meter at a temperature of 25 degrees Centigrade and at an absolute pressure of 760 millimeters of mercury (1 atm)." — verified yes (read from the page image, p. 63 of the FAOLEX English PDF https://faolex.fao.org/docs/pdf/uae185024E.pdf; text also listed at https://leap.unep.org/en/countries/ae/national-legislation/cabinet-decree-no12-2006-concerning-protection-air-pollution, dated 1 May 2006, "Repealed: No", "Legislation Amendment: No")
- Federal AQI confirms it and PM2.5 gap — NCM, "Guideline for calculating the Emirati Air Quality Index (EAQI)", 2023 (https://airquality.ncm.gov.ae/resources/pdf/aqi-quickguide-en-2023.pdf): "PM2.5 ambient air quality standard is not currently included in the cabinet decree 12 of 2006, but given the health concerns related to PM2.5 exposure a reference value is included in this Guideline." Annex: "For all pollutants, the upper/higher breakpoint in the 'Moderate' category corresponds to the National Ambient Air Quality Standards." and "For PM10, evidence indicates that acute health effects occur after pollution episodes lasting at least 24 hours, therefore the averaging period should be 24 hours (rolling average)." — verified yes
- EAQI PM10 24-hour breakpoints, Table 2 (µg/Nm3): sub-index 50: 0–75; 100: >75–150; 150: >150–250; 200: >250–350; 300: >350–420; 500: >420–600. Category names (Table 1): 0–50 Good; 51–100 Moderate; 101–150 Unhealthy for sensitive groups; 151–200 Unhealthy ("Greater proportion of the public may be affected"); 201–300 Very unhealthy ("Everyone may experience health effects"); 301–500 Hazardous. EAQI Annex on "Very unhealthy": "It is at this level when health alerts are triggered." — verified yes. So the national PM10 standard (150) equals the top of "Moderate", and PM10 above 250 µg/Nm3 is in the "Unhealthy" band (index 151–200 starts at >250).
- EAQI PM2.5 24-hour breakpoints: Good 0–50, Moderate >50–60, USG >60–75, Unhealthy >75–150. These are a "proposed ambient standard", not law. — verified yes (the 60 and 75 are the NCM reference values; the Annex says the Good limit corresponds to WHO IT-2 and the USG upper limit to WHO IT-1, matching the WHO table above)
- Abu Dhabi EAD-specific PM10 limit: NOT VERIFIED. A web search returned a World Bank box saying the emirate's standards are based on US EPA guidelines and a 2009 NILU report with a table I could not read; I did not open the EAD site (adairquality.ae). Do not claim an EAD number. The federal 150 µg/Nm3 is the number I can quote.
- Cabinet Resolution No. 86 of 2023 (air quality measurements) — mentioned by secondary summaries only; I did not verify that it sets or changes any limit. NOT VERIFIED.

### 1.4 Official UAE / Abu Dhabi guidance for outdoor work during dust
Honest result: I found no official UAE or Abu Dhabi document that tells employers what to do about dust for outdoor workers specifically. What exists is general adverse-weather employer guidance and public health advice. ADPHC and NCEM dust guidance for workers: NOT VERIFIED (nothing found; the MoHRE website refused my connection from this machine, so MoHRE's own pages were read only through press copies).

- MoHRE, general adverse weather (not dust-specific) — Gulf News, 24 Mar 2026, "UAE urges firms to protect workers as unstable weather hits": MoHRE urges employers to "strengthen workplace safety measures and take preventive steps to protect workers"; "Companies were advised to take necessary precautions, introduce remote or flexible working arrangements where required,"; "ensure the availability of personal protective equipment, safe transportation arrangements and appropriate workplace conditions." The page does not mention dust. https://gulfnews.com/uae/government/uae-urges-firms-to-protect-workers-as-unstable-weather-hits-1.500484290 — partial (secondary press report of an official notice; dust not mentioned)
- Abu Dhabi workplace directives for rough weather — Gulf News (last updated 23 Dec 2024): "Abu Dhabi authorities have issued directives for the workplace during rough weather", sent to "private sector companies in the construction, contracting, and infrastructure development sectors"; items include "Stop outdoor work during thunder storms.", "Review outdoor work and work at heights when wind speeds exceed 38km/h.", "Provide high-visibility clothing for outdoor workers." The issuing agency is not named in the article and dust is not mentioned. https://gulfnews.com/amp/uae/weather/abu-dhabi-issues-workplace-directives-for-rough-weather-1.104976696 — partial
- ADPHC public dust-storm alert — The National (dated 14 Aug 2022, first published 19 May 2022), quoting an ADPHC WhatsApp alert: "exposure to sand and dust could be harmful to all." and "there are certain groups of people who are more susceptible to such harm caused by sandstorms"; ADPHC "advised staying home during sandstorms and closing windows" and applying "a little amount of non-perfumed Vaseline inside the nostrils to avoid dry mucosa". At-risk groups listed by the article as ADPHC's: chronic respiratory disease (asthma, COPD), infants, children, the elderly, heart disease, rhinitis, sinusitis, conjunctivitis. No mask advice and no mention of outdoor workers in the ADPHC text. https://thenationalnews.com/uae/health/2022/05/19/sandstorms-in-the-uae-how-do-i-stay-safe-and-who-is-at-risk — partial (press quote of an official message)
- MoHAP public dust advice — Khaleej Times, 14 Aug 2022: the Ministry of Health and Prevention's three tips: "Stay inside and avoid open spaces."; "In case of asthma, use bronchodilator sprays as directed by your doctor."; "Wear a mask or damp cloth." The article does not mention workers. A physician quoted there says the "best option" is an N95 mask: that is a doctor's view, not official guidance. https://khaleejtimes.com/uae/mask-up-uae-ministry-issues-3-tips-to-protect-health-as-dust-storm-engulfs-country?amp=1 — partial
- Al Dhafra Municipality, 13 Mar 2021 (after an NCM dust warning) — "Follow weather forecast announcements from official sources and avoid exposure to dust and dirt particles." (as quoted by Khaleej Times; the article does not mention workers or masks). https://www.khaleejtimes.com/uae/weather/uae-dust-storm-authority-issues-tips-to-stay-safe?amp=1 — partial
- No official source I found gives a PM10 value at which outdoor work must stop, or specifies a respirator type for outdoor workers in dust. NOT VERIFIED.

### 1.5 Peer-reviewed papers (PubMed, via NCBI E-utilities)
- PMID 22819885 — Thalib L, Al-Taiar A. "Dust storms and the risk of asthma admissions to hospitals in Kuwait." Sci Total Environ 2012;433:347-51. doi:10.1016/j.scitotenv.2012.06.082. Quote: "Dust storm days were defined as the mean daily PM(10)>200 μg/m(3) based on measurements obtained from all six monitoring sites in the country." and "569 (33.6%) days had dust storm events and they were significantly associated with an increased risk of same-day asthma and respiratory admission, adjusted relative risk of 1.07 (95% CI: 1.02-1.12) and 1.06 (95% CI: 1.04-1.08), respectively. This was particularly evident among children." — verified yes (abstract)
- PMID 23329278 — Al-Taiar A, Thalib L. "Short-term effect of dust storms on the risk of mortality due to respiratory, cardiovascular and all-causes in Kuwait." Int J Biometeorol 2014;58(1):69-77. Quote: "Dust storm days were identified when the national daily average of PM10 exceeded 200 μg/m(3)." and "Overall our findings suggest that local dust, that most likely originates from crustal materials, has little impact on short-term respiratory, cardiovascular or all-cause mortality." (a null result: report it alongside the positive one) — verified yes (abstract)
- PMID 39889591 — Tobías A, et al. "Short-term exposure to desert dust and sandstorms and all-cause and cause-specific mortality and morbidity: A systematic review and meta-analysis." Environ Int 2025;196:109277. doi:10.1016/j.envint.2025.109277. Quote: "Most studies focused on Asian and African desert dust, with fewer studies from Arabian, American, and Australian regions."; "The risk also increased for cardiovascular (RR = 1.0094, 95 % CI = [1.0014, 1.0174]) and respiratory morbidity (RR = 1.0693, 95 % CI = [1.0188, 1.1224])."; conclusion "Exposure to desert dust and sandstorms is linked to increased risks of all-cause and cardiovascular mortality, as well as respiratory morbidity. The overall evidence quality for each exposure-outcome combination was assessed as moderate". — verified yes (abstract)
- Not found: a peer-reviewed study linking dust or PM10 to health outcomes in outdoor workers in the Gulf. My PubMed searches returned only population studies. NOT VERIFIED that such a study exists; I did not search exhaustively.

### 1.6 PROPOSAL (needs Dr Zayed's sign-off): two-level dust alert
Not tested on outcomes. Thresholds are borrowed from regulatory and public-health sources, not derived from worker injury or illness data. The signal is a model forecast (CAMS via Open-Meteo), whose accuracy over Abu Dhabi is unvalidated here.

Metric: forecast daily mean PM10 (µg/m³), the mean of the 24 hourly `pm10` values of the local (Asia/Dubai) day, requiring at least 18 non-null hours (the 18-of-24 validity rule is the EAQI's own rule for 24-hour averages, NCM 2023, section VI). Averaging time matches the standard's "24 hour". Do not alert on the hourly `dust` series: I found no sourced threshold for it.

| Level | Rule | Source of number |
|---|---|---|
| Dust: elevated | daily mean PM10 > 150 µg/m³ | UAE Cabinet Decree 12/2006 Annex 8: PM10 150 µg/Nm3, 24 hour. Same value as WHO IT-1 (150) and the top of the EAQI "Moderate" band |
| Dust: high | daily mean PM10 > 250 µg/m³ | EAQI Table 2: PM10 >250 starts the "Unhealthy" category (index 151–200, "Greater proportion of the public may be affected"). Cross-check: Kuwait studies define a dust-storm day as mean daily PM10 > 200 (PMIDs 22819885, 23329278), so 250 sits above a peer-reviewed storm-day definition |

Alternative for the physician to choose instead (sourced, more cautious): elevated at > 100 (WHO IT-2) and high at > 200 (Kuwait storm-day definition, PMID 22819885). Not recommended as the default, because 100 is not a UAE legal level.

Supervisor actions (text shown in the app; each must keep its source):

| Level | Action | Source |
|---|---|---|
| elevated | "Check official weather and dust announcements before shift start." | Al Dhafra Municipality via Khaleej Times, 13 Mar 2021 ("Follow weather forecast announcements from official sources and avoid exposure to dust and dirt particles.") |
| elevated | "Ask workers with asthma, COPD, heart disease, rhinitis, sinusitis or conjunctivitis to report symptoms; reduce their time outdoors." | ADPHC alert via The National, 2022 (at-risk groups). Wording "reduce their time outdoors" is mine, derived from "advised staying home during sandstorms" |
| elevated | "Mask or damp cloth available." | MoHAP via Khaleej Times, 14 Aug 2022 ("Wear a mask or damp cloth."). This is public advice, not a workplace standard |
| high | "Review outdoor tasks; move work indoors or to flexible hours where possible." | MoHRE via Gulf News, 24 Mar 2026 ("introduce remote or flexible working arrangements where required"; "ensure the availability of personal protective equipment"); MoHAP ("Stay inside and avoid open spaces"); WHO GPS 1 ("short-term air pollution action plans to alert the population to stay indoors and take personal measures to minimize exposure") |
| high | "Follow the emirate's weather directives if issued (for example the wind-speed review of outdoor work)." | Abu Dhabi workplace directives via Gulf News, Dec 2024 ("Review outdoor work and work at heights when wind speeds exceed 38km/h.") |

Explicit limits to show to the user: no source gives a PM10 number at which work must stop; no official respirator specification for outdoor dust exposure was found (N95 only appears as a physician's opinion); the app must not say "stop work" as an official rule, only "review" and "consider".

---

## 2. Topic 2: baseline-deviation (cluster) detection, EARS C2

### 2.1 Primary sources and what I could and could not read
- PMID 12791783 — Hutwagner L, Thompson W, Seeman GM, Treadwell T. "The bioterrorism preparedness and response Early Aberration Reporting System (EARS)." J Urban Health 2003;80(2 Suppl 1):i89-96. doi:10.1007/pl00022319. PMCID PMC3456557. Abstract quote: "The primary purpose of EARS is to provide national, state, and local health departments with several alternative aberration detection methods." and "EARS allows end users to select validated aberration detection methods and modify sensitivity and specificity thresholds". The abstract has no formulas. The full text is on PMC but PMC blocked my automated download; I did not read it. So the C1/C2/C3 definitions below are NOT taken from Hutwagner's text. — abstract verified yes; definitions in that paper NOT VERIFIED
- PMID 18240128 — Fricker RD Jr, Hegler BL, Dunfee DA. "Comparing syndromic surveillance detection methods: EARS' versus a CUSUM-based methodology." Stat Med 2008;27(17):3407-29. doi:10.1002/sim.3197. Abstract quote: "This paper compares the performance of three detection methods, entitled C1, C2, and C3, that are implemented in the early aberration reporting system (EARS) and other syndromic surveillance systems versus the CUSUM applied to model-based prediction errors. The cumulative sum (CUSUM) performed significantly better than the EARS' methods across all of the scenarios we evaluated." and "This leads us to recommend replacing the C1, C2, and C3 methods in existing syndromic surveillance systems with an appropriately implemented CUSUM method." Full text not accessible; formulas not read. — abstract verified yes; definitions in that paper NOT VERIFIED

### 2.2 Definitions as stated in open secondary sources (verified text, partial provenance)
Because the two primary full texts were not accessible, the definitions come from three open papers that describe EARS. Each quote is verbatim from the PDF I downloaded. Ahmed or a clinician reviewer should check them against Hutwagner 2003 / Fricker 2008 before the claims go in a public write-up.

- C1 (baseline, statistic) — Salmon M, Schumacher D, Höhle M. "Monitoring Count Time Series in R: Aberration Detection in Public Health Surveillance." J Stat Softw 2016 (preprint https://arxiv.org/abs/1411.1292), describing the `earsC` function "as described in Fricker, Hegler, and Dunfee (2008)": "Here we shall expand on C1 for which the baseline are the 7 timepoints before the assessed timepoint t0, that is to say (y_t0−7, ..., y_t0−1). The expected value is the mean of the baseline. The method is based on a statistic called C_t0 defined as C_t0 = (y_t0 − ȳ_t0)/s_t0", with ȳ the baseline mean and s² the unbiased (n−1) variance; "An alarm is raised if y_t0 > U_t0" where "U_t0 = ȳ_t0 + z_{1−α} s_t0". — verified yes (text), primary-by-proxy
- The "3 standard deviations" threshold — Allévius B, Höhle M. "Prospective Detection of Outbreaks" (preprint of a chapter in the Handbook of Infectious Disease Data Analysis; https://arxiv.org/abs/1711.08960), section 0.2.1: "In its simplest form, the baseline is formed by the last k = 7 timepoints before the assessed timepoint t"; "The threshold for an extreme observation, under the assumption of no outbreak, is now defined as U_t = ȳ_t + 3 · s_t. Consequently, an alarm is raised if the current observation y_t exceeds this upper limit." — verified yes (text)
- C2 (guard band and statistic) — Collier N. "What's unusual in online disease outbreak news?" J Biomed Semantics 2010;1:2. PMID 20618980. https://arxiv.org/abs/1110.3091. Quote: "The test statistic for the Early Aberration Reporting System (EARS) C2 algorithm [19] is calculated using a 7 day sliding window baseline with a 2 day guard on the target day t being assessed. The target value was calculated as: S_t = max(0, (C_t − (μ_t + k s_t)) / s_t) where C_t is the count on the target day, k is a constant, set in our simulations to 1, and μ_t and s_t are the mean and standard deviation of the counts during a series of past time instants which we refer to as the baseline window. S_t captures the number (k) of standard deviations that the count exceeds the baseline mean, defaulting to 0 if it does not exceed the baseline mean." Figure 2 caption: "a 7 day test period (days -3 to -9) as background data, days -1 to -2 as a buffer period and day 0 'test day' as the test period." (so the baseline is days t−9 to t−3). Reference [19] in that paper is the EARS literature; which paper it is I did not check. — verified yes (text), partial provenance
- C3 — same paper: "C3 [19] is based on a modified version of the Cumulative Summation (CUSUM) algorithm. ... C3 uses only the two previous observations and is calculated in a similar manner to C2 except that it is the sum of S_t + S_t-1 + S_t-2. S_t-1 and S_t-2 are added if the counts on those days do not exceed the threshold of 3 standard deviations plus the mean on those days. C3 is designed to extend the sensitivity of C2 and will generate an alert at least as often as C2." — verified yes (text), partial provenance
- Convention difference to flag — Salmon et al. describe C1 as baseline t−7..t−1 with no guard band; Collier describes C2 as baseline t−9..t−3 with a 2-day guard. The two agree with the usual description (C1 no gap; C2 two-day gap); I did not see Hutwagner's or Fricker's own statement of it. The threshold in the original EARS software (3 SD for C1/C2, with C3's own cut-off) is NOT VERIFIED from a primary text; the "3" above is from Allévius & Höhle and the C3 sentence in Collier.

### 2.3 Known weaknesses (quotes)
- Small counts — Allévius & Höhle: "the distributional N(0, 1) assumption is likely to be inaccurate in case of counts below 5-10, because the distribution is discrete, non-negative and hence right-skewed." — verified yes
- False alarms are higher than the "3 sigma" label suggests — same source: "when k = 7 the α corresponding to a multiplication factor of 3 is not α = 1 − Φ(3) = 0.0013, as one might think, but α = 1 − F(3/√(1+1/k)) = 0.0155 ... In other words, using a factor of 3 means that the probability of false discoveries is notably higher than one might naively expect." (0.0155 is about 1 false alarm per 65 days per zone under their assumptions: computed here.) — verified yes
- Short memory — Salmon et al.: "The EARS methods C1, C2 and C3 are simple in that they only use information from the very recent past. ... ignoring an increasing time trend could decrease sensitivity. Inversely, overlooking an annual surge in counts during the summer could decrease specificity." and "the EARS methods do not compute a proper prediction interval for the current count." — verified yes
- Division by zero on sparse data — Collier: "Due to data sparseness we were in constant danger with standard deviation of division by zero so we implemented a minimum value for all models, finding an optimal level of F1 at a standard deviation value of 0.2. ... For example with the threshold optimized and a zero count background for all 7 days, an alert is generated for C2 when the current daily count is 3 or more." (tuned on news-article counts, not ED visits: do not carry 0.2 over as a clinical number). — verified yes
- Performance versus alternatives — Fricker 2008 abstract (2.1): CUSUM on model-based prediction errors "performed significantly better than the EARS' methods across all of the scenarios we evaluated". — verified yes (abstract)
- Seasonality matters here: Abu Dhabi heat-illness counts rise steeply from spring to summer. A 7-day window adapts to a slow rise, so it will under-alert during a ramp, and a count that jumps from 1 to 4 will alert easily. Both are consequences of the quotes above, not separate findings.

### 2.4 PROPOSAL (needs Dr Zayed's sign-off): C2 on simulated daily heat-illness ED visits per zone
Applies only to the simulated signal in the app. Not tested on real ED data; no real data are used. Not clinical surveillance.

| Item | Proposed value | Source / basis |
|---|---|---|
| Unit | daily count of simulated ED heat-illness visits, per zone, one series per zone | project design |
| Baseline window | 7 days, t−9 to t−3 | Collier 2010 (7-day baseline) and its Fig. 2 (days −3 to −9) |
| Guard band | 2 days (t−2, t−1 excluded) | Collier 2010 ("2 day guard") |
| Statistic | S_t = (y_t − μ_t) / max(s_t, s_min) | Salmon 2016 form C_t = (y − ȳ)/s with unbiased s; floor from Collier's minimum SD idea |
| Alert if | y_t > μ_t + 3 · max(s_t, s_min) (i.e. S_t > 3) | Allévius & Höhle: "U_t = ȳ_t + 3 · s_t" |
| s_min (floor) | 1.0 visit | PROPOSAL: judgement only. Collier used 0.2 on a different kind of count and said it was tuned; no ED-based source. With a zero background, 3 · 1.0 = 3, so an alert needs y_t > 3 i.e. at least 4 visits |
| Minimum count | y_t ≥ 3 visits in the zone on that day | PROPOSAL: judgement only, informed by Collier's remark that a C2 alert occurred "when the current daily count is 3 or more" on a zero background. Guards against alerting on 1 or 2 visits |
| Missing data | no alert if fewer than 7 baseline days are available | PROPOSAL |
| Variant | C2 only (not C3) | simplest; C3 "will generate an alert at least as often as C2" (Collier), more false alarms |

Alert text (shown to supervisors): "Signal: [zone] logged [y] simulated heat-illness ED visits today against about [μ, 1 decimal] expected from the earlier 7-day baseline (2-day gap). This is a statistical flag on simulated data, not a confirmed cluster. Review conditions in the zone." Do not use the words "outbreak" or "confirmed".

State in the UI and in the write-up: false-alarm rate per zone-day is about 1.6% by the Allévius & Höhle calculation for a normal model with k = 7; for low counts, no number was verified. The project should report the false-alarm rate it measures on its own simulation instead of quoting the 1.6%.

---

## 3. What was not verified (summary)
- Hutwagner 2003 and Fricker 2008 full text (PMC blocked automated access); EARS definitions come from three open secondary papers.
- EAD (Abu Dhabi) own PM10 limit; any amendment to the 2006 federal annex.
- Any ADPHC, NCEM or MoHRE dust-specific guidance for outdoor workers; any official mask/respirator specification; any PM10 level at which work should stop.
- CAMS global-product citation text; CAMS forecast accuracy over Abu Dhabi.
- Any peer-reviewed study of dust or PM10 in Gulf outdoor workers.
- MoHRE pages themselves (connection refused); MoHRE content is from press copies.

## 4. For sign-off

| # | Proposed rule | Source | Exact number | Signed (Ahmed) |
|---|---|---|---|---|
| D1 | Dust metric = daily mean of hourly forecast PM10, local day, at least 18 valid hours | UAE EAQI guideline NCM 2023 (24 h rolling average; 18 of 24 valid hours) | 24 h; 18 h minimum | Signed, 18 Nov 2026 |
| D2 | "Dust: elevated" when daily mean PM10 exceeds the UAE standard | UAE Cabinet Decree 12/2006 Annex 8 (= WHO IT-1 24 h PM10) | > 150 µg/m³ | Signed, 18 Nov 2026 |
| D3 | "Dust: high" when daily mean PM10 reaches the EAQI "Unhealthy" band | NCM EAQI 2023 Table 2 (PM10 index 151–200 starts above 250); cross-check Kuwait storm-day 200 (PMID 22819885) | > 250 µg/m³ | Signed, 18 Nov 2026 |
| D3-alt | More cautious pair: elevated > 100 (WHO IT-2), high > 200 (Kuwait storm-day definition) | WHO 2021 Table 0.1; PMID 22819885 | 100 / 200 µg/m³ | not chosen |
| D4 | Elevated actions: check official announcements; flag sensitive workers; mask or damp cloth available | Al Dhafra Municipality 2021; ADPHC 2022; MoHAP 2022 (all via press) | no number | Signed, 18 Nov 2026 |
| D5 | High actions: review outdoor tasks, flexible hours or indoor work where possible; follow emirate directives | MoHRE 24 Mar 2026; MoHAP; WHO GPS 1; Abu Dhabi directives Dec 2024 (via press) | no number | Signed, 18 Nov 2026 |
| D6 | App never states "stop work" as an official dust rule | no official source found | none | Signed, 18 Nov 2026 |
| E1 | EARS C2 baseline window | Collier 2010 (7-day sliding window baseline); Allévius & Höhle (k = 7) | 7 days (t−9 to t−3) | Signed, 18 Nov 2026 |
| E2 | Guard band | Collier 2010 | 2 days | Signed, 18 Nov 2026 |
| E3 | Alert threshold | Allévius & Höhle (U = ȳ + 3 s) | mean + 3 SD (S_t > 3) | Signed, 18 Nov 2026 |
| E4 | SD floor (division by zero guard) | PROPOSAL, judgement (Collier used 0.2 on a different data type) | 1.0 visit | Signed, 18 Nov 2026 |
| E5 | Minimum count to alert | PROPOSAL, judgement (informed by Collier "3 or more") | 3 visits | Signed, 18 Nov 2026 |
| E6 | Alert wording says "statistical flag on simulated data", no "outbreak" | project design | n/a | Signed, 18 Nov 2026 |
