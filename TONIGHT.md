# Task brief: Thursday night (about 3 hours)

Goal: a frozen backtest protocol and a baseline leaderboard for JC and DOM.
Nothing else. Foundation models, skills, and the judge are Friday's work.

Details for every step (query templates, formula, coordinates) are in `REFERENCE.md`.

## Steps

1. **Project setup (15 min)**
   - `uv` project, Python 3.12, `core/` environment only.
   - `.gitignore` covering `.env`, `data/raw/`, model caches.
   - Expect `EIA_API_KEY` in `.env`. If missing, stop and ask.

2. **Load data (40 min)** in `fetch.py`
   - EIA hourly demand for PJM sub-regions JC and DOM, 2019-01-01 to latest.
   - Verify the facet names and the timestamp convention (UTC? hour-ending?) against
     a live response before bulk paging.
   - Checks: expected hour count, duplicates, gaps. Fill gaps of 3 hours or less by
     interpolation; log every filled or flagged value to `data/quality_log.csv`.
   - Output `data/processed/load.parquet` (`unique_id, ds, y`).

3. **Weather data (30 min)** in `fetch.py`
   - Oracle regime: Open-Meteo archive, hourly `temperature_2m`, per station.
   - Forecast regime: Open-Meteo Previous Runs, lead-day 1 to 7 temperature.
     Verify the variable names and how far back the archive goes.
   - Check whether wind speed and solar radiation are available the same way in both
     regimes. If yes, pull them too. If not, temperature only; record which.
   - Average stations to one series per zone.
   - Output `weather_oracle.parquet` and `weather_forecast.parquet`.
   - Write SHA-256 of every raw file to `fetch_manifest.json`.

4. **Freeze the protocol (20 min)**
   - Write `protocol.yaml`: zones, h=168, origins, regimes, station list, training
     window, weather variables, metrics, bootstrap seed and draws, the "worth
     switching" bar, one pre-written sentence per possible outcome, and the
     train-on-reanalysis / predict-on-forecast caveat (see `REFERENCE.md`).
   - Origins: 52 consecutive Mondays 00:00 America/New_York. The last origin is the
     latest Monday whose full 168 hours of actuals are already in the data.
   - If the forecast-weather archive does not cover all 52 origins, record the
     shorter window for that regime in the protocol. Do not shrink the oracle window.
   - Commit, `git tag protocol-v1`, push with tags.

5. **Harness and baselines (60 min)**
   - Backtest loop over origins from `protocol.yaml`.
   - Rows, in this order:
     1. seasonal-naive (same hour 168 h earlier)
     2. lag regression, no weather (per-hour fits, trailing 365 days)
     3. lag regression + weather: the headline comparator
     4. Vanilla + recency weather regression (trailing 2-year fit), if time allows
   - Rows 1 and 2 use no weather, so they are identical in both regimes.
   - Metrics per row: MAPE, MAE, RMSE, MASE (scaled by seasonal-naive-168), and
     error ratio vs. row 3. Bootstrap intervals can wait until Friday.
   - Smoke-test on 2 origins, then run all, both regimes.
   - Output `results/leaderboard.parquet` and per-window forecasts.

6. **If time remains: LightGBM row** on exactly row 3's input columns.

## Acceptance criteria

- [ ] `protocol.yaml` exists, is tagged `protocol-v1`, and the tag is pushed.
- [ ] `fetch_manifest.json` hashes match the raw files.
- [ ] Leaderboard has rows 1 to 3 for both zones and both regimes, each with n_windows stated.
- [ ] Row 2 beats row 1, and row 3 beats row 2 in the oracle regime, for both zones.
      If not, the likely causes are timezone alignment or feature bugs: investigate
      before adding anything else.
- [ ] A short `results/README.md` states the numbers and anything surprising.

## Out of scope tonight

Foundation models, FoundationForecast, skills, `spec.yaml`, the judge, You.com,
any dashboard.

## Leave running overnight (only after the criteria above pass)

- Create the `models/` environment.
- Download weights: `amazon/chronos-2` first; others as listed in `REFERENCE.md`.
  Needs `HF_TOKEN` in `.env` for gated models.
- Optional: Chronos-2 via the direct adapter on both regimes, written as new rows.
