# How much would a better weather forecast change the results?

Research pass on Nov 13, 2026. Read-only: no model was run, no protocol, code or
results file was changed. Numbers marked "computed here" come from the existing
`results/` and `data/processed/` files plus a few Open-Meteo requests at two generic
test points (40.0, -75.0 and 38.0, -78.0; not our stations). Everything computed from
the scored weeks here is exploratory and post hoc; none of it is a leaderboard row.
Items marked (memory) were not confirmed on a page opened today.

## Summary and recommendation

- **The ceiling is already measured.** Perfect temperature would cut the forecast-regime
  error by 22% (lag regression), 38% (Vanilla with trend) and 29% (Chronos-2) on DOM,
  and by 10%, 24% and 23% on JC. No weather model can buy more than that.
- **Our current weather skill**: temperature error against the oracle series grows from
  about 1.4 °C RMSE on horizon day 1 to 3.6 °C (DOM) and 3.9 °C (JC) on day 7.
- **The curve between the two regimes is convex.** In a no-rerun approximation, a 25%
  cut in temperature error recovers 35 to 56% of the oracle gap, and a 50% cut recovers
  65 to 93%. A 20% cut lowers load error by about 8% (lag regression), 13% (Vanilla
  with trend) and 9% (Chronos-2) on DOM; 5%, 9% and 7% on JC.
- **Better weather helps the regressions more than Chronos-2.** Against Vanilla with
  trend, Chronos-2's DOM ratio moves from 0.95 (today's weather) to 1.09 (perfect
  weather). Against the lag regression its lead widens (0.73 to 0.66).
- **Three things about our weather inputs that the docs do not say** (section 3):
  1. The "oracle" is not ERA5 for the scored year. Open-Meteo's default archive series
     is ECMWF's 9 km IFS; it differs from ERA5 by about 1.4 °C RMSE at both test points.
  2. The forecast regime is two models, not one: HRRR on horizon day 1, GFS on days 2
     to 7 (Open-Meteo `best_match` for the US).
  3. GFS is the weakest of the archived sources. NBM, ECMWF IFS, AIFS and the
     AI/hybrid ensembles have 15 to 35% lower temperature error at days 2 to 7 at the
     test points, and all have lead-matched archives covering most or all scored weeks.
- **Recommended for the dashboard (stage 1):** one chart per zone, load error against
  "share of today's temperature error remaining" (1.0 = today, 0 = perfect), for the lag
  regression, Vanilla with trend and Chronos-2, built by re-running the models on
  blended temperature over the 52 pre-window (`ordering_gate`) weeks and the gate
  weeks only. Register as `protocol-v1.2`. About half a day. A no-rerun preview from
  the existing scored forecasts (table in section 2a) takes about an hour and must be
  labelled as an approximation.
- **Stage 2:** add real alternative sources (NBM, ECMWF IFS 0.25°, AIFS) as new
  forecast regimes under a further protocol version, gate first, score once. About a
  day. This replaces the synthetic x-axis with measured points.

## 1. What the two regimes already tell us

### Oracle-to-forecast gap (computed here from `results/windows.parquet`)

48 scored windows per zone. MAE in MW. Intervals are 90%, whole-week bootstrap, 2,000
draws, protocol seed, same weeks for both arms. "Cut" is the share of forecast-regime
error that perfect temperature removes.

