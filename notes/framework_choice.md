# Framework choice

Research pass on Nov 13, 2026. Research only: nothing was installed, no code or protocol
file was changed, nothing was run. It builds on `notes/model_families.md` and does not
repeat its library survey.

Evidence labels, as in `notes/model_families.md`: **(fetched)** read today at the URL
given; **(search summary)** seen only in a search result; **(memory)** not checked today;
**(estimate)** the agent's guess. **No runtime below was measured.**

## Which framework to explore first

### Answer

**Explore Nixtla first** (statsforecast + mlforecast + neuralforecast in one new
environment, here called `models_nx/`). Runner-up: **Darts**.

Why Nixtla:

- It is the only candidate whose own models cover all three families the question names:
  multi-seasonal statistical (MSTL, MFLES), boosted with future covariates (mlforecast),
  and neural with future covariates (NHITS, TFT, TiDE and others). In Darts the NHiTS
  model takes past covariates only (fetched).
- It has the most electricity evidence of the six: its own tutorials on PJM and ERCOT
  hourly load, and an independent 2026 load benchmark that builds on its NHITS and TFT
  code (table below).
- All three libraries share one long data format, `unique_id, ds, y`, which is this
  repo's convention, and each fits and predicts from the end of the frame it is handed.
  The harness can truncate at the cutoff and call it once.
- Darts, sktime and AutoGluon wrap these same Nixtla models, so learning them first
  transfers; the reverse is not true.

What the choice does not buy: the row most worth adding (a competition-grade LightGBM,
row 1 in `notes/model_families.md`) needs no framework at all. The framework is for the
statistical and neural rows.

### Comparison

All versions, dates, bounds and licences are from PyPI JSON metadata fetched today
(`https://pypi.org/pypi/<package>/json`).

