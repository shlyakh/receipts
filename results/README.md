# Baseline results, protocol-v1

Scored once on Thu Nov 12, 2026, at commit `912a902`, the commit tagged `protocol-v1`.
52 Monday origins from 2025-11-10 to 2026-11-02, 168-hour horizon, zones JC and DOM.

Baselines were scored on Thu Nov 12, 2026 at commit `912a902`. Chronos-2 was scored
once on Fri Nov 13, 2026 at commit `2029bad`, against the same unchanged protocol.

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
  is a week old. The pre-registered 48-hour-gap row that measures this is not run yet.
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
| Seasonal naive | DOM | oracle | 1,619 | 9.5 | 1.06 | 2.07 |
| Lag regression | DOM | oracle | 1,533 | 8.8 | 1.00 | 1.96 |
| Lag regression + temperature | DOM | oracle | 782 | 4.5 | 0.51 | 1.00 |
| LightGBM + temperature | DOM | oracle | 736 | 4.4 | 0.48 | 0.94 |
| Chronos-2, no weather | DOM | oracle | 1,349 | 7.9 | 0.89 | 1.72 |
| Chronos-2 + temperature | DOM | oracle | 519 | 3.1 | 0.34 | 0.66 |
| Seasonal naive | JC | forecast | 377 | 13.8 | 1.03 | 1.41 |
| Lag regression | JC | forecast | 350 | 13.1 | 0.96 | 1.31 |
| Lag regression + temperature | JC | forecast | 267 | 10.2 | 0.74 | 1.00 |
| LightGBM + temperature | JC | forecast | 229 | 8.7 | 0.63 | 0.86 |
| Chronos-2, no weather | JC | forecast | 290 | 10.5 | 0.80 | 1.09 |
| Chronos-2 + temperature | JC | forecast | 218 | 8.0 | 0.60 | 0.82 |
| Seasonal naive | JC | oracle | 377 | 13.8 | 1.03 | 1.58 |
| Lag regression | JC | oracle | 350 | 13.1 | 0.96 | 1.46 |
| Lag regression + temperature | JC | oracle | 239 | 9.3 | 0.66 | 1.00 |
| LightGBM + temperature | JC | oracle | 179 | 7.0 | 0.49 | 0.75 |
| Chronos-2, no weather | JC | oracle | 290 | 10.5 | 0.80 | 1.21 |
| Chronos-2 + temperature | JC | oracle | 167 | 6.3 | 0.46 | 0.70 |

Seasonal naive, the lag regression and Chronos-2 without weather use no weather, so
their rows are the same in both regimes. Full precision, per-horizon-day errors and run metadata are in
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

- Chronos-2 with a 48-hour data gap (pre-registered secondary).
- TimesFM 2.5, Timestral and other foundation models.
- Vanilla + recency regression row (optional in the brief).