| Zone | Model | Oracle | Forecast | Gap (90% interval) | Forecast / oracle | Cut |
|---|---|---|---|---|---|---|
| DOM | Lag regression + temperature | 782 | 1,005 | 223 (153 to 300) | 1.285 (1.198 to 1.372) | 22% |
| DOM | Vanilla with trend | 478 | 776 | 298 (237 to 363) | 1.623 (1.500 to 1.756) | 38% |
| DOM | Chronos-2 + temperature | 519 | 734 | 215 (167 to 267) | 1.414 (1.310 to 1.537) | 29% |
| DOM | LightGBM + temperature | 736 | 952 | 216 (164 to 272) | 1.294 (1.217 to 1.379) | 23% |
| DOM | Vanilla | 1,227 | 1,393 | 166 (112 to 223) | 1.136 (1.089 to 1.186) | 12% |
| DOM | Chronos-2, 48-hour gap | 572 | 766 | 195 (150 to 244) | 1.341 (1.247 to 1.454) | 25% |
| DOM | TimesFM 2.5 + temperature | 1,114 | 1,224 | 110 (59 to 168) | 1.099 (1.049 to 1.162) | 9% |
| DOM | Timestral (not out-of-sample) | 380 | 660 | 279 (230 to 336) | 1.735 (1.603 to 1.890) | 42% |
| JC | Lag regression + temperature | 239 | 267 | 28 (16 to 39) | 1.116 (1.067 to 1.168) | 10% |
| JC | Vanilla with trend | 166 | 219 | 53 (39 to 69) | 1.320 (1.236 to 1.414) | 24% |
| JC | Chronos-2 + temperature | 167 | 218 | 51 (34 to 71) | 1.306 (1.208 to 1.412) | 23% |
| JC | LightGBM + temperature | 179 | 229 | 50 (35 to 67) | 1.280 (1.197 to 1.377) | 22% |
| JC | Vanilla | 165 | 217 | 53 (38 to 69) | 1.319 (1.235 to 1.415) | 24% |
| JC | Chronos-2, 48-hour gap | 170 | 214 | 44 (30 to 60) | 1.258 (1.172 to 1.356) | 21% |
| JC | TimesFM 2.5 + temperature | 266 | 299 | 33 (20 to 46) | 1.122 (1.071 to 1.179) | 11% |
| JC | Timestral (not out-of-sample) | 130 | 186 | 56 (42 to 72) | 1.433 (1.334 to 1.542) | 30% |

Gap by horizon day (forecast MAE minus oracle MAE, MW):

| Zone | Model | D1 | D2 | D3 | D4 | D5 | D6 | D7 |
|---|---|---|---|---|---|---|---|---|
| DOM | Lag regression + temperature | 26 | 153 | 159 | 186 | 313 | 226 | 498 |
| DOM | Vanilla with trend | 159 | 180 | 231 | 208 | 361 | 350 | 596 |
| DOM | Chronos-2 + temperature | 68 | 127 | 173 | 178 | 284 | 279 | 396 |
| JC | Lag regression + temperature | 0 | -4 | 9 | 28 | 48 | 55 | 58 |
| JC | Vanilla with trend | 12 | 21 | 30 | 44 | 86 | 71 | 106 |
| JC | Chronos-2 + temperature | 9 | 34 | 52 | 63 | 75 | 70 | 55 |

- The better a model uses temperature, the more forecast weather costs it. The models
  with the lowest oracle error have the largest gaps.
- Most of the gap sits in days 5 to 7. A weather model that improves only days 1 to 3
  buys little.
- The ceiling is optimistic for a second reason: the regressions are fitted on the
  oracle series, so the oracle regime also removes the train/predict mismatch, which
  no real forecast removes.

### Temperature forecast error by horizon day (computed here)

Forecast-regime temperature minus oracle temperature, zone series, over the 168 hours
of each of the 48 scored windows. Units °C. "Daily mean" is the absolute error of the
24-hour mean. "Last week" is the error of using the temperature 168 hours earlier, a
no-skill anchor.

| Zone | Day | MAE | RMSE | Bias | Daily mean MAE | Last week RMSE |
|---|---|---|---|---|---|---|
| DOM | 1 | 1.05 | 1.38 | -0.30 | 0.73 | 5.4 |
| DOM | 2 | 1.13 | 1.45 | +0.22 | 0.77 | 6.9 |
| DOM | 3 | 1.29 | 1.71 | +0.09 | 1.00 | 7.7 |
| DOM | 4 | 1.92 | 2.52 | +0.33 | 1.46 | 6.4 |
| DOM | 5 | 2.01 | 2.95 | +0.31 | 1.58 | 6.4 |
| DOM | 6 | 2.12 | 2.77 | -0.40 | 1.58 | 6.3 |
| DOM | 7 | 2.79 | 3.63 | -0.17 | 1.97 | 5.7 |
| DOM | all | 1.76 | 2.47 | +0.01 | | 6.5 |
| JC | 1 | 1.15 | 1.47 | -0.36 | 0.74 | 5.4 |
| JC | 2 | 1.24 | 1.59 | +0.23 | 0.89 | 7.4 |
| JC | 3 | 1.33 | 1.73 | +0.22 | 0.88 | 7.9 |
| JC | 4 | 1.92 | 2.88 | +0.27 | 1.23 | 6.6 |
| JC | 5 | 2.15 | 3.22 | +0.06 | 1.73 | 6.2 |
| JC | 6 | 2.55 | 3.50 | +0.09 | 1.71 | 5.8 |
| JC | 7 | 2.86 | 3.89 | +0.36 | 2.07 | 5.4 |
| JC | all | 1.89 | 2.77 | +0.12 | | 6.5 |

