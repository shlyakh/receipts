# Baseline results, protocol-v1

Scored once on Thu Nov 12, 2026, at commit `912a902`, the commit tagged `protocol-v1`.
52 Monday origins from 2025-11-10 to 2026-11-02, 168-hour horizon, zones JC and DOM.

Baselines were scored on Thu Nov 12, 2026 at commit `912a902`. Chronos-2 was scored
once on Fri Nov 13, 2026 at commit `2029bad`, TimesFM 2.5 (univariate) once on the same day at
commit `760adc7`, and the 48-hour-gap, TimesFM-with-temperature and Timestral rows once
at commit `0771698`, all against the same unchanged protocol.

## Primary comparison

Chronos-2 with temperature against the temperature-only lag regression, forecast
regime, per zone. Ratio of mean weekly errors with a 90% whole-week bootstrap interval
(2,000 draws, seed from `protocol.yaml`). The sentences are the ones written before
scoring; the generated text is in `primary.md`.

| Zone | Ratio | 90% interval | Verdict |
|---|---|---|---|
| DOM | 0.730 | 0.665 to 0.805 | Worth switching: the whole interval is below 0.90 |
| JC | 0.817 | 0.686 to 0.960 | Inconclusive: the interval crosses 0.90 |

- **DOM:** On DOM, a week ahead with archived forecast weather, Chronos-2's error was
  0.730 of the temperature-only lag regression's (90% interval 0.665 to 0.805). The
  whole interval is below 0.90, so the model clears the 10% bar.
- **JC:** On JC, a week ahead with archived forecast weather, Chronos-2's error was
  0.817 of the temperature-only lag regression's (90% interval 0.686 to 0.960). The
  interval crosses the 10% bar, so 48 weeks cannot separate a tie from a real
  difference.
- **Leakage:** 48 of 48 scored weeks start after the date of the pinned weights
  (`amazon/chronos-2` revision `29ec3766`, weights file committed 2025-10-30). Earlier
  years of the same public series may be in the model's training data.

So the GB study's "rough tie" does not transfer to DOM under this protocol, and is
undecided on JC. Read that with the caveats below.

### Caveats on the primary result

- It is a transfer test. The comparator here has a 7-day lag and temperature only; the
  GB regression also had a 2-day lag, wind and solar, and a day-ahead horizon.
- The information set is idealised: load is visible up to the cutoff. That favours
  Chronos-2, which uses the most recent hours, over a regression whose only load input
  is a week old. The pre-registered 48-hour-gap row measures this (below): the gap costs
  about 4% on DOM and nothing on JC over the week, and 15 to 19% on day 1.
- The comparator is not the strongest simple model. LightGBM on the same inputs has a
  ratio of 0.857 (0.751 to 0.963) on JC and 0.947 (0.856 to 1.031) on DOM. Against
  LightGBM, Chronos-2's lead on JC is about 5% and on DOM about 23% (point values; no
  interval was computed for that pair).
- On DOM the regression is fitted on a trailing year of a growing load and
  underpredicted by about 2% in the year before the scored window.

## Secondary results

All secondary; none changes the sentences above. Intervals are 90%.

| Result | DOM | JC |
|---|---|---|
| Chronos-2 + temperature vs. regression, oracle regime | 0.663 (0.579 to 0.759) | 0.698 (0.589 to 0.824) |
| Chronos-2 without weather vs. regression, forecast regime | 1.342 (1.173 to 1.528) | 1.088 (0.939 to 1.241) |
| Weather gain, Chronos-2, forecast regime (with / without) | 0.544 (0.487 to 0.612) | 0.751 (0.662 to 0.852) |
| Weather gain, regression, forecast regime | 0.656 | 0.763 |
| Cost of forecast weather, Chronos-2 (forecast / oracle) | 1.414 (1.310 to 1.537) | 1.306 (1.208 to 1.412) |
| Cost of forecast weather, regression | 1.285 | 1.116 |

