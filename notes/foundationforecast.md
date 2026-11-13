# Notes: model libraries, verified against installed packages

Checked on Nov 13, 2026 in the `models/` environment.

## chronos-forecasting 2.3.2 (the version the GB study used)

- `Chronos2Pipeline.from_pretrained(repo_id, revision=..., cache_dir=..., device_map="cpu")`.
- `predict_df(df, future_df=None, id_column="item_id", timestamp_column="timestamp",
  target="target", prediction_length=None, quantile_levels=[0.1..0.9], batch_size=256,
  context_length=None, cross_learning=False, validate_inputs=True, freq=None)`.
  The sketch in `REFERENCE.md` was right about the argument names.
- Past covariates: extra columns in `df`. Known-future covariates: the same column
  names in `future_df`. Timestamps must be timezone-naive.
- Output columns: id, timestamp, `target_name`, `predictions` (equal to the 0.5
  quantile) and one column per quantile, named "0.1", "0.5", "0.9".
- Speed on this laptop, CPU, 4 threads, two series per call, 168-hour horizon:
  0.2 s at 2,048 hours of context, 0.5 s at 4,096 (first call 1.4 s, includes warm-up).
- Settings used (`models/chronos2.py`): context 2,048 hours, no cross-learning, median.

## foundationforecast

- `uv add foundationforecast` installs version 0.1.0 from PyPI, which is an EMPTY
  PLACEHOLDER: its only content is a top-level `main.py` that prints a greeting. There
  is no `foundationforecast` module in it. It was removed.
- The real library is at `github.com/TimeCopilot/foundationforecast` (Apache-2.0,
  "Pre-Alpha" in its classifiers). Its README says to install from PyPI, which does not
  work as of Nov 13, 2026.
- Installed from git on Nov 13, 2026 with Yuri's approval, pinned to commit `cd67b608`
  (Nov 11, 2026; reports version 0.1.20), in its own environment `models_ff/`. It cannot
  share `models/`: it requires `huggingface-hub<2.0` and brings a fork of the Chronos
  package (`timecopilot-chronos-forecasting` 0.2.2) that installs the same `chronos`
  module. Its stack here is torch 2.11.0 and pandas 2.3.3.
- Verified API: `FoundationForecast(models=[...]).forecast(df, h, freq, level, quantiles,
  X_df=..., futr_exog_list=...)`. `X_df` works as sketched in `REFERENCE.md`: long format
  with `unique_id`, `ds` and the covariate columns for the next `h` steps. Timestamps
  must be timezone-naive.
- Model classes: Chronos, TimesFM, Timestral, T0, TiRex, Kumo, Moirai, Toto, Sundial,
  TabPFN, FlowState, PatchTSTFM, TimeH2O, Tabby, Tafsut, TimeGPT.
- No wrapper takes a Hugging Face `revision`. `repo_id` may be a local directory, so the
  way to honour the pinning rule is to pass the path of the pinned snapshot in
  `models_cache/`.
- `Chronos` has no context-length argument; it uses whatever history it is given, so
  the caller truncates. Only checkpoints with "chronos-2" in `repo_id` accept `X_df`;
  for other models `X_df` raises unless `exog_strategy=False`.

### Cross-check against the direct adapter (gate origins only)

`models_ff/crosscheck_chronos2.py gate`, same inputs and settings as
`models/chronos2.py`, six gate origins, both zones, both regimes, with and without
temperature (8,064 hourly forecasts). Largest difference 0.003 MW on DOM and 0.0007 MW
on JC, a relative difference below 5e-7: single-precision noise across two library
stacks. The library reproduces the direct adapter. Side-by-side values are in
`results/gate/crosscheck/chronos2_ff.parquet`. It is not a leaderboard row.

### Other models through the library (`models_ff/run_ff.py`)

- TimesFM 2.5: the wrapper is univariate (no `X_df`). Runs at 2,048 hours of context,
  about 0.3 s per series on CPU. Missing hours in the context (the EIA clock-change
  gaps) produce finite forecasts. Scored once on Nov 13, 2026.
- Timestral-209M: accepts `X_df`; library defaults are symmetric averaging and clipping
  at zero. About 0.5 s per series. Run on the gate origins only. Its repository has a
  single squashed weights commit dated 2026-10-15, so no earlier revision can be pinned.

## Hugging Face ids

All eight ids in `REFERENCE.md` resolve and none is gated. Pins and weights dates for
downloaded models are in `models/pins.json`.