- Each horizon day is always the same weekday (day 1 is Monday), so the rows mix lead
  with 48 particular days. Scoring each lead's forecast on all 168 hours gives a
  smoother growth curve: RMSE 1.42, 1.56, 1.71, 2.06, 2.59, 3.05, 3.64 (DOM) and 1.45,
  1.62, 1.78, 2.17, 2.68, 3.29, 3.92 (JC) for leads 1 to 7.
- Errors persist within a day: the daily-mean error is about 70% of the hourly error.
  Independent hourly noise would not look like this.
- The bias changes sign between day 1 and day 2, and at day 1 it is a night-time cold
  bias of 0.5 to 0.9 °C. That is the HRRR-to-GFS switch (section 3).
- By season (all days): DOM RMSE 2.9 winter, 2.7 spring, 2.0 summer, 2.2 autumn; JC
  2.9, 3.4, 2.5, 2.2.
- About 1.4 °C of error remains at day 1. Much of that is a difference between two
  modelling systems (the oracle is ECMWF's, the forecast is NOAA's), not forecast
  error. No better model would reach zero on this axis.

## 2. Ways to estimate load error as a function of weather skill

"New regime" means a temperature series that neither existing regime defines, so it
needs a protocol addendum (rules 4 and 5) and, if run on the 52 scored origins, gate
runs and a tag first (rule 12).

| Method | What it does | Can honestly claim | Cannot claim | New regime | Touches scored origins |
|---|---|---|---|---|---|
| a. Blend | T(a) = oracle + a x (forecast - oracle), a from 0 to 1; rerun models | error if today's forecast errors were uniformly a times as large | what a specific model would give; real models change the error pattern, not only its size | yes | only if run there; can be done on pre-window weeks |
| a'. Blend, no rerun | interpolate each model's two existing hourly forecasts | a first-order preview of (a) | exact values: the models are not linear in temperature | no (post hoc arithmetic) | reads existing scored forecasts; exploratory label |
| b. Lead substitution | give horizon day k the lead k-1 (or k-2) forecast | effect of "one day of lead gained", using real forecast errors | it is a real information set (the run starts after the cutoff) | yes | same as (a) |
| c. Synthetic error | oracle + simulated error matched to a growth curve | sensitivity to error size under a stated error model | realism, unless the simulator reproduces autocorrelation, diurnal bias and regime dependence | yes | same as (a) |
| d. Decomposition | load error change is about dLoad/dT x temperature error | where and when temperature error matters; needs no runs | a prediction: sensitivity changes sign with season and errors add in quadrature | no | reads existing forecasts |
| e. Real alternative source | swap in NBM, IFS, AIFS forecasts | measured error with that source | generality beyond these zones and this year | yes | yes, once, after a tag |

### a'. No-rerun blend (computed here, exploratory)

For each model, hourly forecast(a) = oracle-regime forecast + a x (forecast-regime
forecast - oracle-regime forecast). MAE in MW over the 48 scored windows. a = 1 and
a = 0 are the registered results; the rest is interpolation.

| Zone | Model | a=0 | 0.25 | 0.5 | 0.7 | 0.8 | 0.9 | a=1 |
|---|---|---|---|---|---|---|---|---|
| DOM | Lag regression + temperature | 782 | 790 | 834 | 892 | 927 | 965 | 1,005 |
| DOM | Vanilla with trend | 478 | 491 | 557 | 634 | 678 | 726 | 776 |
| DOM | Chronos-2 + temperature | 519 | 536 | 584 | 638 | 668 | 700 | 734 |
| JC | Lag regression + temperature | 239 | 237 | 241 | 249 | 254 | 260 | 267 |
| JC | Vanilla with trend | 166 | 164 | 175 | 190 | 199 | 208 | 219 |
| JC | Chronos-2 + temperature | 167 | 173 | 185 | 197 | 204 | 211 | 218 |

Change in load MAE against today (a = 1):

