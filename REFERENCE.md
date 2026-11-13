# Reference

Condensed from two research passes on Nov 12, 2026. Items under "Unverified" at the
end were not confirmed against a primary source: check them before relying on them.

## Load data: EIA Open Data API v2

Free key: https://www.eia.gov/opendata/register.php

```
https://api.eia.gov/v2/electricity/rto/region-sub-ba-data/data/
  ?api_key=$EIA_API_KEY
  &frequency=hourly&data[0]=value
  &facets[parent][]=PJM&facets[subba][]=JC&facets[subba][]=DOM
  &start=2019-01-01T00&end=<latest>
  &sort[0][column]=period&sort[0][direction]=asc
  &offset=0&length=5000
```

- Page with `offset`. Values arrive as strings.
- Operator-reported, not settlement data; expect a 1 to 2 day lag, some gaps and
  outliers.
- Later upgrade: PJM Data Miner 2 `hrl_load_metered` (needs account + subscription;
  no redistribution).

## Weather: Open-Meteo (free, no key)

- Oracle regime: `https://archive-api.open-meteo.com/v1/archive`, hourly
  `temperature_2m` (ERA5, about 5 days behind real time).
- Forecast regime: Previous Runs API, `temperature_2m_previous_day1` ..
  `previous_day7` = the value forecast N days before the valid time. Reported to be
  archived from January 2024. Horizon day k uses `previous_dayk`.
- `protocol-v1` uses temperature only (decision 17). The GB study also uses wind
  speed and solar radiation (see `notes/moran.md`). If Previous Runs serves
  `wind_speed_10m`, `shortwave_radiation` and `dew_point_2m` at lead days 1 to 7,
  download and hash them for a later protocol version, but do not use them.

Station points (a judgment call, not an official PJM mapping; write the final list
into `protocol.yaml`):

| Zone | Points (lat, lon) |
|------|-------------------|
| JC   | Morristown (40.80, -74.48); Monmouth shore (40.19, -74.06); Toms River (39.95, -74.20) |
| DOM  | Richmond (37.54, -77.43); Norfolk (36.85, -76.29); Dulles / N. Virginia (38.95, -77.45) |

DOM note: Northern Virginia data-center load is weather-insensitive and growing, so
a linear trend on a 2-year window may lag. The `y_lag168` regression variant is the
check on that.

## Weather regression baseline (Vanilla + recency)

Tao Hong's "Vanilla" benchmark with recency terms. No lagged load, so no recursion
is needed at h=168.

```python
import statsmodels.formula.api as smf

FORMULA = (
    "y ~ trend + C(month) + C(dow)*C(hour) + C(hol)"
    " + (T + I(T**2) + I(T**3))*(C(month) + C(hour))"
    " + T_lag1 + T_lag2 + T_lag3 + T_ma24 + T_ma24_lag24"
)

def fit_predict(train, test):   # train: trailing 2 years before cutoff; test: 168 h
    return smf.ols(FORMULA, data=train).fit().predict(test)
```

- Refit at every weekly origin.
- Temperature lags and moving averages over the horizon must be built from the
  active regime's temperature series (observed before the cutoff, regime series
  after it).
- Second row: same formula plus `y_lag168`.
- This model is a secondary, lag-free baseline. The LightGBM row does NOT use its
  columns: it uses exactly the lag regression's inputs (next section), namely
  `y_lag168`, hour, day of week, holiday, year-end indicator and `T`.

## Lag regression (adapted from the GB study): the headline comparator

The GB study's regression is one least-squares fit per clock slot with lagged
demand, calendar terms and weather terms (`notes/moran.md`). Adapted to a 168-hour
horizon: the 2-day lag is not available across the horizon, the 7-day lag always is.

- One OLS fit per local hour of day (24 fits), refit at every origin on the trailing
  365 days of complete data before the cutoff.
- Base terms: intercept; `y_lag168`; six day-of-week indicators (Monday base);
  US federal holiday; 24 Dec to 2 Jan indicator.
- Weather terms in `protocol-v1`: `Tc` (temperature minus its mean over the fit
  rows) and `Tc**2` only. The code below also handles `wind`, `Tc*wind` and `solar`
  for a later protocol version; pass `weather_cols=["T"]` for v1.