Chronos-2 with temperature vs. the regression by horizon day, forecast regime:

| Zone | Day 1 | Day 2 | Day 3 | Day 4 | Day 5 | Day 6 | Day 7 |
|---|---|---|---|---|---|---|---|
| DOM | 0.63 | 0.68 | 0.72 | 0.78 | 0.75 | 0.76 | 0.75 |
| JC | 0.64 | 0.76 | 0.94 | 0.88 | 0.89 | 0.79 | 0.77 |

On DOM every day's interval is below 1. On JC the intervals for days 3 to 5 include 1.
Day 1 is the closest to the GB study's day-ahead setting, and there the model leads in
both zones (DOM 0.55 to 0.74, JC 0.54 to 0.77), with the idealised-information caveat
at its strongest. Full table with intervals: `stats.csv`.

- Without weather, Chronos-2 is worse than the temperature regression on DOM and no
  better on JC. Its lead comes from using temperature well, not from the load history
  alone.
- Forecast weather costs Chronos-2 more than it costs the regression in both zones.

### TimesFM 2.5 (univariate, secondary)

Run through FoundationForecast, whose TimesFM 2.5 wrapper has no covariate path, so the
row uses load history only. Weights `google/timesfm-2.5-200m-pytorch` revision
`1d952420`, file committed 2025-10-01; 48 of 48 scored weeks start after that date.

| Comparison, forecast regime | DOM | JC |
|---|---|---|
| TimesFM 2.5 vs. the temperature-only regression | 1.328 (1.169 to 1.502) | 1.117 (0.969 to 1.274) |
| TimesFM 2.5 vs. Chronos-2 without weather | 0.990 (0.910 to 1.077) | 1.027 (0.967 to 1.089) |

- Without weather the two foundation models are indistinguishable. Both lose to a
  regression that has temperature on DOM, and neither beats it on JC.
- On horizon day 1 TimesFM 2.5 is slightly ahead of the regression (0.94 on DOM, 0.90
  on JC); from day 2 it is behind (1.41 to 1.50 on DOM, 1.07 to 1.22 on JC).
- This is the weather-free pattern the GB study reports: a foundation model without
  weather does not beat a regression that has it.

### Chronos-2 with a 48-hour data gap (pre-registered secondary)

The load context ends 48 hours before the cutoff; weather inputs are unchanged. The
regression is not rerun: its only load input is a week old, so the gap does not touch it.

| Forecast regime | DOM | JC |
|---|---|---|
| Gap row vs. the temperature-only regression | 0.762 (0.683 to 0.849) | 0.803 (0.671 to 0.943) |
| Cost of the gap (gap / no gap), whole week | 1.045 (0.991 to 1.104) | 0.984 (0.936 to 1.041) |
| Cost of the gap, day 1 | 1.193 (1.044 to 1.358) | 1.151 (0.967 to 1.374) |
| Gap row vs. regression, day 1 | 0.757 (0.612 to 0.934) | 0.741 (0.579 to 0.948) |

- The idealised cutoff explains little of the week-ahead result. With realistic data
  latency the verdicts stay the same: DOM below 0.90, JC crossing it.
- The gap matters on day 1 only, where the lead shrinks from about 0.63 to about 0.75.

### TimesFM 2.5 with temperature (secondary)

Direct adapter (`models_ff/timesfm25_xreg.py`) using the package's
`forecast_with_covariates`, configured as in the GB study: mode "xreg + timesfm",
temperature as the one covariate. The model has no covariate input; this method fits a
straight line of load on temperature over the context and lets TimesFM forecast the rest.

| Forecast regime | DOM | JC |
|---|---|---|
| vs. the temperature-only regression | 1.218 (1.027 to 1.454) | 1.120 (0.949 to 1.315) |
| Weather gain (with / without temperature) | 0.917 (0.798 to 1.071) | 1.003 (0.884 to 1.148) |