| Zone | Model | 10% less temperature error | 20% less | 30% less | 50% less | One day of lead gained | Every day as good as day 1 |
|---|---|---|---|---|---|---|---|
| DOM | Lag regression + temperature | -4.0% | -7.8% | -11.3% | -17.1% | -5.8% | -14.2% |
| DOM | Vanilla with trend | -6.4% | -12.6% | -18.3% | -28.2% | -9.0% | -22.6% |
| DOM | Chronos-2 + temperature | -4.5% | -8.9% | -13.0% | -20.4% | -6.5% | -16.4% |
| JC | Lag regression + temperature | -2.5% | -4.8% | -6.7% | -9.7% | -3.9% | -8.9% |
| JC | Vanilla with trend | -4.6% | -8.9% | -12.9% | -19.7% | -7.0% | -17.0% |
| JC | Chronos-2 + temperature | -3.4% | -6.6% | -9.7% | -15.2% | -5.1% | -11.9% |

"One day of lead gained" scales day k's temperature error by RMSE(lead k-1) / RMSE(lead
k), days 2 to 7 (factors 0.80 to 0.91). "Every day as good as day 1" scales day k by
RMSE(lead 1) / RMSE(lead k).

- The curve is convex and flat near perfect weather: weather-driven error adds to model
  error roughly in quadrature, so the first improvements pay most.
- Chronos-2 against Vanilla with trend under this approximation: DOM 0.946 today, 0.985
  at 20% less temperature error, 1.049 at 50% less, 1.085 at perfect. JC stays within
  1.00 to 1.06. Against the lag regression: DOM 0.730 to 0.663, JC 0.817 to 0.698.
- Known weakness: on JC the Chronos-2 / Vanilla ratio is not monotonic in a (1.053 at
  a = 0.5, 1.007 at a = 0), which a true rerun may not reproduce. The approximation
  error must be measured on gate weeks before any of this is shown.

### d. Sensitivity (computed here)

| Zone | Model | Mean abs. forecast change between regimes, MW | Per °C of mean abs. temperature error |
|---|---|---|---|
| DOM | Lag regression + temperature | 638 | 363 |
| DOM | Vanilla with trend | 634 | 360 |
| DOM | Chronos-2 + temperature | 447 | 254 |
| JC | Lag regression + temperature | 139 | 74 |
| JC | Vanilla with trend | 147 | 78 |
| JC | Chronos-2 + temperature | 104 | 55 |

- Chronos-2 responds about 30% less to a degree of temperature change than the
  regressions. That is why forecast weather hurts it less in MW and why better weather
  helps it less.
- The forecast change is nearly uncorrelated with the oracle-regime error (-0.16 to
  +0.21), so squared errors add: on DOM, sqrt(RMSE_oracle^2 + RMS change^2) gives 997
  for Chronos-2 against a measured 996.
- A single "MW per °C" slope is not usable as a predictor: the hourly correlation
  between temperature error and forecast change is near zero (-0.03 to 0.31) because
  the response changes sign between heating and cooling seasons. Across weeks, the
  correlation between a week's temperature MAE and its load-error gap is only 0.10 to
  0.35.

### e. Published approaches

- Ex post against ex ante is the field's standard split: error with actual weather is
  model error, the rest is input error. Tao Hong's tips post states this and says model
  error is often the larger part.
  https://blog.drhongtao.com/2014/08/13-lucky-tips-for-energy-forecasting.html
- Hong's 2018 post: evidence favours temperature models with actual temperature; with
  forecast temperature for point forecasts there is no solid evidence either way.
  https://blog.drhongtao.com/2018/12/temperature-based-models-vs-time-series-models.html
- Fay and Ringwood (2010, IEEE Trans. Power Systems 25(3), read in full): with few real
  forecasts archived, they simulate "pseudo-forecasts" whose error has a level and a
  shape component between weather-front turning points plus noise, because real errors
  are serially correlated and independent Gaussian noise is a poor model. In their Irish
  data MAPE rose from about 1.9 to 2.4% with actual weather to about 2.2 to 2.9% with
  pseudo-forecasts. They cite earlier estimates that weather error causes 17% to 60% of
  load error in other systems. They train on actual weather and fit the combining step
  on forecast weather. https://mural.maynoothuniversity.ie/3618/
