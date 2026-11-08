# Data search for a trained model (8 Nov 2026)

Sonnet agent search, then checked by Claude. Research only: nothing downloaded, no sign-ups.

## Finding
No public daily, weekly or located heat-illness outcome series exists for Abu Dhabi, the UAE or any Gulf state (checked:
ADPHC, DoH, SEHA, MOHAP, NCEMA, Bayanat, Dubai Pulse, SCAD, Qatar MoPH/HMC, Saudi, Kuwait, Oman, Bahrain). A trained model
learns from US OSHA outcomes; Abu Dhabi supplies the weather, the law layer and, at most, a published scale anchor.

## Usable sources
| Source | Verified | Access | Granularity | Use |
|---|---|---|---|---|
| Joubert D, Thomsen J, Harrison O. Safety in the Heat: a comprehensive program for prevention of heat illness among workers in Abu Dhabi. Am J Public Health 2011;101(3):395-8. PMID 21307373 | Yes (PubMed, 8 Nov): abstract quotes one company's "15.3 vs 1.16 cases per 1000 workers" | Paper only | Two companies, annual rates, 2008-09 | Abu Dhabi context and scale anchor; evidence that a heat programme measurably cut cases |
| CDC Heat & Health Tracker (NSSP heat-related illness ED visits) | Page yes; no download/API found | Dashboard | Daily/weekly, by HHS region (10 regions) | Too coarse for region-day training |
| Maine heat illness ED visits (data.mainepublichealth.gov) | Agent only | Open portal | County, weekly/daily | Dated and located, but cool climate; weak fit |
| Washington L&I heat claims | Agent only | Annual PDFs | State aggregates | Not trainable |
| ERA5-HEAT (UTCI, mean radiant temperature), Copernicus CDS | Agent only | Free, needs a CDS account (Ahmed's sign-up) | Global, hourly, 0.25 deg, 1940- | Better heat-stress predictors than heat index (sun and wind included) |
| SCAD labour statistics | Agent only | Open tables | Annual, emirate, by sector | Outdoor-worker denominator for the regulator view |
| Abu Dhabi 2010: 3,017 heat-illness ED cases | UNVERIFIED (press only) | n/a | Annual | Do not cite until a primary source is found |

## Implication for the model
Train on OSHA region-days (as now) with richer weather features; score once against the frozen relative rule at the same
alert load. Output a relative risk for the zone, not an absolute probability. State plainly: no local outcome validation.
