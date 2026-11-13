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
- Optional extra variable: `dew_point_2m`.

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
- LightGBM row: same columns as features, no load lags.

```python
FEATS = ["trend","month","dow","hour","hol","T",
         "T_lag1","T_lag2","T_lag3","T_ma24","T_ma24_lag24"]
```

## Metrics and headline statistic

- MAPE, MAE, RMSE, MASE (scaled by in-sample seasonal-naive-168).
- Probabilistic models: pinball loss at q = 0.1 .. 0.9 and 80% interval coverage.
- Headline: error ratio vs. the weather regression, with a week-block bootstrap 90%
  interval. Pre-set a "worth switching" bar (suggested 5%) in the protocol.

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
| t0-gamma | `theforecastingcompany/t0-gamma` | known-future | gated: accept terms, set `HF_TOKEN` |
| TiRex-2 | `NX-AI/TiRex-2` | per FF docs | Apache-2.0 |
| TimesFM 2.5 | `google/timesfm-2.5-200m-pytorch` | treat as univariate | |
| TimesFM-3 | `google/timesfm-3.0-pytorch` | past + known-future | non-commercial weights |
| Kumo Forecast | `nvidia/Kumo-Forecast` | none | point only; intervals via conformal; native horizon 72, so 168 h is a rollout |

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
baseline_to_beat: weather_regression_vanilla_recency
runnable_class:
  sources: [huggingface, pypi, foundationforecast]
  cpu_ok: true
  max_runtime_min: 60
license_policy: {prefer: [Apache-2.0, MIT], flag_noncommercial: true}
metrics: [MAPE, MAE, RMSE, MASE, pinball, coverage80, error_ratio_vs_regression]
min_evidence: {test_window_days: 90, primary_source_required: true}
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
    "verdict": "holds|partially|fails|untestable"
  }
}
```

Rule for the judge: when no primary source can be found, say so. Never invent one.

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
- Hugging Face ids for TiRex-2 and TimesFM 2.5.
- All runtime estimates. Time one window per model first.
- The GB study's weather-run numbers (its Zenodo record could not be opened).
- PJM load is widely shared public data: treat training-overlap risk as unknown to
  high for every foundation model.