| | Nixtla (3 libraries) | Darts | sktime | AutoGluon-TimeSeries | GluonTS | skforecast |
|---|---|---|---|---|---|---|
| Latest release | statsforecast 2.1.1 (2026-07-16), mlforecast 1.1.0 (2026-07-10), neuralforecast 3.3.1 (2026-11-10) | 0.48.1 (2026-10-16) | 1.3.0 (2026-11-08) | 1.6.3 (2026-09-18); nightly pre-releases to today | 0.17.0 (2026-07-31) | 0.27.0 (2026-11-11) |
| Release rhythm | neuralforecast about monthly; statsforecast had a gap from 2025-10 to 2026-07 | about monthly | 1.0 in June 2026, four releases since | active | one release between 2025-06 and 2026-06, then 0.17.0 | about monthly |
| Licence | Apache-2.0 | Apache-2.0 | BSD-3 | Apache-2.0 | Apache-2.0 | BSD-3 |
| pandas bound | statsforecast and mlforecast below 3.0; neuralforecast 2.3.3 or later. Together: pandas 2.3.x | 2.2 or later, no upper bound | below 3.2 | below 2.4 | below 3 | 2.2 to below 3.0 |
| Could share `core/` (pandas 3.1)? | no | by metadata yes; not tested | by metadata yes; not tested | no | no | no |
| Install weight | statsforecast: fugue, statsmodels. mlforecast: scikit-learn, optuna. neuralforecast: torch 2.9.1 or later, pytorch-lightning, ray[train,tune], optuna | core already pulls shap, pyod, xarray, numba, statsmodels, matplotlib; torch is an extra | very small core; every model is an optional dependency | heaviest: torch, lightning, transformers, gluonts, statsforecast, chronos, three boosting libraries, all tightly pinned | small core; torch is an extra | small: scikit-learn, numba, optuna |
| Multi-seasonal statistical | MSTL, MFLES, AutoMFLES, TBATS; MSTL and MFLES take regressors in their signatures | through statsforecast | through statsforecast and statsmodels (memory) | through statsforecast | through statsforecast extra | through an optional `stats` extra; not its focus |
| Boosted with future covariates | mlforecast: target lags built in; covariate lags through a separate helper, `transform_exog`; future values through `X_df` | strongest interface: `lags_future_covariates` takes past and future offsets of the covariate in one argument; one model per step by default | reduction wrappers around scikit-learn regressors (memory) | DirectTabular, RecursiveTabular, PerStepTabular | none of note | its core purpose: recursive and direct forecasters around any regressor |
| Neural with future covariates | NHITS, NBEATSx, TFT, TiDE, BiTCN and more | TFT, TiDE, DLinear, TSMixer yes; NHiTS and NBEATS no | wrappers (memory) | DeepAR, TFT, TiDE | DeepAR, TFT (memory) | a `deeplearning` extra; not investigated |
| One call per cutoff | fit on the frame up to the cutoff, predict with a future frame (`X_df` or `futr_df`). No hidden splitting unless a validation size is set | fit, then predict with the target series and a covariate series reaching past its end. Needs conversion to its own `TimeSeries` type | fit and predict with `y`, `X` and a horizon object (memory) | fit a predictor per cutoff; an ensemble is fitted by default and must be switched off for a single-model row | dataset and predictor objects; most ceremony (memory) | fit and predict with `exog` (argument names not read today) |
| Lookahead risk to watch | the future frame must hold only the regime's temperature; covariate lags are computed by us before the call | a covariate series longer than needed is accepted, so the harness must cut it at `c+168` itself | low | internal validation windows are cut from the training data, which is safe, but time limits make runs hard to reproduce | low | low |
| Electricity evidence | PJM hourly load tutorial; ERCOT hourly load tutorial; hourly price tutorial with load as a covariate; a 2026 load benchmark reuses its NHITS and TFT code | official example on Zurich hourly household load with temperature as a future covariate | one third-party tutorial on Spanish hourly data (search summary) | fev-bench, by the same group, includes GEFCom load tasks with a known covariate (`notes/model_families.md`); no load tutorial found | none found | one official tutorial on hourly demand with calendar and weather inputs (listed; the page itself could not be read) |
| Mac CPU runtime (estimate) | statistical and boosted: seconds per fit. NHITS: 1 to 3 min per fit | same models, same cost | as the wrapped model | set by the time limit; its presets also run Chronos-2 | as Nixtla's neural models | seconds per fit |

Sources (all fetched today):

- Covariates in neuralforecast, on French and Belgian hourly prices:
  https://nixtlaverse.nixtla.io/neuralforecast/docs/capabilities/exogenous_variables.html
- NHITS parameters and defaults: https://nixtlaverse.nixtla.io/neuralforecast/models.nhits.html
- mlforecast future features and `X_df`:
  https://nixtlaverse.nixtla.io/mlforecast/docs/how-to-guides/exogenous_features.html
- mlforecast covariate lags (`transform_exog`):
  https://nixtlaverse.nixtla.io/mlforecast/docs/how-to-guides/transforming_exog.html
- mlforecast constructor and predict arguments: https://nixtlaverse.nixtla.io/mlforecast/forecast.html
- statsforecast regressors and `X_df`:
  https://nixtlaverse.nixtla.io/statsforecast/docs/how-to-guides/exogenous.html
- statsforecast model signatures (MSTL, MFLES, AutoMFLES, SklearnModel):
  https://nixtlaverse.nixtla.io/statsforecast/src/core/models.html
- ERCOT hourly load tutorial (MSTL with cycles of 24 and 168 hours, 24 hours ahead, 30 daily
  windows, no weather):
  https://nixtlaverse.nixtla.io/statsforecast/docs/tutorials/electricitypeakforecasting.html
- PJM tutorial: see `notes/model_families.md`.
- Load benchmark repository; its README says it contains modified NHITS and TFT from
  neuralforecast. Datasets: UCI electricity, a feeder set and a German transmission
  operator, with reanalysis weather. Not GEFCom or PJM.
  https://github.com/KIT-IAI/load-forecasting-benchmark (paper: https://arxiv.org/abs/2607.15705)