- Li (2022 dissertation, advised by Hong; abstract seen in search results only, PDF
  returned 403): ex ante short-term forecasting with a weather-forecast evaluation
  chapter; reports that a smaller temperature error does not always give a smaller load
  error, and a 7.4% gain from predicting the temperature error itself.
  https://ninercommons.charlotte.edu/record/2203
- Xie and Hong (2018, IEEE Trans. Smart Grid; summary only): temperature scenarios by
  fixed-date, shifted-date and bootstrap methods, for probabilistic load forecasts when
  no usable weather forecast exists.
  https://blog.drhongtao.com/2016/07/temperature-scenario-generation-for-probabilistic-load-forecasting.html
- Hong, Wang and White (2015, Int. J. Forecasting 31(2); abstract only): choosing how
  many and which weather stations per zone improves accuracy. Our three unweighted
  points per zone are a separate, untested source of weather-input error.
  https://econpapers.repec.org/RePEc:eee:intfor:v:31:y:2015:i:2:p:286-295
- Not found: a published curve of load error against temperature-forecast skill by lead
  day for week-ahead zonal load. Teisberg et al. (2005) and Douglas et al. (1998) are
  the sources of the 17% and 60% figures in Fay and Ringwood's reference list; neither
  was opened.

## 3. Better weather models with usable archives

### What our two regimes actually are (verified on the live API today)

- **Oracle.** Open-Meteo's historical API page says the default selection combines IFS
  HRES, ERA5 and ERA5-Land, with IFS at 9 km from 2017. At the test point the default
  archive series is identical to `ecmwf_ifs` day 0 over the scored year and differs
  from `models=era5` by 1.38 °C RMSE (bias -0.5 to -0.8 °C). `fetch.py` sends no
  `models` parameter, so the oracle is the IFS series. `REFERENCE.md` and
  `protocol.yaml` call it reanalysis / ERA5.
  https://open-meteo.com/en/docs/historical-weather-api
- **Forecast.** `best_match` equals `gfs_seamless` at every lead, equals `gfs_hrrr` at
  day 0 and day 1, and equals `gfs_global` at days 2 to 7. HRRR only reaches 48 hours.
  The Open-Meteo pages mark HRRR as discontinued on 2026-11-30 and NAM on 2026-11-01,
  so `best_match` will change after that date.
- Consequence: swapping in an ECMWF forecast would shrink the temperature error partly
  because forecast and oracle would then come from the same system. A neutral truth
  (station observations) is needed before ranking sources.

### Lead-matched archives on Open-Meteo Previous Runs (probed today)

Hours with a value out of 8,760 between 2025-11-10 and 2026-11-09, `temperature_2m`,
leads day 1 to day 7, test point 40.0, -75.0. Model ids are the ones the API accepted.

| Source | API id | Coverage of the scored year |
|---|---|---|
| Current regime | `best_match` | complete |
| NOAA GFS | `gfs_global` | complete |
| NOAA NBM (blend, CONUS) | `ncep_nbm_conus` | complete |
| ECMWF IFS 0.25° | `ecmwf_ifs025` | complete |
| ECMWF IFS HRES 9 km | `ecmwf_ifs` | 94 to 100% by lead |
| ECMWF AIFS Single | `ecmwf_aifs025_single` | complete at leads 1-3, 6; 96% at 4, 5, 7 |
| NOAA HRRR | `gfs_hrrr` | lead day 1 only |
| DWD ICON, GEM, UKMO, JMA GSM | `icon_global`, `gem_global`, `ukmo_global_deterministic_10km`, `jma_gsm` | mostly complete; ICON and UKMO stop at day 6 |
| NOAA AIGFS | `ncep_aigfs025` | from 2026-01, 60 to 76% |
| NOAA HGEFS mean (hybrid ensemble) | `ncep_hgefs025_ensemble_mean` | from 2026-01-22, 51 to 68% |
| NOAA AIGEFS mean | `ncep_aigefs025_ensemble_mean` | from 2026-01-22 |
| ECMWF IFS ENS mean, AIFS ENS mean, GEFS mean | `ecmwf_ifs025_ensemble_mean`, `ecmwf_aifs025_ensemble_mean`, `ncep_gefs025_ensemble_mean` | from 2026-02-20 (about 70%) |
| Google WeatherNext 2 mean | `google_weathernext2_ensemble_mean` | from 2026-06-06 (about 42%) |