- Two rows: without weather terms ("lag regression") and with them ("lag regression
  + temperature"). The second is the baseline every model is compared against;
  call it the "temperature-only regression" in any receipt. The ratio between the
  two is the regression's weather gain.
- Seasonal naive = the same hour 168 hours earlier.
- Write our own implementation. A second, independent implementation that agrees to
  0.1 MW on three sample origins is a cheap and convincing check.

```python
import numpy as np

def fit_predict_hour(train, test, weather_cols):
    # train/test: rows for ONE local hour of day; columns y, y_lag168, dow, hol, yearend, T, ...
    def design(df, tbar):
        X = [np.ones(len(df)), df.y_lag168.to_numpy()]
        X += [(df.dow == k).to_numpy(float) for k in range(1, 7)]
        X += [df.hol.to_numpy(float), df.yearend.to_numpy(float)]
        if "T" in weather_cols:
            tc = df["T"].to_numpy() - tbar
            X += [tc, tc**2]
            if "wind" in weather_cols:
                X += [df.wind.to_numpy(), tc * df.wind.to_numpy()]
        if "solar" in weather_cols:
            X += [df.solar.to_numpy()]
        return np.column_stack(X)
    tbar = train["T"].mean() if "T" in weather_cols else 0.0
    b, *_ = np.linalg.lstsq(design(train, tbar), train.y.to_numpy(), rcond=None)
    return design(test, tbar) @ b
```

The Vanilla + recency model above stays as a second, lag-free weather baseline.

Known caveat to write into `protocol.yaml`: in the forecast regime the regression
trains on reanalysis and predicts with forecast weather. The GB study puts that
mismatch at 100 to 200 MW in its cool months.

## Metrics and headline statistic

- MAPE, MAE, RMSE, MASE (scaled by in-sample seasonal-naive-168).
- Probabilistic models: pinball loss at q = 0.1 .. 0.9 and 80% interval coverage.
- Headline: error ratio vs. the lag regression with temperature. Per-window error =
  MAE over the 168 hours; ratio = mean window error of A / mean window error of B.
- Primary comparison (decision 15): Chronos-2 with temperature vs. that regression,
  forecast regime, per zone. Verdict from the whole 90% interval against 0.90 and
  1.10: worth switching / practical tie (claim transfers) / regression clearly
  better / inconclusive. All other results are secondary.
- Per-lead-day ratio (secondary): the same ratio computed on the 24 hours of
  horizon day k, for k = 1 .. 7. Day 1 is closest to the GB study's setting.
- 48-hour-gap row (secondary): Chronos-2 with its context ending 48 hours before
  the cutoff, forecasting 216 hours, scored on the same 168.
- Leakage per model: pin the weights revision; report `n_windows_after_weights`
  and, where that is below `n_windows`, the ratio on the post-weights windows.
- Intervals: bootstrap over whole weeks (each origin is one block), 2,000 draws,
  fixed seed in `protocol.yaml`, the same resampled weeks for both arms; 90%
  percentile intervals.
- Also report each forecaster's weather gain: with weather / without weather.
- Pre-set a "worth switching" bar in the protocol (the GB study used 10%) and write
  one result sentence per possible outcome before scoring.
- A window that cannot be built for one forecaster is dropped for all, and listed.

## Foundation models (Friday)

Harness-owned loop, one call per cutoff:

```python
from foundationforecast import FoundationForecast
from foundationforecast.models import Chronos

ff = FoundationForecast(models=[Chronos(repo_id="amazon/chronos-2", alias="Chronos-2")])
out = []
for cutoff in CUTOFFS:                      # from protocol.yaml
    hist = panel[panel.ds <= cutoff]        # unique_id, ds, y, T
    X = horizon_weather(cutoff, regime)     # unique_id, ds, T for the next 168 h
    fc = ff.forecast(df=hist, h=168, freq="h", X_df=X, level=[80])
    out.append(fc.assign(cutoff=cutoff, regime=regime))
```

Direct Chronos-2 fallback:

```python
from chronos import Chronos2Pipeline
pipe = Chronos2Pipeline.from_pretrained("amazon/chronos-2", device_map="cpu")
pred = pipe.predict_df(hist.rename(columns={"y": "target"}), future_df=X,
                       prediction_length=168, quantile_levels=[0.1, 0.5, 0.9],
                       id_column="unique_id", timestamp_column="ds", target="target")
```

Candidate rows and notes:

| Model | HF id | Covariates | Notes |
|-------|-------|------------|-------|
| Chronos-2 | `amazon/chronos-2` | known-future | first row to add |
| Timestral | `mistralai/Timestral-209M` (also `-5M`) | known-future | Modified MIT weights |
| t0-gamma | `theforecastingcompany/t0-gamma` | known-future | not gated as of Nov 13, 2026 (the earlier note said gated) |
| TiRex-2 | `NX-AI/TiRex-2` | per FF docs | Apache-2.0 |
| TimesFM 2.5 | `google/timesfm-2.5-200m-pytorch` | treat as univariate | |
| TimesFM-3 | `google/timesfm-3.0-pytorch` | past + known-future | non-commercial weights |
| Kumo Forecast | `nvidia/Kumo-Forecast` | none | point only; intervals via conformal; native horizon 72, so 168 h is a rollout |

Direct-adapter settings used in the GB study (`notes/moran.md`): Chronos-2 with
weather as both past and future covariates, no cross-learning, median as the point
forecast (`chronos-forecasting` 2.3.2); Timestral with known covariates and
symmetric averaging; TimesFM 2.5 through `forecast_with_covariates`.

Speed-ups: batch both zones in one call; cap context at 2,048 to 4,096 hours; score
26 windows first; calibrate conformal intervals once, not per cutoff.

## spec.yaml (Friday)

```yaml
problem: hourly zonal electric load, PJM JC & DOM
horizon_hours: 168
frequency: hourly
issue_time: "Mon 00:00 America/New_York"
covariates:
  required: [temperature_2m]
  known_future: true
  regimes: [oracle, forecast]
baseline_to_beat: lag_regression_temperature
primary_comparison: {model: chronos-2, regime: forecast, bar: 0.10}
runnable_class:
  sources: [huggingface, pypi, foundationforecast]
  cpu_ok: true
  max_runtime_min: 60
license_policy: {prefer: [Apache-2.0, MIT], flag_noncommercial: true}
metrics: [MAPE, MAE, RMSE, MASE, pinball, coverage80, error_ratio_vs_regression]
min_evidence: {test_window_days: 90, primary_source_required: true}
missing_source_rule: cap at PARTIAL unless candidate_type is model_release and runnable
excluded_sources: [linkedin.com]
```

## Scorecard schema (Friday)

```json
{
  "candidate_id": "str",
  "title": "str",
  "discovered_via": {"url": "str", "provider": "claude|youcom|manual", "retrieved_at": "iso8601"},
  "candidate_type": "model_release|library_feature|practitioner_backtest|paper|vendor_claim|off_target",
  "primary_sources": [{"url": "str", "kind": "hf_card|github|arxiv|zenodo|blog|docs", "quote": "str"}],
  "claims": [{
    "text": "str", "metric": "str", "value": "num", "dataset": "str", "horizon": "str",
    "baseline": "str", "baseline_same_inputs": "yes|no|unknown",
    "test_window_days": "int", "citation_idx": "int"
  }],
  "relevance": {"target_match": "0-3", "horizon_match": "0-3", "covariates_match": "0-3", "rationale": "str"},
  "checks": {
    "pre_registered": "yes|no|unknown",
    "training_overlap_risk": "low|med|high|unknown",
    "independent_replication": "yes|no|unknown"
  },
  "evidence_strength": "strong|moderate|weak|none",
  "license": "str",
  "license_ok_for_commercial": "bool",
  "runnable_class": "ff_native_exog|ff_univariate|direct_adapter|not_runnable",
  "label": "ACCEPT_RUN|ACCEPT_STAGE3|PARTIAL|REJECT",
  "implementation_hint": "str",
  "receipt": {
    "claimed": "str",
    "measured": {"error_ratio": "num", "ci90": ["num", "num"], "coverage80": "num"},
    "horizon_mismatch": "str",
    "n_windows_after_weights": "int",
    "verdict": "transfers|partially|does_not_transfer|untestable"
  }
}
```

Rules for the judge: when no primary source can be found, say so. Never invent one.
A claim with no primary source has an empty `citation_idx` and caps the label at
`PARTIAL` (see `missing_source_rule`). A LinkedIn URL may appear in
`discovered_via` as an identifier; it is never fetched and never a citation.

## Swappable search (Friday / Saturday)

Skills use three capabilities: `search(query, recency, domains)`, `fetch(url)`,
`research(question, schema)`. A `providers.md` maps each to the tools in the session.
Every result is normalised to
`{url, title, snippet, published_at, provider, retrieved_at, raw}` and appended to
`evidence/*.jsonl`. `/judge` reads only that ledger.

You.com MCP (Saturday):
`claude mcp add --transport http you-com https://api.you.com/mcp --header "Authorization: Bearer $YDC_API_KEY"`
The research tool must be requested explicitly (`?tools=you-search,you-contents,you-research`).

## Unverified: check before use

- EIA facet names (`parent`, `subba`), timestamp convention, per-zone start dates.
- Open-Meteo Previous Runs variable names and archive depth.
- FoundationForecast: model class names other than `Chronos`; whether `forecast()`
  takes `X_df` exactly as shown; `cross_validation()` argument names; MPS behaviour.
  Check with `python -c "import foundationforecast.models as m; print(dir(m))"`.
- `Chronos2Pipeline.predict_df` argument names (written from memory).
- All runtime estimates. Time one window per model first.
- The GB study's weather-run ratios (0.97x, 1.07x). The weather gains are in the
  description of Zenodo record 24161799; the ratios should be in the zip's
  `weather_study/RESULTS.md`, not yet opened (`notes/moran.md`). The weather-free
  results are verified.
- Whether Open-Meteo Previous Runs serves wind, solar and dew point at each lead
  day (only matters for a later protocol version).
- VERIFIED Nov 13, 2026 from the Hugging Face API: all eight model ids in the table
  above resolve and none is gated. Weights-file commit dates: Chronos-2 2025-10-30,
  TimesFM 2.5 2025-10-01, TimesFM-3 2026-08-24. Timestral-209M 2026-10-15 (single squashed commit).
  Not yet checked per file:
  t0-gamma, TiRex-2, Kumo Forecast (their repos changed in autumn 2026).
- Residual overlap for every model: earlier years of the same public series may be
  in training, so a model may know these zones' typical shape.
- That the Zenodo record is findable through You.com search (Friday smoke test).
