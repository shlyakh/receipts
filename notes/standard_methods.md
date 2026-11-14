# Standard forecasting methods: a running collection

Started 2026-11-13 (Yuri's request). Purpose: for each forecasting problem we might
judge claims about, know the field's standard benchmark before freezing a baseline (the
lesson in `BASELINES.md`). One row per method. "Verified" means a primary source was
opened and the fact is recorded in the note named; "from memory" means it still needs
checking before use (CLAUDE.md rule 7).

LinkedIn posts are not sources (decision 21). A method that comes to our attention
through one is recorded here only from its own primary sources.

## Electricity load (our benchmark)

| Method | What it is | Primary source | Status here |
|---|---|---|---|
| Seasonal naive (same hour last week) | copy of load 168 h earlier | review papers | scored (v1) |
| Tao's Vanilla Benchmark | regression: trend, month, weekday by hour, cubic temperature by month and hour | Hong, Pinson, Fan 2014, doi 10.1016/j.ijforecast.2013.07.001 | verified (`hong2014_gefcom2012.md`); scored (v1.1) |
| Recency-effect regression | Vanilla plus lagged and averaged temperatures | Wang, Liu, Hong 2016 | from memory; not run |
| Additive models (GAM) | smooth terms for temperature, time of year, lags | GEFCom2012 and 2014 leading entries | summaries only (`classical_baselines.md`); not run |
| Boosted trees, competition grade | calendar, temperature lags and rolling statistics, detrended target | BigDEAL 2022 entry, arXiv 2305.05575 | opened; our untuned version registered (v1.3) |
| MSTL, NHITS, TFT via Nixtla | multi-seasonal decomposition; neural with future covariates | library docs | researched (`framework_choice.md`); not run |

## Electricity price, day ahead (not our benchmark; for future work)

| Method | What it is | Primary source | Status here |
|---|---|---|---|
| Naive (similar day) | yesterday's or last week's price for the same hour | Lago et al. 2021 review | from memory |
| LEAR (Lasso Estimated AutoRegressive) | one lasso regression per delivery hour on lagged prices and day-ahead exogenous forecasts (load, wind, solar), recalibrated daily, often averaged over several calibration windows | Uniejewski, Nowotarski, Weron 2016; Lago, Marcjasz, De Schutter, Weron 2021; epftoolbox documentation | from memory; to verify |
| DNN benchmark | feed-forward network with tuned hyperparameters, the review's second open benchmark | Lago et al. 2021; epftoolbox | from memory; to verify |

Good practice the price literature asks for (from memory, to verify with the review):
long test periods of a year or more, several markets, the relative MAE against the
naive forecast, and a significance test (Diebold-Mariano or Giacomini-White).

Usual data for European prices: ENTSO-E Transparency Platform (prices, day-ahead load,
wind and solar forecasts); fuel and carbon prices from exchanges.

## General-purpose

| Method | Primary source | Status here |
|---|---|---|
| ETS, ARIMA, Theta, seasonal naive | Hyndman and Athanasopoulos, Forecasting: Principles and Practice | from memory; single-season forms judged unsuitable for hourly load (`model_families.md`) |
| Leaderboards for pretrained models | GIFT-Eval, fev-bench | change logs recommended as scan feeds (`blog_newsletter_sources.md`) |

## How to add a row

Find the problem's review papers and competitions, name the benchmark the organisers
used, open the primary source, record the formula in a reading note, and only then mark
it verified. The eight-step procedure is in `BASELINES.md`.