- Docs: most models from January 2024, GFS temperature from March 2021, JMA from 2018;
  leads day 1 to day 7. https://open-meteo.com/en/docs/previous-runs-api
- Single Runs API (`run=` parameter): IFS HRES 9 km from 2024-03-14, most other models
  only from 2026-04-02. A request for the IFS run of 2025-11-10 00 UTC returned 192
  hourly values. This is the route to true issue-time matching (it would retire the
  publication-latency caveat). https://open-meteo.com/en/docs/single-runs-api
- Historical Forecast API stitches the first hours of each run; no fixed lead, so not
  usable for a forecast regime. https://open-meteo.com/en/docs/historical-forecast-api
- Ensemble API: members kept three days only. Ensemble Mean API: mean and spread, most
  from March 2026. https://open-meteo.com/en/docs/ensemble-api ,
  https://open-meteo.com/en/docs/ensemble-mean-api
- Licence: Open-Meteo API data CC BY 4.0; ECMWF open data CC-BY-4.0; UK Met Office
  CC BY-SA; NOAA under its own disclaimer page. https://open-meteo.com/en/licence

### Other archives

| Source | Archive | Useful for our scored year? | Licence | Status |
|---|---|---|---|---|
| FourCastNet v2-small, Pangu-Weather, GraphCast (and Aurora per MetPy docs) | NOAA/CIRA AIWP reforecasts on AWS (`noaa-oar-mlwp-data`), from 10/2020 (GraphCast 01/2022) to present, 00 and 12 UTC, 6-hourly to 240 h, includes 2 m temperature, GFS and IFS initial states | yes, with gridded-file handling and 6-hourly interpolation | open, no restrictions | registry page read; Aurora from a search summary |
| ECMWF open data (IFS, AIFS Single, AIFS ENS) | portal keeps the last 12 runs; cloud mirrors exist; 0.1° IFS added 2026-10-20 | only through a mirror's history, depth not stated on the page | CC-BY-4.0 | page read |
| WeatherNext 2 / 3 (Google) | BigQuery, Earth Engine, Cloud Storage; 64 members | archive depth, access terms and licence not stated on the pages read | not verified | pages read |
| WeatherBench 2 | evaluation forecasts mainly for 2020 | no: wrong year; use only for published skill | not stated in FAQ | FAQ read |
| NeuralGCM | no operational archive found | no | | (memory) |
| GEFS members, GFS, HRRR, NBM raw files | NOAA buckets on AWS | yes, heavier engineering | open | (memory) |

Sources: https://registry.opendata.aws/aiwp/ ,
https://www.ecmwf.int/en/forecasts/datasets/open-data ,
https://developers.google.com/weathernext/guides/dissemination ,
https://sites.research.google/weatherbench/faq/

### Temperature skill of the alternatives in our region and year (computed here)

RMSE in °C by lead day at the test point 38.0, -78.0 (Virginia), hours where every
listed source has a value. Percentages are against the current regime. Two references,
because the choice changes the ranking.

Full scored year (8,442 hours), reference = our oracle series (IFS 9 km):

| Source | D1 | D2 | D3 | D4 | D5 | D6 | D7 | D2 to D7 vs. current |
|---|---|---|---|---|---|---|---|---|
| Current (`best_match`) | 1.90 | 2.43 | 2.55 | 2.85 | 3.38 | 3.91 | 4.40 | |
| NBM | 1.57 | 1.76 | 1.95 | 2.21 | 2.72 | 3.04 | 3.46 | -20 to -27% |
| ECMWF IFS 0.25° | 1.48 | 1.79 | 2.05 | 2.31 | 2.75 | 3.51 | 4.11 | -7 to -26% |
| ECMWF AIFS Single | 1.36 | 1.53 | 1.68 | 1.97 | 2.29 | 2.86 | 3.49 | -21 to -37% |

Same year, reference = ERA5: NBM -18 to -25%, IFS 0.25° -9 to -26%, AIFS -24 to -47%
at days 2 to 7. At the other test point (40.0, -75.0): NBM -16 to -26% on both
references; AIFS -14 to -19% (IFS reference) and -18 to -34% (ERA5); IFS 0.25° -5 to
-19% (IFS reference) but only +2 to -6% against ERA5.