- Darts covariate support by model: https://unit8co.github.io/darts/userguide/covariates.html
- Darts regression example on Zurich load:
  https://unit8co.github.io/darts/examples/20-SKLearnModel-examples.html
- AutoGluon known covariates, ensemble switch, presets:
  https://auto.gluon.ai/stable/tutorials/timeseries/forecasting-indepth.html
- skforecast example list: https://skforecast.org/latest/examples/examples_english.html

### Findings that matter for the choice

- **AutoGluon cannot share an environment with current Nixtla.** AutoGluon 1.6.3 pins
  mlforecast below 0.15 and coreforecast below 0.0.17; neuralforecast 3.3.1 and
  statsforecast 2.1.1 require coreforecast 0.0.17 or later (fetched, PyPI). Choosing
  AutoGluon means its older copies of these libraries.
- **skforecast's pandas bound is below 3.0** (fetched). This fills the "not read" cell
  in `notes/model_families.md`.
- **Only Darts and sktime could, by metadata, live in `core/`.** That is not a reason to
  put them there: Darts' core install is large.
- **MSTL does accept regressors in statsforecast 2.1.1**: `forecast` takes `X` and
  `X_future` (fetched, signatures). How they enter is not documented on the page; by the
  earlier index-page wording they go to the trend forecaster. This narrows the open
  item in `notes/model_families.md` but does not close it: read the installed source.
- **No published paper was found that runs any of these frameworks on PJM, GEFCom or
  ERCOT load** (one search). The evidence is tutorials plus one benchmark on other load
  data. GEFCom winners used their own regression and additive-model code
  (`notes/model_families.md`).
- **GluonTS is the weakest fit**: slow release rhythm until mid-2026, nothing on load
  found, and AutoGluon already wraps it.
- **sktime is an interface layer.** Useful for a team standardising on one API; here
  the harness already is that layer.

### Models to run first (Nixtla)

All three would be secondary rows under a protocol addendum, gated on the gate origins
first (`notes/model_families.md` section 6). Class names and arguments are from the
pages fetched today unless marked. Settings marked "proposed" are the agent's starting
values, not tuned and not from a source; fix them in the addendum before scoring.

**1. `statsforecast.models.MSTL`, univariate**

- `MSTL(season_length=[24, 168])`, leaving `trend_forecaster` at its default,
  `AutoETS(model='ZZN')`.
- Call: `StatsForecast(models=[...], freq='h', n_jobs=1).forecast(df=history, h=168)`.
  (`freq='h'` is from the neuralforecast page; the ERCOT tutorial writes `'H'`. Check
  which the installed version accepts.)
- Covariates: none. Label "univariate". It sets the bar for weather-free rows.
- History: 730 days, proposed, to match the Vanilla rows.
- Runtime: 10 to 30 s per fit, under 1 hour for all origins and both zones (estimate).

**2. `neuralforecast.models.NHITS` with future temperature**

- `NHITS(h=168, input_size=336, futr_exog_list=['temp', 'hour_sin', 'hour_cos', 'dow', 'holiday'], scaler_type='robust', max_steps=500, random_seed=1)`.
  `h` and `futr_exog_list` follow from the task; `scaler_type='robust'` follows the
  Nixtla covariate tutorial; `input_size` and `max_steps` are proposed (library default
  for `max_steps` is 1000). Pooling and downsampling left at defaults.
- Call: `NeuralForecast(models=[...], freq='h').fit(df=history)` with both zones in one
  frame, then `.predict(futr_df=future)` where `future` has `unique_id`, `ds` and the
  listed columns for exactly `c+1 .. c+168`.