- Temperature gives TimesFM 2.5 no reliable gain here (the GB study reports 6%). A
  straight line cannot represent load that rises in both heat and cold; on the gate
  weeks, where the context is summer and the horizon is autumn, it made the forecast
  about twice as bad. Temperature squared was not added: the settings were fixed before
  scoring to match the GB study.

### Timestral with temperature (secondary, NOT out-of-sample)

Run through FoundationForecast with temperature as a known-future covariate. Its only
weights file was committed on 2026-10-15, so **1 of 48 scored weeks starts after the
weights**. The model may have been trained on the weeks it is scored on. The ratio on
the weeks after the weights, which the protocol asks for, rests on that single week and
is not reported.

| Regime | DOM | JC |
|---|---|---|
| Forecast, vs. the temperature-only regression | 0.656 (0.608 to 0.709) | 0.698 (0.599 to 0.802) |
| Oracle, vs. the temperature-only regression | 0.486 (0.442 to 0.537) | 0.543 (0.468 to 0.631) |

It is the lowest error on the board in every zone and regime. That cannot be told apart
from leakage with this window; see the open research task in `DECISIONS.md`.

### Against the field's standard benchmark (protocol-v1.1, secondary)

Added on Nov 13, 2026 after a search for the field's standard baselines
(`BASELINES.md`). Tao's Vanilla Benchmark is one regression with no lagged load: month,
day of week by hour, and a cubic in temperature by month and by hour, fitted on two
years. Two forms were registered before scoring (`protocol-v1.1.yaml`): as written in
Ziel and Liu (2016), and the same with a linear trend. Both were scored once at commit
`5185461`. Intervals are 90%.

| Forecast regime | DOM | JC |
|---|---|---|
| Vanilla vs. the lag regression with temperature | 1.386 (1.245 to 1.540) | 0.814 (0.717 to 0.914) |
| Vanilla with trend vs. the lag regression with temperature | 0.772 (0.724 to 0.825) | 0.819 (0.722 to 0.919) |
| **Chronos-2 + temperature vs. Vanilla with trend** | **0.946 (0.885 to 1.011)** | **0.997 (0.903 to 1.088)** |
| Chronos-2 + temperature vs. Vanilla | 0.527 (0.484 to 0.570) | 1.003 (0.908 to 1.097) |
| Chronos-2 + temperature, 48-hour gap, vs. Vanilla with trend | 0.988 (0.916 to 1.072) | 0.980 (0.887 to 1.068) |
| LightGBM + temperature vs. Vanilla with trend | 1.228 (1.146 to 1.309) | 1.046 (0.999 to 1.092) |
| Timestral + temperature vs. Vanilla with trend (not out-of-sample) | 0.850 (0.811 to 0.893) | 0.851 (0.795 to 0.910) |

- **The frozen baseline is weaker than the field's standard.** Vanilla with trend has
  23% less error than the lag regression with temperature on DOM and 18% less on JC.
- **Against Vanilla with trend, Chronos-2's lead is gone on JC and small on DOM.** Read
  with the same 10% bar: JC is a practical tie (the whole interval is inside 0.90 to
  1.10); DOM is inconclusive (the interval reaches below 0.90). With actual weather the
  point ratios are 1.085 on DOM and 1.007 on JC.
- **The trend term decides DOM.** Without it Vanilla is the worst temperature model on
  DOM, whose load is growing; on JC the two forms are the same. The trend form's
  provenance is weaker (see `protocol-v1.1.yaml`), which is why both are shown.
- **The primary outcome is unchanged** because the protocol fixed its baseline in
  advance: DOM 0.730, JC 0.817 against the lag regression with temperature. What changes
  is how much weight that outcome can bear: it shows Chronos-2 beats that regression,
  not that it beats a standard load-forecasting regression. Against the standard one,
  the GB study's "rough tie" largely reappears.

## Leaderboard

