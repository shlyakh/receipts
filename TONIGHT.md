# Task brief: Thursday night (about 3 hours)

Goal: a frozen backtest protocol and a baseline leaderboard for JC and DOM.
Nothing else. Foundation models, skills, and the judge are Friday's work.

Details for every step (query templates, formula, coordinates) are in `REFERENCE.md`.

Order tonight: **draft the protocol, gate it on pre-window origins, tag it, then
score once.** The 52 scored origins are not run by any code that is later changed.

## Steps

1. **Project setup (15 min)**
   - `uv` project, Python 3.12, `core/` environment only.
   - `.gitignore` covering `.env`, `data/raw/`, model caches.
   - Expect `EIA_API_KEY` in this project's `.env` (not `~/.env`). If missing, stop
     and ask.

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
   - `protocol-v1` uses **temperature only** (decision 17). If wind speed, solar
     radiation and dew point are served the same way in both regimes, download and
     hash them too, but do not use them. Record which were available.
   - Average stations to one series per zone.
   - Output `weather_oracle.parquet` and `weather_forecast.parquet`.
   - Write SHA-256 of every raw file to `fetch_manifest.json`.

4. **Draft the protocol (20 min)**: write `protocol.yaml`, do NOT tag yet
   - Zones, h=168, origins, regimes, station list, training window, weather
     variables (temperature only, stated as a deliberate choice), metrics, bootstrap
     seed and draws.
   - Origins: 52 consecutive Mondays 00:00 America/New_York. The last origin is the
     latest Monday whose full 168 hours of actuals are already in the data.
   - Gate origins: the 4 Mondays immediately before the first scored origin. They
     are listed in the protocol and never scored.
   - If the forecast-weather archive does not cover all 52 origins, record the
     shorter window for that regime in the protocol. Do not shrink the oracle window.
   - Primary comparison, bar and outcome sentences: see "Primary comparison" below.
   - Secondary results, each labelled secondary: oracle regime; per-lead-day ratio
     (horizon day 1 to 7); weather gain per forecaster; other models; the Chronos-2
     48-hour-gap row (`FRIDAY.md`).
   - Named caveats: transfer test, not replication; idealised information set
     (load is visible up to the cutoff, which favours models that use recent
     context); the regression trains on reanalysis and predicts on forecast weather.

5. **Harness and baselines (60 min)**
   - Backtest loop over origins from `protocol.yaml`.
   - Rows, in this order:
     1. seasonal-naive (same hour 168 h earlier)
     2. lag regression, no weather (per-hour fits, trailing 365 days)
     3. lag regression + temperature: the headline comparator
     4. Vanilla + recency weather regression (trailing 2-year fit), if time allows
   - Rows 1 and 2 use no weather, so they are identical in both regimes.
   - Metrics per row: MAPE, MAE, RMSE, MASE (scaled by seasonal-naive-168), error
     ratio vs. row 3, and MAE per horizon day. Bootstrap intervals can wait until
     Friday.

6. **Gate checks, on the 4 gate origins only**
   - Timestamps align: local Monday 00:00 maps to the expected UTC hour in both
     winter and summer time.
   - No lookahead: for one origin, assert no input row is later than the cutoff
     except the regime's horizon weather.
   - Row ordering is sane: row 2 beats row 1, and row 3 beats row 2 in the oracle
     regime, for both zones. If not, the likely causes are timezone alignment or
     feature bugs: fix them now, before the tag.
   - `fetch_manifest.json` hashes match the raw files.
   - Fixing code or the draft protocol at this stage is allowed and is not a
     deviation.

7. **Freeze**
   - Yuri reads and approves the four outcome sentences.
   - Commit, `git tag protocol-v1`, push with tags.

8. **Score once**
   - Run all 52 origins, both regimes. This is the official run.
   - Any change after this point follows hard rule 5: a new protocol version and a
     dated line in `DEVIATIONS.md`. The failed or superseded run is kept.
   - Output `results/leaderboard.parquet` and per-window forecasts.

9. **If time remains: LightGBM row** on exactly row 3's input columns.

## Primary comparison (goes into `protocol.yaml`)

- Chronos-2 with temperature vs. the lag regression with temperature, **forecast**
  regime, reported per zone: two primary numbers.
- Statistic: ratio of mean per-window MAE, 90% whole-week bootstrap interval.
- Bar: 10%. The verdict is read from the whole interval:
  - entirely below 0.90: worth switching
  - entirely above 1.10: the regression is clearly better
  - entirely inside 0.90 to 1.10: practical tie; the GB claim transfers to this zone
  - anything else: inconclusive at 52 weeks
- One sentence per outcome, written before scoring. Drafts and an illustration:
  https://claude.ai/artifact/TSpY7YUQmdC9Yf7BetQGgC
- Everything else is secondary and cannot change the outcome sentence.

## Acceptance criteria

- [ ] All gate checks in step 6 passed on the gate origins before the tag.
- [ ] `protocol.yaml` exists, is tagged `protocol-v1`, and the tag is pushed.
- [ ] `fetch_manifest.json` hashes match the raw files.
- [ ] Leaderboard has rows 1 to 3 for both zones and both regimes, each with
      n_windows stated, from a single scored run.
- [ ] A short `results/README.md` states the numbers and anything surprising,
      including any row ordering on the scored window that differs from the gates.

## Out of scope tonight

Foundation models, FoundationForecast, skills, `spec.yaml`, the judge, You.com,
any dashboard.

## Leave running overnight (only after the criteria above pass)

- Create the `models/` environment.
- Verify that each Hugging Face id in `REFERENCE.md` resolves, that
  `foundationforecast` installs, and that gated models' terms are accepted. A model
  that fails is dropped from Friday. Write the result to
  `notes/foundationforecast.md`.
- Download weights at a pinned revision: `amazon/chronos-2` first, then TimesFM 2.5
  and Timestral. Record each revision hash and its commit date. Needs `HF_TOKEN` in
  `.env` for gated models.
- Optional: Chronos-2 via the direct adapter on both regimes, written as new rows.
