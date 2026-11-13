# Notes: the GB demand weather study (Andy Moran, Heaviside Analytics)

Read on Nov 12, 2026 from two public repos:

- `AndyMoran/gb-foundation-model-tests` (MIT): the earlier weather-free study,
  results in `RESULTS.md`, DOI 10.5281/zenodo.23962005.
- `AndyMoran/gb-weather-private` (no licence stated): the weather study's plan
  (`docs/PLAN_weather.md`) and processing code. Commit `67f3b67`, Nov 12, 2026.

Use these as design references. Implement our own code; do not copy from the
second repo, which states no licence.

## What the study asks

Great Britain national demand, half-hourly, day-ahead, issued 09:30 the day before.
Three zero-shot models (Chronos-2, Timestral, TimesFM 2.5) and a regression, each
with and without weather, plus the grid operator's own forecast as a reference.

## Verified results (weather-free study only)

Window 1 Jan 2024 to 31 Oct 2026, 1,035 days. Error ratio to the regression
(below 1 = model better), 90% interval:

| Model | Ratio | Interval |
|-------|-------|----------|
| TimesFM 2.5 | 1.009 | 0.978 to 1.042 |
| Chronos-2 | 0.928 | 0.902 to 0.955 |
| Timestral | 0.910 | 0.885 to 0.935 |

- Seasonal naive: 2,095 MW mean daily error; the regression's error was 0.741 of it.
- Operator forecast: 694 MW, less than half of every model's error.
- On bank holidays every model lost to the regression.
- On days after each model's release the edges shrink (Chronos-2 0.965, interval
  crossing 1).

Weather-study results: partly verified on Nov 12, 2026 (evening). Zenodo record
24161799, "Weather and zero-shot forecasting models: backtest results for GB
electricity demand (part 1 of 2)", published Nov 12, 2026, version
`weather-results-backtest`: https://zenodo.org/records/24161799

- Read from the record's description only (through a summarising fetch; the 9.4 MB
  zip was not opened): a pre-registered backtest over 960 days, 16 Mar 2024 to
  31 Oct 2026; weather cut mean daily error by 34% for the regression, 32% for
  Chronos-2, 23% for Timestral and 6% for TimesFM 2.5; the models' edge over the
  weather-free regression largely disappears once weather is included. A live
  check to 31 Mar 2027 is planned as part 2.
- VERIFIED on Nov 13, 2026 from `weather_study/RESULTS.md` inside the Zenodo zip (MIT
  licence, repository commit `58b87d0`). Error divided by the regression's, both with
  the same weather, day-ahead, 960 days, 90% intervals: Chronos-2 0.966 (0.931 to
  1.001), Timestral 1.074 (1.034 to 1.115), TimesFM 2.5 1.453 (1.394 to 1.510). Weather
  gains: regression 34%, Chronos-2 32%, Timestral 23%, TimesFM 2.5 6%. Weather closed
  62% of Chronos-2's gap to NESO's forecast.
- The study notes that TimesFM 2.5 takes weather through a linear fit on its own
  context, not through the network, and that it gained nothing in autumn. Our result
  agrees: with temperature it stays behind the regression on both PJM zones.
- Release dates the study uses: TimesFM 2.5 15 Sep 2025, Chronos-2 30 Oct 2025,
  Timestral 15 Oct 2026. It treats Timestral as having no usable unseen backtest.
- The zip is a release of `gb-foundation-model-tests` (MIT). Once confirmed, cite
  this record for the weather study's design in place of the no-licence repo.

## The regression

One least-squares fit per clock slot (48 half-hour slots), refit for every target
day on the trailing 365 complete days.

- Base terms: intercept; demand at the same slot 2 days earlier; demand at the same
  slot 7 days earlier; six day-of-week indicators (Monday base); bank holiday;
  a 24 Dec to 2 Jan indicator.
- Weather terms added in the weather study, per slot: temperature centred on its
  mean over the fit rows; its square; wind; centred temperature x wind; solar.
- A weather variable with almost no range in a slot's fit rows is dropped from that
  slot (in practice solar at night).
- Seasonal naive = same slot 7 days earlier.

## Weather inputs

- Variables: temperature, wind speed, solar radiation; national averages weighted by
  population (temperature, wind) and installed solar capacity (solar).
- Target day: the forecast run that was public before the issue time, with a
  flagged fallback to the previous run.
- History: reanalysis up to 11 days back; each of the last 10 days from its own
  forecast run's first 24 hours.
- For the models' context, reanalysis days are shifted onto the forecast model's
  scale using the last 60 or so days. The regression's training data is not shifted.
- Known caveat stated in the plan: the regression trains on reanalysis and predicts
  with forecast weather; in the cool months that mismatch is put at 100 to 200 MW.

## Model settings with weather

| Model | How weather enters | Settings |
|-------|--------------------|----------|
| Chronos-2 (`chronos-forecasting` 2.3.2) | past covariates over the context and future covariates over the horizon | no cross-learning; point forecast = median |
| Timestral (`timestral` 1.0.0) | known covariates over context + horizon | symmetric averaging on; non-negative clipping on; median |
| TimesFM 2.5 (`timesfm` 3.0.2) | `forecast_with_covariates`, dynamic numerical covariates | xreg mode "xreg + timesfm"; CPU |

Context length in the weather-free study: 2,688 half-hours (8 weeks) for every model.

## Statistics

- Daily error = mean absolute error over the target day, in MW.
- Ratio = mean daily error of arm A / arm B over the window.
- Intervals and tests: moving-block bootstrap over days, blocks of 7, 2,000 draws,
  fixed seed, same resampled days for both arms; 90% percentile intervals;
  one-sided test of ratio >= 1.
- A "worth switching" bar (10%) was set in advance in the weather-free study.
- Result sentences were written before scoring, one per possible outcome.

## Discipline worth copying

- Plan frozen at a public git tag before scoring; GitHub's push time is the evidence.
- A lock file holds hashes of the plan, inputs, weights and package list.
- Scoring refuses to start if any locked file's hash differs.
- The official run is the first that passes a list of gate checks; failed attempts
  are kept and logged as deviations.
- One gate check: a second, independent implementation of the regression must match
  the first to 0.1 MW on sample days.
- A day that cannot be built is dropped for every forecaster, and listed.
- Leakage is stated after every backtest sentence about a model; a forward window
  that no model can have seen is the check.

## How this maps to our benchmark

| Study | Ours |
|-------|------|
| GB national, half-hourly | PJM zones JC and DOM, hourly |
| Day-ahead, daily origins | Week-ahead (168 h), weekly origins |
| Lags of 2 and 7 days | 7-day lag only (the 2-day lag is not available across a 168-hour horizon) |
| 48 slot models | 24 hour-of-day models |
| Blocks of 7 days | Resample whole weeks |
| Bank holidays, Christmas window | US federal holidays, same 24 Dec to 2 Jan window |
| Temperature, wind, solar | Temperature only in `protocol-v1` (decision 17) |
| 1,035 or 960 daily origins | 52 weekly origins, so wider intervals |

Because of these differences our result is a transfer test, not a replication
(decision 12). Horizon day 1 of our per-lead-day breakdown is the closest
comparison to the study's setting.

Latest commit in the weather repo specifies an exploratory run that gives Chronos-2
and Timestral the regression's calendar terms as covariates, with and without
weather. Calendar covariates for the foundation models are a cheap extra row for us.