Subsample from 2026-06 (3,066 hours, all ensemble means available), reference = oracle:

| Source | D1 | D3 | D5 | D7 | D7 vs. current |
|---|---|---|---|---|---|
| Current | 1.76 | 2.24 | 2.89 | 3.68 | |
| NBM | 1.45 | 1.63 | 2.16 | 2.76 | -25% |
| ECMWF IFS 0.25° | 1.35 | 1.83 | 2.22 | 3.24 | -12% |
| ECMWF IFS ENS mean | 1.31 | 1.61 | 2.04 | 2.65 | -28% |
| ECMWF AIFS Single | 1.33 | 1.49 | 1.91 | 2.38 | -35% |
| ECMWF AIFS ENS mean | 1.48 | 1.75 | 2.16 | 2.55 | -31% |
| GEFS mean | 1.76 | 1.86 | 2.31 | 2.85 | -22% |
| NOAA AIGFS | 1.52 | 1.70 | 2.11 | 2.65 | -28% |
| NOAA HGEFS mean | 1.42 | 1.57 | 1.96 | 2.50 | -32% |
| WeatherNext 2 mean | 1.35 | 1.54 | 1.94 | 2.30 | -37% |

- Read as an order of magnitude: two grid points, one year, model-based truth. ECMWF
  products are flattered by the IFS reference, AIFS by ERA5 (its training data). NBM is
  the cleanest evidence: a different centre, calibrated on observations, and 16 to 27%
  better on both references.
- A rough map onto the stage-1 axis: a realistic better source sits at a = 0.65 to 0.85
  of today's temperature error at days 2 to 7.

### Published skill statements

- ECMWF Newsletter 187: AIFS Single and AIFS ENS cut medium-range errors by about 5 to
  15% against IFS for most upper-air and surface fields; for 2 m temperature the gain is
  fewer large errors, mainly in stable winter weather; a 10% precipitation gain is
  equated to 0.5 to 1 day of lead. AIFS Single operational 25 Feb 2025, AIFS ENS 1 July
  2025. https://www.ecmwf.int/en/newsletter/187/news/forecast-performance-2025
- NOAA (Dec 2025 press release, via search summaries): AIGFS, AIGEFS and HGEFS made
  operational; AIGEFS extends skill by 18 to 24 hours over GEFS; HGEFS beats both.
  https://epic.noaa.gov/noaa-deploys-new-ai-driven-global-weather-models/
- Google's WeatherNext page: WeatherNext 2 about 10 to 20% better than WeatherNext Gen;
  Gen (GenCast) better than ECMWF ENS on over 96% of targets; Graph (GraphCast) better
  than HRES on over 90%. Vendor statements, mostly upper-air and CRPS, not 2 m
  temperature at our points. https://developers.google.com/weathernext/guides/research
- Rule of thumb that numerical forecasts gain about one day of lead per decade: (memory).

## 4. Ensembles

- **Ensemble mean** is the cheap path. It is a drop-in point series, archived
  lead-matched on Open-Meteo from 2026-02-20, and at the test point it beats its own
  deterministic run at every lead, clearly from day 3 (IFS: 2.65 against 3.24 °C at
  day 7). It is one more
  forecast regime, same code path as stage 2. Cost: a fetch and one run per model.
- **Its flaw for load**: the mean is smoother than any real day and under-forecasts
  extremes at long leads. Load rises on both sides of a comfortable temperature, so the
  load at the mean temperature is below the mean of the loads. Expect a low bias on the
  peak days that matter most.
- **Members through the load model**, averaging the load forecasts (or keeping them as
  a distribution), is the more realistic use and the only one that gives a
  weather-driven load interval to score with pinball loss and coverage. It is what
  operators' scenario methods do (PJM's weather-year replay, cited in
  `notes/unseen_data_for_new_models.md`).
- **Cost of members**: Open-Meteo keeps members three days, so no hindcast there.
  Options: (i) collect members daily from now on, for a prospective panel; (ii) pull
  IFS ENS or GEFS files from cloud mirrors and extract six points, one to two days of
  data engineering (archive depth unverified); (iii) approximate members from the
  archived mean and spread (`temperature_2m_spread`), cheap but it loses the
  hour-to-hour coherence of real members. Compute is small: 51 members x 48 weeks x 2
  zones is about 5,000 Chronos-2 calls at under a second each; the regressions are free.