Mean absolute error over each 168-hour window, averaged over 48 windows, in MW.
Ratio is against the lag regression with temperature in the same zone and regime.

| Model | Zone | Regime | MAE | MAPE % | MASE | Ratio |
|---|---|---|---|---|---|---|
| Seasonal naive | DOM | forecast | 1,619 | 9.5 | 1.06 | 1.61 |
| Lag regression | DOM | forecast | 1,533 | 8.8 | 1.00 | 1.52 |
| Lag regression + temperature | DOM | forecast | 1,005 | 5.8 | 0.66 | 1.00 |
| LightGBM + temperature | DOM | forecast | 952 | 5.6 | 0.62 | 0.95 |
| Chronos-2, no weather | DOM | forecast | 1,349 | 7.9 | 0.89 | 1.34 |
| Chronos-2 + temperature | DOM | forecast | 734 | 4.3 | 0.48 | 0.73 |
| TimesFM 2.5, univariate | DOM | forecast | 1,336 | 7.8 | 0.88 | 1.33 |
| Chronos-2 + temperature, 48-hour gap | DOM | forecast | 766 | 4.5 | 0.50 | 0.76 |
| TimesFM 2.5 + temperature | DOM | forecast | 1,224 | 7.5 | 0.80 | 1.22 |
| Timestral + temperature (weights inside the window) | DOM | forecast | 660 | 3.8 | 0.43 | 0.66 |
| Seasonal naive | DOM | oracle | 1,619 | 9.5 | 1.06 | 2.07 |
| Lag regression | DOM | oracle | 1,533 | 8.8 | 1.00 | 1.96 |
| Lag regression + temperature | DOM | oracle | 782 | 4.5 | 0.51 | 1.00 |
| LightGBM + temperature | DOM | oracle | 736 | 4.4 | 0.48 | 0.94 |
| Chronos-2, no weather | DOM | oracle | 1,349 | 7.9 | 0.89 | 1.72 |
| Chronos-2 + temperature | DOM | oracle | 519 | 3.1 | 0.34 | 0.66 |
| TimesFM 2.5, univariate | DOM | oracle | 1,336 | 7.8 | 0.88 | 1.71 |
| Chronos-2 + temperature, 48-hour gap | DOM | oracle | 572 | 3.4 | 0.38 | 0.73 |
| TimesFM 2.5 + temperature | DOM | oracle | 1,114 | 6.8 | 0.73 | 1.42 |
| Timestral + temperature (weights inside the window) | DOM | oracle | 380 | 2.3 | 0.25 | 0.49 |
| Seasonal naive | JC | forecast | 377 | 13.8 | 1.03 | 1.41 |
| Lag regression | JC | forecast | 350 | 13.1 | 0.96 | 1.31 |
| Lag regression + temperature | JC | forecast | 267 | 10.2 | 0.74 | 1.00 |
| LightGBM + temperature | JC | forecast | 229 | 8.7 | 0.63 | 0.86 |
| Chronos-2, no weather | JC | forecast | 290 | 10.5 | 0.80 | 1.09 |
| Chronos-2 + temperature | JC | forecast | 218 | 8.0 | 0.60 | 0.82 |
| TimesFM 2.5, univariate | JC | forecast | 298 | 10.8 | 0.82 | 1.12 |
| Chronos-2 + temperature, 48-hour gap | JC | forecast | 214 | 7.9 | 0.59 | 0.80 |
| TimesFM 2.5 + temperature | JC | forecast | 299 | 11.7 | 0.82 | 1.12 |
| Timestral + temperature (weights inside the window) | JC | forecast | 186 | 6.9 | 0.51 | 0.70 |
| Seasonal naive | JC | oracle | 377 | 13.8 | 1.03 | 1.58 |
| Lag regression | JC | oracle | 350 | 13.1 | 0.96 | 1.46 |
| Lag regression + temperature | JC | oracle | 239 | 9.3 | 0.66 | 1.00 |
| LightGBM + temperature | JC | oracle | 179 | 7.0 | 0.49 | 0.75 |
| Chronos-2, no weather | JC | oracle | 290 | 10.5 | 0.80 | 1.21 |
| Chronos-2 + temperature | JC | oracle | 167 | 6.3 | 0.46 | 0.70 |
| TimesFM 2.5, univariate | JC | oracle | 298 | 10.8 | 0.82 | 1.25 |
| Chronos-2 + temperature, 48-hour gap | JC | oracle | 170 | 6.3 | 0.47 | 0.71 |
| TimesFM 2.5 + temperature | JC | oracle | 266 | 10.5 | 0.73 | 1.11 |
| Timestral + temperature (weights inside the window) | JC | oracle | 130 | 4.9 | 0.36 | 0.54 |

