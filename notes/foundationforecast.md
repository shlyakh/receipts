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
  "Pre-Alpha" in its classifiers, last pushed 2026-11-11). Its README says to install
  from PyPI, which does not work as of today. Installing it means installing from git.
  Not done: ask Yuri first.

## Hugging Face ids

All eight ids in `REFERENCE.md` resolve and none is gated. Pins and weights dates for
downloaded models are in `models/pins.json`.