- Recommendation: ensemble mean as a stage-2 regime; members only as a later
  probabilistic study with its own protocol.

## 5. Recommendation

### Stage 1: one chart, no new weather data

- **Chart**: per zone, x = share of today's temperature error remaining (1.0, 0.75,
  0.5, 0.25, 0), y = load MAE, three lines: lag regression with temperature, Vanilla
  with trend, Chronos-2 with temperature. Mark a band at 0.65 to 0.85, "where the
  better archived sources sit at our test points". Second panel or toggle: one day of
  lead gained (method b).
- **Where to run it**: the 52 `ordering_gate` weeks and the 6 gate weeks. Forecast
  temperature is complete for all of them (checked), the regressions already have both
  regimes there (50 windows per zone), and these weeks are never scored. Chronos-2 has
  not been run on the pre-window year; its weights postdate those weeks, so its line
  carries "0 of 50 weeks after the weights". Nothing touches the 52 scored origins.
- **Registration**: `protocol-v1.2.yaml` plus a dated line in `DEVIATIONS.md`. It must
  define the blend as a named what-if regime (rule 4 forbids mixing regimes in a row;
  this is a third series, not a mixture of results), state that it uses actuals after
  the cutoff by construction, list the values of a, the three models, the origin sets,
  and that every result is secondary and cannot change the outcome sentence. Gate: the
  lookahead test passes with a = 1 reproducing the forecast regime and a = 0 the oracle
  regime to 0.1 MW. Needs Yuri's sign-off because it adds a regime.
- **Allowed claim**: "If today's temperature-forecast errors were x% smaller at every
  lead, week-ahead load error on {zone} would fall by about y% for {model}, measured on
  the year before the scored window." Plus the measured ceiling from the scored weeks.
- **Not allowed**: naming a weather model on the x-axis as if measured; implying the
  oracle end is reachable; mixing these numbers into the leaderboard.
- **Effort**: about half a day. A blend option in `harness/data.py` and a test (1 h),
  addendum and gate (1 h), runs (minutes), export and chart (1 to 2 h).
- **Faster fallback for the demo**: the no-rerun table in section 2 drawn as the same
  chart from existing files, labelled "interpolated from the two scored regimes,
  exploratory". About an hour, no protocol change, but it is post hoc analysis of scored
  forecasts and its approximation error is unmeasured.

### Stage 2: a real alternative weather source

1. New protocol version registering forecast regimes by source: `forecast_nbm`,
   `forecast_ifs025`, `forecast_aifs`, optionally `forecast_ifs_ens_mean` (36 of 52
   weeks). Same stations, same lead-matching rule, `models=` fixed per regime.
2. Fetch and hash the new raw files (the fetch step needs a `models` parameter; the
   current regime should also be pinned to `gfs_seamless` explicitly so a change in
   `best_match` after 2026-11-30 cannot alter a refetch).
3. Scope the window-drop rule to each new regime, so gaps in a new source (AIFS lacks
   about 4% of hours at three leads) do not change `n_windows` for existing rows.
4. Add a neutral temperature truth (airport station observations) for the skill axis.
5. Gate origins, tag, then score the 52 origins once per registered row. All secondary.
6. The chart then gets measured points: x = that source's temperature RMSE against
   observations, y = load MAE, with the stage-1 curve behind them as the prediction.
7. Optional: true issue-time matching for IFS through the Single Runs API.

Effort: about one day, mostly fetching, hashing and gate checks.

### Open points for Yuri

- Whether a what-if regime is acceptable under rule 4, or should live outside the
  leaderboard entirely (a separate `sensitivity/` output).
- Whether to correct the wording "reanalysis / ERA5" for the oracle in `REFERENCE.md`
  and note it in `DEVIATIONS.md` (the frozen protocol text cannot be edited).
- Whether stage 2 should replace the forecast regime's source in a future primary
  comparison: the current one is the weakest available and is being retired upstream.

## Reproduction

Scratch scripts and probe downloads (not in the repo):
`/private/tmp/claude-501/-Users-yuri-work-research-receipts/d3f42f6f-8020-400a-9942-98b819248985/scratchpad/`
(`wx.py`, `wx2.py` for sections 1 and 2; `probe.py`, `skill2.py`, `skill3.py` for
section 3). Run with `uv run --project core python <script>` from the repo root.