- Keep the validation size at zero and early stopping off (default
  `early_stop_patience_steps=-1`), so nothing is held out and the stopping point does
  not depend on data near the cutoff.
- CPU: pass `accelerator='cpu'` through the trainer keyword arguments (memory; the page
  says only that extra arguments go to the Lightning trainer).
- Runtime: 1 to 3 min per fit (estimate). One fit covers both zones. 52 origins x 2
  regimes = 104 fits, 2 to 5 hours. If history before the cutoff is the same series in
  both regimes, one fit per origin could serve both regimes with two `predict` calls,
  halving this; check `harness/export_inputs.py` before relying on it.
- Risks: results move with seed and step count; retrained at every origin; low expected
  gain over a good boosted row. A second seed on the gate origins shows the noise.

**3. `mlforecast.MLForecast` around LightGBM, with temperature**

- `MLForecast(models=[lightgbm.LGBMRegressor(...)], freq='h', lags=[168], date_features=['hour', 'dayofweek', 'month', 'dayofyear'])`.
- Temperature: build lags and rolling means with
  `mlforecast.feature_engineering.transform_exog(temp_frame, lags=[...], lag_transforms={...})`
  on the regime's full series (history plus the 168 future hours), merge into the
  training frame, `fit(df, static_features=[])`, then `predict(h=168, X_df=transformed)`.
  `static_features=[]` matters: without it every extra column is treated as static and
  repeated forward (fetched).
- With `lags=[168]` as the only target lag and a horizon of 168, the recursive loop
  never feeds a prediction back in, so there is no compounding error (the agent's
  reasoning, not from a source). Adding shorter target lags changes that.
- Rows with missing covariate lags must be dropped by hand; the built-in `dropna`
  covers target lags only (fetched).
- Runtime: 5 to 20 s per fit (estimate).
- This overlaps row 1 of `notes/model_families.md`. Run it only if the aim is to learn
  the framework; if the aim is the best boosted row, build row 1 in `core/` and skip
  this one. It does not handle a growing load level (the DOM problem) by itself.

Optional fourth, cheap once model 1 runs: `statsforecast.models.MFLES(season_length=[24, 168])`
with temperature passed through `X_df`. It is the one multi-seasonal statistical model
documented as using regressors. Temperature enters linearly, so it needs heating and
cooling terms (for example two hinge columns) built by us. Not found in any load study.

Environment: one `models_nx/` with pandas 2.3.x should satisfy all three libraries by
their metadata (statsforecast and mlforecast below 3.0, neuralforecast 2.3.3 or later).
Not resolved or installed today. If ray or torch make it heavy, split statsforecast and
mlforecast into `models_stat/` as `notes/model_families.md` already suggests.

### Runner-up: Darts

Reason: it has the cleanest future-covariate interface of the six. For boosted models,
`lags_future_covariates` expresses "temperature from 48 hours back to the forecast hour"
in one argument, with no separate feature step, and `predict` takes the target series
and covariate series explicitly, which matches a per-cutoff harness. `TiDEModel` and
`TFTModel` accept future covariates, and it has an official worked example on hourly
load with temperature. It may also resolve with pandas 3.1.

Why second: its `NHiTSModel` has no future covariates; its multi-seasonal statistical
models are Nixtla's, wrapped; it needs conversion to and from its own series type at
every call; and the base install is large. If the first Nixtla rows show that the
neural model is worth a second look, Darts' `TiDEModel` is the natural next step.

### Not checked

- Every runtime. Time one gate window before planning a run.
- Whether the three Nixtla libraries resolve together, and against which torch.
- How MSTL uses `X` internally.
- skforecast's argument names and its demand tutorial (pages too long to read in full);
  the dataset of that tutorial.
- sktime and GluonTS interfaces (memory only).
- Whether Darts 0.48.1 actually runs on pandas 3.1.
- Load papers that use these frameworks on GEFCom, PJM or ERCOT: one search found none;
  that is not proof there are none.
