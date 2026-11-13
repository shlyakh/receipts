# Baseline results, protocol-v1

Scored once on Thu Nov 12, 2026, at commit `912a902`, the commit tagged `protocol-v1`.
52 Monday origins from 2025-11-10 to 2026-11-02, 168-hour horizon, zones JC and DOM.

These are baselines only. The primary comparison in `protocol.yaml` (Chronos-2 against
the temperature-only regression, forecast regime) has no result yet: no foundation
model has been run.

## Leaderboard

Mean absolute error over each 168-hour window, averaged over 48 windows, in MW.
Ratio is against the lag regression with temperature in the same zone and regime.

| Model | Zone | Regime | MAE | MAPE % | MASE | Ratio |
|---|---|---|---|---|---|---|
| Seasonal naive | DOM | forecast | 1,619 | 9.5 | 1.06 | 1.61 |
| Lag regression | DOM | forecast | 1,533 | 8.8 | 1.00 | 1.52 |
| Lag regression + temperature | DOM | forecast | 1,005 | 5.8 | 0.66 | 1.00 |
| LightGBM + temperature | DOM | forecast | 952 | 5.6 | 0.62 | 0.95 |
| Seasonal naive | DOM | oracle | 1,619 | 9.5 | 1.06 | 2.07 |
| Lag regression | DOM | oracle | 1,533 | 8.8 | 1.00 | 1.96 |
| Lag regression + temperature | DOM | oracle | 782 | 4.5 | 0.51 | 1.00 |
| LightGBM + temperature | DOM | oracle | 736 | 4.4 | 0.48 | 0.94 |
| Seasonal naive | JC | forecast | 377 | 13.8 | 1.03 | 1.41 |
| Lag regression | JC | forecast | 350 | 13.1 | 0.96 | 1.31 |
| Lag regression + temperature | JC | forecast | 267 | 10.2 | 0.74 | 1.00 |
| LightGBM + temperature | JC | forecast | 229 | 8.7 | 0.63 | 0.86 |
| Seasonal naive | JC | oracle | 377 | 13.8 | 1.03 | 1.58 |
| Lag regression | JC | oracle | 350 | 13.1 | 0.96 | 1.46 |
| Lag regression + temperature | JC | oracle | 239 | 9.3 | 0.66 | 1.00 |
| LightGBM + temperature | JC | oracle | 179 | 7.0 | 0.49 | 0.75 |

Seasonal naive and the lag regression use no weather, so their rows are the same in
both regimes. Full precision, per-horizon-day errors and run metadata are in
`leaderboard.parquet` and `leaderboard.csv`; per-window errors in `windows.parquet`;
hourly forecasts in `forecasts/`.

No bootstrap intervals yet: they are Friday's work, so none of the ratios above has an
uncertainty attached.

## Dropped windows

48 of 52 windows are scored in each zone, as `protocol.yaml` expected. EIA has no rows
for the days of the clock changes (2026-03-08 and 2026-11-01). Origins 2026-03-02 and
2026-10-26 lack actuals; origins 2026-03-09 and 2026-11-02 lack the 168-hour lag. The
list is in `dropped_windows.csv`.

## What stands out

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
- **Runtime is negligible**: about 0.03 s per forecast for the regressions and 0.1 s
  for LightGBM.

## Gate history

All gate checks passed before the tag (`tests/test_gates.py`, 11 tests). The row-ordering
check first failed on the four usable gate weeks in October 2025, where the weather-free
regression was worse than seasonal naive. It was moved to the 52 Mondays before the gate
set, where it passes; the reason is in `protocol.yaml` under `gate_history`. Gate-stage
results are in `gate/` and `ordering_gate/` and are not scored results.

## Not done

- Vanilla + recency regression row (optional in the brief).
- Bootstrap intervals.
- Any foundation model.