Seasonal naive, the lag regression, Chronos-2 without weather and TimesFM 2.5 use no
weather, so their rows are the same in both regimes. Full precision, per-horizon-day errors and run metadata are in
`leaderboard.parquet` and `leaderboard.csv`; per-window errors in `windows.parquet`;
hourly forecasts in `forecasts/`.

Intervals for every ratio against the baseline are in `stats.csv`.

## Dropped windows

48 of 52 windows are scored in each zone, as `protocol.yaml` expected. EIA has no rows
for the days of the clock changes (2026-03-08 and 2026-11-01). Origins 2026-03-02 and
2026-10-26 lack actuals; origins 2026-03-09 and 2026-11-02 lack the 168-hour lag. The
list is in `dropped_windows.csv`.

## What stands out in the baselines

- **The lag regression without temperature barely beats seasonal naive**: 5% on DOM
  and 7% on JC. In the GB study the regression's error was 0.74 of naive's, but that
  regression also had a 2-day lag and a day-ahead horizon.
- **Temperature is worth a lot.** With reanalysis temperature the regression's error
  falls to 0.51 of the weather-free regression's on DOM and 0.68 on JC.
- **Forecast weather costs DOM far more than JC.** Moving from reanalysis to archived
  forecasts raises the temperature regression's error by 29% on DOM and 12% on JC.
  On DOM the error at horizon day 7 is 1,281 MW with forecast weather against 782 MW
  with reanalysis; at day 1 the two are close (801 against 775).
- **LightGBM on the same inputs beats the regression on JC** (ratio 0.86 with forecast
  weather, 0.75 with reanalysis) and is slightly ahead on DOM (0.95, 0.94). So the
  headline comparator is not the strongest simple model available on JC. It stays the
  comparator because the protocol fixed it before scoring.
- **Runtime is negligible**: about 0.03 s per forecast for the regressions, 0.1 s for
  LightGBM, and well under a second for Chronos-2 on CPU.

## Gate history

All gate checks passed before the tag (`tests/test_gates.py`, 11 tests). The row-ordering
check first failed on the four usable gate weeks in October 2025, where the weather-free
regression was worse than seasonal naive. It was moved to the 52 Mondays before the gate
set, where it passes; the reason is in `protocol.yaml` under `gate_history`. Gate-stage
results are in `gate/` and `ordering_gate/` and are not scored results.

## Cross-check through FoundationForecast

Not a leaderboard row. Chronos-2 run through FoundationForecast (installed from GitHub
at commit `cd67b608`, separate environment `models_ff/`) on the six gate origins agrees
with the direct adapter to within 0.003 MW on every one of 8,064 hourly forecasts.
Details in `notes/foundationforecast.md`; values in `gate/crosscheck/chronos2_ff.parquet`.

## Not done

- Stronger classical rungs: Vanilla with recency terms, an additive model (GAM),
  tuned LightGBM (`notes/classical_baselines.md`).
- A fair test of Timestral and other models whose weights fall inside the scored
  window (open research task in `DECISIONS.md`).
- TimesFM 2.5 with a curved temperature term.
- Other foundation models.
- Vanilla + recency regression row (optional in the brief).
