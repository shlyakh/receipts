# Model families to add as rows

Research pass on Nov 13, 2026. Research only: nothing was installed, no code or protocol
file was changed, nothing was run on the scored origins.

How to read the evidence labels:

- **(fetched)**: read on Nov 13, 2026 on the page at the URL given (docs, PyPI metadata,
  release page, arXiv abstract or HTML, Hugging Face API, model card).
- **(local)**: read in this repo or in an installed package under `models_ff/.venv` or
  `core/.venv`.
- **(search summary)**: seen only in a search-result summary; the page was not opened.
- **(memory)**: the research agent's recollection, not checked today.
- **(estimate)**: the agent's own arithmetic or guess. No runtime below was measured.

## 1. Summary and shortlist

- **The row most worth adding is a properly built boosted model, and it needs no new
  package.** The current LightGBM row has six features, one year of training and no
  tuning, and it loses to Vanilla with trend (1.228 on DOM, 1.046 on JC,
  `results/README.md`). Published competition entries look very different (section 3).
- **The strongest new challenger to Chronos-2 with temperature is a tabular foundation
  model.** On fev-bench's covariate tasks TabPFN-TS is the only other pretrained model
  whose score is reported with and without covariates, and it gains about as much from
  them as Chronos-2 does. `tabpfn` 9.2.0 and `tabpfn-time-series` 1.4.0 are already
  installed in `models_ff/` as dependencies of FoundationForecast (local).
- **Tabular models pretrained on synthetic tables only cannot have memorised PJM load.**
  That bears on the open research task in `DECISIONS.md`. It holds for TabPFN v2, Mitra
  and (by its abstract) TabICLv2; it is not established for the fine-tuned
  TabPFN-TS-3 checkpoint.
- **Nothing from Nixtla, GluonTS or AutoGluon can go into `core/`.** `core/` is on pandas
  3.1.1; statsforecast 2.1.1 and mlforecast 1.1.0 require pandas below 3.0, GluonTS 0.17.0
  below 3, AutoGluon 1.6.3 below 2.4 (fetched, PyPI). They need a new environment.
- **Trained models (boosting, MSTL, NHITS) have no weights date.** They are fitted on
  history up to each cutoff, so all 48 weeks are out-of-sample by construction.

Recommended rows, ranked by expected information per hour of work. All would be
secondary rows under a new protocol addendum (section 6). There are 2 zones x 2 regimes
x 52 origins = 208 calls per model with weather.

| # | Row | Library, exact model | Temperature | Environment | Mac CPU runtime (estimate) | Work | Main risks |
|---|---|---|---|---|---|---|---|
| 1 | Boosted, competition-grade | LightGBM 4.7.0 (already in `core/`), feature set of section 3 | yes, with lags and rolling means | `core/`, no install | 5 to 20 s per fit, 20 to 70 min in all | half a day | many choices to fix before scoring; where to tune (section 7) |
| 2 | TabPFN-TS, v2 weights | `tabpfn-time-series` 1.4.0, `TabPFNTSPipeline` in LOCAL mode with the v2 regressor checkpoint | yes, as a known covariate column plus its lags | `models_ff/` (already installed) | 10 to 60 s per forecast, 0.5 to 3.5 h in all; unmeasured | 2 to 3 h | licence acceptance and token needed; cloud mode is the default on a Mac; does not extrapolate trend (DOM) |
| 3 | MSTL, univariate | statsforecast 2.1.1 `MSTL(season_length=[24, 168])`, default trend forecaster | no (labelled univariate) | new `models_stat/` (pandas < 3) | 10 to 30 s per fit, under 1 h | 2 h | new environment; yearly cycle not modelled |
| 4 | TabICLv2 on row 1's feature table | `tabicl` 2.2.0 `TabICLRegressor` (regressor checkpoint of 2026-02-12) | yes, as columns | new `models_tab/`, or `models_ff/` if it resolves | similar to row 2; unmeasured | 2 to 3 h after row 1 | 34 of 48 weeks after the weights; CPU speed unknown |
| 5 | TabPFN-TS, newer weights | same adapter as row 2 with the TabPFN-TS-3 checkpoint (and optionally v3.5) | yes | `models_ff/` | as row 2 | 30 min after row 2 | 24 of 48 weeks after the weights (6 of 48 for v3.5); non-commercial licence; fine-tuning data unknown |
| 6 | NHITS with future temperature | neuralforecast 3.3.1 `NHITS` with `futr_exog_list` | yes | new `models_nf/` (torch, lightning, ray) | 1 to 3 min per training, 2 to 5 h in all | half a day | must be retrained at every origin; sensitive to settings; low expected gain |
| 7 | XGBoost and CatBoost on row 1's table | xgboost 3.4.1, catboost 1.2.10 | yes | `core/` (two `uv add`) or a new environment | as row 1 | 1 h after row 1 | little new information: a published entry calls the three comparable |
| 8 | AutoML reference | AutoGluon-TimeSeries 1.6.3, `high_quality`, known covariates | yes | new `models_ag/` (pandas < 2.4) | time limit x 104 fits, e.g. 9 h at 5 min | half a day | its presets include Chronos-2, so the row is not independent of the primary model |

Not recommended, with reasons, in section 2.

A cheaper variant of row 3 needs no new environment: `statsmodels.tsa.seasonal.MSTL`
imports in `core/` (local, statsmodels 0.15.0). It decomposes only; the trend forecast
would be our own code.

## 2. Statistical and deep-learning libraries

### Releases and compatibility (all fetched from PyPI JSON on Nov 13, 2026)

| Library | Latest | Uploaded | Python | pandas bound | Licence | Source |
|---|---|---|---|---|---|---|
| statsforecast | 2.1.1 | 2026-07-16 | >= 3.10 | < 3.0 | Apache-2.0 | https://pypi.org/pypi/statsforecast/2.1.1/json |
| mlforecast | 1.1.0 | 2026-07-10 | >= 3.10 | < 3.0 | Apache-2.0 | https://pypi.org/pypi/mlforecast/1.1.0/json |
| neuralforecast | 3.3.1 | 2026-11-10 | >= 3.11 | >= 2.3.3 | Apache-2.0 | https://pypi.org/pypi/neuralforecast/json |
| darts | 0.48.1 | 2026-10-16 | >= 3.11 | >= 2.2.0 | Apache-2.0 | https://pypi.org/pypi/darts/0.48.1/json |
| sktime | 1.3.0 | 2026-11-08 | >= 3.11 | < 3.2 | BSD-3 | https://pypi.org/pypi/sktime/1.3.0/json |
| gluonts | 0.17.0 | 2026-07-31 | >= 3.10 | < 3 | Apache-2.0 | https://pypi.org/pypi/gluonts/0.17.0/json |
| autogluon.timeseries | 1.6.3 | 2026-09-18 | 3.10 to 3.13 | < 2.4 | Apache-2.0 | https://pypi.org/pypi/autogluon.timeseries/1.6.3/json |
| prophet | 1.5.0 | 2026-10-05 | >= 3.10 | >= 1.3.5 | MIT | https://pypi.org/pypi/prophet/json |
| neuralprophet | 0.9.0 | 2024-06-21 | <= 3.12 | >= 2.0, numpy < 2 | MIT | https://pypi.org/pypi/neuralprophet/json |
| skforecast | 0.27.0 | 2026-11-11 | >= 3.10 | not read | BSD-3 | https://pypi.org/pypi/skforecast/json |
| pygam | 0.12.0 | 2025-12-18 | 3.10 to 3.14 | none; scipy < 1.17 | not read | https://pypi.org/pypi/pygam/json |

- neuralforecast 3.3.1 also requires torch >= 2.9.1, pytorch-lightning, ray and optuna
  (fetched). AutoGluon 1.6.3 pins torch below 2.11 on macOS and chronos-forecasting below
  2.4 (fetched).
- NeuralProphet has had no release since June 2024 and requires numpy below 2 (fetched).
- pygam cannot go into `core/`: `core/` has scipy 1.18.1 (local). `statsmodels.gam`
  imports there (local).

### What each offers for this problem

| Family | Models | Future temperature | Daily and weekly cycles at hourly resolution | Evidence |
|---|---|---|---|---|
| statsforecast, multi-seasonal | MSTL, MFLES, TBATS and their Auto forms | MFLES and AutoMFLES yes; MSTL only if its trend forecaster takes regressors; TBATS no | yes | https://nixtlaverse.nixtla.io/statsforecast/index.html (fetched) |
| statsforecast, single-seasonal | AutoARIMA, AutoETS, AutoTheta, AutoCES | AutoARIMA yes; the others no | one season length only (memory) | same page (fetched) |
| neuralforecast, with future covariates | NHITS, NBEATSx, TFT, TiDE, BiTCN, KAN, xLSTM, TSMixerx, XLinear, DeepAR, MLP, TCN, recurrent models | yes | learned from the input window | https://nixtlaverse.nixtla.io/neuralforecast/docs/capabilities/overview.html (fetched) |
| neuralforecast, without | PatchTST, TimeMixer, NBEATS, NLinear, SOFTS, RMoK, TSMixer, TimeLLM | no | learned | same page (fetched) |
| neuralforecast, multivariate | iTransformer (future covariates since 3.3.0), TimeXer (historic and static only) | partly | learned | same page; https://github.com/Nixtla/neuralforecast/releases (fetched) |
| mlforecast | any scikit-learn-style regressor on lag features; recursive by default, one model per step with `max_horizon`, a subset with `horizons` | yes, as columns | through lag and date features | https://nixtlaverse.nixtla.io/mlforecast/docs/how-to-guides/one_model_per_horizon.html (fetched) |
| Darts | wrappers: statsforecast models, LightGBM, XGBoost, CatBoost, TFT, TiDE, NHiTS, 30+ neuralforecast models (0.42), foundation models up to TimesFM 3, T0, TiRex-2 (0.48) | regression models, TFT, TiDE, DLinear, TSMixer yes; its own NHiTS and NBEATS past covariates only | as the wrapped model | https://unit8co.github.io/darts/ and its release notes (fetched) |
| AutoGluon-TimeSeries | statistical, deep (DeepAR, TFT, TiDE, PatchTST, DLinear), tabular (DirectTabular, RecursiveTabular, PerStepTabular), pretrained (Chronos-2, Toto-2), weighted ensemble | known covariates for the tabular models, DeepAR, TFT, TiDE, Chronos-2 | as the member models | https://auto.gluon.ai/stable/tutorials/timeseries/forecasting-model-zoo.html (fetched; page cut off before its end) |
| skforecast | recursive and direct forecasters around any regressor; adapters for foundation models including TabPFN, TabICL, Timestral, TiRex-2 | yes | lag features | https://skforecast.org/latest/releases/releases.html (fetched) |
| sktime | a wrapper layer over the above | as the wrapped model | as the wrapped model | version only (fetched); capabilities from memory |
| Prophet | additive trend, Fourier seasonality, regressors | yes | yes | version (fetched); capabilities from memory |

New model classes in neuralforecast during 2026 are XLinear (3.1.5) and SOFTSSharp
(3.1.9); the release page shows day and month only, the years are inferred (fetched).
statsforecast 2.1.0 added conformal intervals and an unobserved-components model and
deprecated Numba (fetched).

### Evidence on hourly load

- Nixtla's own tutorial on PJM hourly load, 24 hours ahead: MSTL with cycles of 24 and
  168 hours had about a third less error than seasonal naive; Prophet and NeuralProphet
  were worse than seasonal naive.
  https://nixtlaverse.nixtla.io/statsforecast/docs/tutorials/electricityloadforecasting.html
  (fetched). One test day, a vendor tutorial: weak evidence, but it is our operator.
- A July 2026 benchmark over three grid levels reports that Transformers trained on the
  data beat established methods by 7 to 11%, and that Chronos-2 zero-shot was
  competitive on two of three datasets but missed special events on the transmission
  data. https://arxiv.org/abs/2607.15705 (fetched, abstract only; the list of ten methods
  and the resolution were not read).
- NBEATSx was introduced on electricity prices with exogenous inputs (about 20% better
  than NBEATS). https://arxiv.org/abs/2104.05522 (fetched, abstract). NHITS claims better
  long-horizon accuracy than Transformers at a fraction of the compute.
  https://arxiv.org/abs/2201.12886 (fetched, abstract). Neither is a load result.
- N-BEATS on load exists for monthly national demand, not hourly.
  https://arxiv.org/abs/2009.11961 (fetched, abstract).
- On fev-bench the trained TFT, CatBoost and a statistical ensemble all rank below the
  pretrained models. https://arxiv.org/html/2509.26468v5 (fetched).

### Not recommended as rows

| Candidate | Reason |
|---|---|
| Prophet, NeuralProphet | worse than seasonal naive in the PJM tutorial above; NeuralProphet is unmaintained |
| AutoARIMA, AutoETS, AutoTheta alone | one seasonal period; useful only as MSTL's trend forecaster |
| TBATS | no regressors; slow on long hourly series (memory) |
| PatchTST, TimeMixer, SOFTS, RMoK, NLinear | no covariate input in neuralforecast; would duplicate the univariate rows |
| iTransformer, TimeXer, TSMixerx | multivariate designs; we have two series |
| TFT | covariates supported, but training 52 times on CPU is slow (estimate); second choice after NHITS |
| Darts, sktime, skforecast as such | wrappers; they add no model that the libraries above lack |
| GluonTS models | reached through AutoGluon if wanted |

## 3. Boosted models

### What strong boosted load forecasters look like

| Source | What it shows | Status |
|---|---|---|
| BigDEAL Challenge 2022 entry (3rd, 3rd and 8th on the three qualifying measures; 6th in the final). https://ar5iv.labs.arxiv.org/html/2305.05575 | LightGBM on temperature and calendar features only, no lagged load. Hourly temperature lags of 1 to 48 hours over four station summaries; rolling mean, max, min, median and spread over 3 hours, a day, a week and a month; daily and month-hour aggregates; calendar with holiday name and days to and from a holiday. Target in logs with a linear trend removed and added back (error 6.18 to 4.81 from detrending alone). Features chosen by permutation importance on correlated clusters (4.81 to 3.09). Tuned with Optuna on time-ordered folds. DART booster and a probabilistic variant in the final. Vanilla ranked 25th to 30th in the same qualifying match; the recency benchmark 10th in the final. | fetched |
| Same paper | XGBoost, LightGBM and CatBoost are described as comparable in accuracy; LightGBM faster | fetched |
| GEFCom2012 load, ranks. https://blog.drhongtao.com/2013/08/gefcom2012-winners.html | 1st a refined parametric model (method from a search summary); 2nd Lloyd; 3rd EDF's semi-parametric additive models; 4th Ben Taieb and Hyndman | ranks fetched |
| Lloyd. https://econpapers.repec.org/RePEc:eee:intfor:v:30:y:2014:i:2:p:369-374 | gradient boosting machines and Gaussian processes with little domain tuning | fetched (abstract) |
| Ben Taieb and Hyndman. https://econpapers.repec.org/RePEc:eee:intfor:v:30:y:2014:i:2:p:382-394 | one model per hour of day; component-wise boosting with penalised splines; current and past temperature and past demand; week-ahead task | fetched (abstract) |
| GEFCom2014 load winner. https://econpapers.repec.org/RePEc:eee:intfor:v:32:y:2016:i:3:p:1038-1050 | quantile additive models; the team tried random forests and boosting and did not report them among its best | fetched (abstract) |
| GEFCom2017. https://blog.drhongtao.com/2017/08/winning-teams-for-global-energy-forecasting-competition-2017.html | winner list fetched. One qualifying entry averaged boosting, a quantile forest and a neural network (search summary). The overview paper's method summary was not read. | partly |
| IEEE DataPort post-COVID day-ahead competition | winners used online combination of many models and state-space adaptation of additive models | search summary |
| Kaggle Enefit 2024 (hourly, weather forecasts) | boosted trees with hundreds of lag and weather features, blended with neural networks | search summary only |

Reading of this evidence:

- In load competitions boosting places near the top and inside ensembles, but the
  winners of 2012 and 2014 were parametric and additive models. A boosted row is the
  "tuned machine learning" rung, not a ceiling. The additive model (rung 6 in
  `notes/classical_baselines.md`) remains worth running.
- **Direct or recursive.** mlforecast's default is recursive: predict one step, feed it
  back. Over 168 steps that compounds error (memory). The competition entries above
  avoid recursion altogether: features are temperature and calendar, or load lags at
  least as old as the horizon. With future temperature known, that is the natural
  design here. One model per step (168 models) is supported by mlforecast but costly
  (fetched). A middle route is one model with horizon day as a feature, or seven
  models, one per horizon day (the agent's suggestion).
- **Library differences** matter less than features (fetched claim above). Latest
  versions: LightGBM 4.7.0 (https://github.com/microsoft/LightGBM/releases, year
  inferred), xgboost 3.4.1 uploaded 2026-08-15 (needs Python >= 3.12, only numpy and
  scipy), catboost 1.2.10 uploaded 2026-02-18 with a macOS universal wheel for Python
  3.12 (fetched, PyPI). Ordered boosting and categorical handling in CatBoost, and
  leaf-wise growth in LightGBM, are from memory.

### Our LightGBM row (`harness/baselines.py`)

It is a weak representative, by design: decision in `DECISIONS.md` says it uses exactly
the lag regression's inputs. The evidence that it is weak is our own: a linear
regression with no load input (Vanilla with trend) beats it in both zones.

| Aspect | Current row | Competition practice | Consequence here |
|---|---|---|---|
| Features | six: `y_lag168`, hour, day of week, holiday, year-end, temperature | tens to hundreds | no way to express season or thermal inertia |
| Season | none (no month or day of year) | month, day of year, week | winter and summer share one temperature response |
| Temperature history | current hour only | lags of 1 to 48 h, rolling means from 3 h to a month, daily max and min | misses the recency effect that the literature values at 12 to 21% for regression |
| Training window | 365 days (`TRAIN_DAYS`) | several years; 730 days for Vanilla | one year cannot separate season from temperature; data go back to 2019 (local) |
| Level and trend | none; a tree cannot predict above the loads it was trained on | detrend, log target, or model a ratio | DOM is growing; this is the likely cause of the DOM result |
| Load inputs | value 168 h earlier only | recent level at the cutoff, profile of the last day, by horizon | ignores load up to the cutoff, which every foundation model sees |
| Horizon | one model for all 168 hours | per-horizon or horizon as a feature | day 1 and day 7 treated alike |
| Tuning | fixed: 300 trees, rate 0.05, 31 leaves, no validation | searched on time-ordered folds, early stopping | unknown under- or over-fit |
| Loss | squared error | absolute or quantile when scored on absolute error | minor |
| Ensembling | one model, one seed | seeds, boosters, other families | minor |

A competition-grade row would need, all fixed in the addendum before scoring:

1. Training window of at least 730 days, to match Vanilla; state it.
2. Calendar: hour, day of week, month, day of year, holiday, days to and from the
   nearest holiday, year-end.
3. Temperature: current, a chosen set of hourly lags (the cited entry found 1 to 6, 11
   to 12 and 25 to 26 hours most useful), rolling means over 3 h, 24 h, 168 h and 30
   days, daily maximum and minimum. All computed from the regime's series, so the
   forecast regime uses forecast values inside the horizon and reanalysis before it,
   which the harness already supplies in one series.
4. Level: either a target relative to the mean load of the 168 hours before the cutoff,
   or a linear trend removed and added back. Without this the row will repeat the
   Vanilla-without-trend failure on DOM.
5. Load at the cutoff: mean of the last 24 and 168 hours, the value at the same hour on
   the last observed day, and `y_lag168`; horizon day as a feature. This uses the same
   information set as the foundation models.
6. Hyperparameters chosen once on origins that are never scored, then frozen and
   written into the addendum.
7. The same drop rule as today when `y_lag168` is missing, or a stated alternative.

Two rows would isolate what matters: "exogenous only" (items 1 to 4, comparable with
Vanilla and the cited entry) and "with load at the cutoff" (adding item 5, comparable
with Chronos-2).

## 4. Tabular models applied to forecasting

### How they are applied

Each series becomes a table: one row per hour, columns for a running index, calendar
cycles as sine and cosine pairs, a few seasonal cycles found by Fourier analysis, and
any covariate known into the future. The history rows carry the target; the model
predicts the target for the 168 future rows in one forward pass, with no training and
no lagged target (https://arxiv.org/html/2501.02945v4, fetched). The installed
`tabpfn-time-series` 1.4.0 adds, by default, lag-1, lag-24 and a 24-hour trailing mean
of every known numeric covariate (local: `features/covariate_features.py`,
`pipeline.py`).

### Models

| Model | Package, latest | Weights: where, date, licence | Pretraining | Forecasting support | Scored weeks after weights |
|---|---|---|---|---|---|
| TabPFN v2 | tabpfn 10.0.0, uploaded 2026-11-13; 9.2.0 installed | `Prior-Labs/TabPFN-v2-reg`, repository created 2025-01-04, not gated, Prior Labs licence (Apache 2.0 plus attribution) | synthetic (memory) | TabPFN-TS paper model; known covariates | 48 of 48 if the file dates from January 2025 (file date not read) |
| TabPFN-TS-3 | same | `Prior-Labs/tabpfn_3`, file `tabpfn-v3-regressor-v3_20260506_timeseries.ckpt`, repository last modified 2026-07-04, non-commercial licence | fine-tuned for time series; on what data is unverified | default of tabpfn-time-series 1.1.0; local only | 24 of 48 by file name; 16 by repository date |
| TabPFN-3.5 | same | `Prior-Labs/tabpfn_3_5`, files dated 2026-09-09, non-commercial | not read | default of tabpfn-time-series since 1.3.0 | 6 of 48 |
| TabICLv2 | tabicl 2.2.0, uploaded 2026-09-02 | `jingang/TabICL`, `tabicl-regressor-v2-20260212.ckpt`, not gated, BSD-3 | synthetic generator (abstract) | `TabICLForecaster` (extra `forecast`), described as univariate and derived from TabPFN-TS; default context 4,096 | 34 of 48 |
| TabDPT | tabdpt 1.3.2, uploaded 2026-11-02 | `Layer6/TabDPT`, three versions, last modified 2026-09-08, Apache-2.0 | real tables (search summary) | none in the package; tested as a backbone in the TabPFN-TS paper and found weaker | 6 of 48 for v1.3; earlier versions not dated |
| Mitra | through autogluon.tabular 1.4 and later | `autogluon/mitra-regressor`, last modified 2025-11-19, Apache-2.0, 72M parameters | synthetic only (model card) | none documented | 46 of 48 |
| TabM, RealMLP | through AutoGluon 1.4 and later | none: trained from scratch | n/a | none | n/a |
| CARTE | not checked | not checked | built for tables with text entities (memory) | none known | not checked |
| TS-ICL (EDF) | paper of June 2026 | release of code or weights not confirmed | synthetic with a causal prior | native, with covariates | not checked |

Sources (all fetched): https://pypi.org/pypi/tabpfn/json ,
https://docs.priorlabs.ai/models ,
https://huggingface.co/api/models/Prior-Labs/TabPFN-v2-reg ,
https://huggingface.co/api/models/Prior-Labs/tabpfn_3 ,
https://huggingface.co/api/models/Prior-Labs/tabpfn_3_5 ,
https://github.com/PriorLabs/tabpfn-time-series , https://pypi.org/pypi/tabicl/json ,
https://huggingface.co/api/models/jingang/TabICL , https://arxiv.org/abs/2602.11139 ,
https://pypi.org/pypi/tabdpt/json , https://huggingface.co/api/models/Layer6/TabDPT ,
https://huggingface.co/autogluon/mitra-regressor ,
https://github.com/autogluon/autogluon/releases , https://arxiv.org/abs/2606.05878 .
The "weeks after weights" column is counted from `protocol.yaml` over the 48 scored
windows; dates are repository or file-name dates, not per-file commit dates, which
`models/download.py` would have to record.

AutoGluon 1.6.0 also added a tabular model called Nori and TabDPT-Turbo (fetched, release
notes); neither was investigated.

### Published forecasting results

- fev-bench, 100 tasks: TabPFN-TS is sixth by win rate behind Chronos-2, TiRex, TimesFM
  2.5, FlowState and Toto, with a skill score close to the second and third. On the 42
  tasks with dynamic covariates its skill is about 42.5% with covariates against 34.1%
  without; Chronos-2's is about 47.0% against 40.9%. The benchmark contains hourly load
  tasks with one known covariate (GFC12, GFC14, GFC17) and ENTSO-E load.
  https://arxiv.org/html/2509.26468v5 (fetched; which TabPFN-TS version is not stated in
  the part read).
- TabPFN-TS paper (v2 backbone): best of the models it compared on 28 covariate tasks;
  close behind the leaders on GIFT-Eval; about 30 times slower than Chronos-Bolt on
  equal hardware; **does not extrapolate trends**; context capped at 4,096 rows with no
  gain beyond. https://arxiv.org/html/2501.02945v4 (fetched). It did not compare with
  Chronos-2.
- Day-ahead load for a German transmission operator: Chronos-2 and TabPFN-TS zero-shot
  were both competitive with a Transformer trained on several years.
  https://arxiv.org/abs/2604.28149 (fetched, abstract).
- Electricity prices in three markets: only the TabPFN models beat the market-specific
  benchmarks consistently. https://arxiv.org/abs/2609.00089 (fetched, abstract).
- District heating and low-voltage feeders: Chronos-2 ahead of TabPFN-TS on accuracy
  (search summary).
- The live GIFT-Eval, fev-bench and TabArena leaderboards could not be read (the pages
  render in the browser only). The tabpfn-time-series README's "ranked first on
  GIFT-Eval" refers to January 2025.
- No published forecasting result was found for TabICLv2, Mitra, TabM, RealMLP or CARTE.

### Feasibility on this laptop (Apple M3, 8 cores, 16 GB; local)

- Context: 4,096 hourly rows is 24 weeks. Two years (17,520 rows) exceeds TabPFN v2's
  stated limit of 10,000 rows and fits within those of v3 and v3.5 (1,000,000) and the
  range TabICLv2 was trained for (up to 48,000). The paper found no gain beyond 4,096,
  and v2's cost grows with the square of the row count.
- `tabpfn` restricts CPU runs to 1,000 rows for v2-era models and 5,000 for v3 and
  later unless an override variable is set, and calls CPU inference slow (fetched, PyPI
  description). On a Mac, `tabpfn-time-series` uses its CPU worker and lets `tabpfn`
  route tensors to MPS (local, `predictor.py`). CLAUDE.md allows MPS only after one
  window matches CPU output.
- Runtime per forecast is unmeasured. Measure one gate window before planning a run.
- **The FoundationForecast wrapper is the wrong route.** Without CUDA it selects cloud
  mode, which sends the series to Prior Labs' service, needs an API key, and cannot be
  pinned to a revision (local, `foundationforecast/models/tabpfn.py`). It also does not
  pass covariates to TabPFN (local: the library lists native covariate support for
  seven other models, `notes/foundationforecast.md`). Use `TabPFNTSPipeline` directly in
  LOCAL mode with `future_df`.
- Local mode needs the licence accepted at Prior Labs' site and a token before the
  first download (fetched, README; local, wrapper notes). Whether that also applies to
  the v2 checkpoint, whose repository is not gated, is unverified. The token is a
  secret: `.env` and `.env.example`.
- The licences of TabPFN 2.5 and later forbid production use; this benchmark is
  research. The leaderboard should carry the licence.

### The design this suggests

One adapter that builds a feature table and takes the regressor as a parameter:
LightGBM (row 1), TabICLv2 (row 4), optionally TabPFN, TabDPT or Mitra. The table is the
same, so the comparison isolates the learner: a boosted model trained on two years
against a pretrained model given the same rows as context. TabPFN-TS with its own
featurisation (row 2) is kept separate because that is the published method.

## 5. How the shortlist answers the project's questions

| Question | Row that answers it |
|---|---|
| Does Chronos-2 beat tuned machine learning, not only regressions? | 1 |
| Is Chronos-2's use of temperature special, or does any covariate-aware zero-shot model do it? | 2, 5 |
| Does a model that cannot have seen PJM data reach the same level? | 2 (synthetic pretraining, weights of January 2025) |
| What is a fair bar for the weather-free rows? | 3 |
| Features or learner? | 1 against 4 on one table |
| Does a trained deep network add anything? | 6 |

## 6. Registration under the frozen protocol

Follow the pattern of `protocol-v1.1.yaml` and `DEVIATIONS.md`.

1. Write `protocol-v1.2.yaml` with `based_on: protocol-v1` and the same `unchanged`
   statement: zones, horizon, origins, regimes, drop rule, bootstrap, baseline, primary
   comparison, bar and sentences are untouched.
2. One `added_model` block per row: name, label, why, exact definition (features,
   window, hyperparameters, library version, checkpoint file and revision, context
   length, mode), and source URL. Anything left open in the definition becomes a choice
   made after seeing results.
3. Gate: run on the six gate origins only; the lookahead test in `tests/test_gates.py`
   passes with the model included (it corrupts load after the cutoff and disallowed
   weather, which is the right test for lag and rolling features); forecasts complete
   wherever other models complete.
4. Add a dated line to `DEVIATIONS.md`, commit, tag `protocol-v1.2`, then score the 52
   origins once per row.
5. Every row is secondary. Pre-write the secondary comparisons: each new row against
   the frozen baseline and against Vanilla with trend; Chronos-2 with temperature
   against each new row with the same 10% bar, reported as secondary.
6. For pretrained rows record revision, weights date and `n_windows_after_weights`
   (rule 13); for trained rows record "not applicable". A row with few weeks after the
   weights is labelled as Timestral's is.
7. Rows from other environments exchange parquet through `harness/export_inputs.py`,
   as the foundation-model rows do. `harness/run.py` reads `MODEL_PROTOCOL` for the
   version label; rows scored elsewhere need the same label.
8. Several small addenda (v1.2 for the boosted row, v1.3 for tabular models) keep each
   gate short, at the price of more tags. One addendum is simpler if the rows are ready
   together.

## 7. Open questions and unverified items

Decisions for Yuri:

- **Where may hyperparameters be tuned?** The gate origins are six autumn weeks. The 52
  ordering-gate origins (2024-09-30 to 2025-09-22) are never scored but were declared
  "used for one check only". Using them for tuning needs a line in the addendum.
  Alternative: tune on origins before 2024-09-30, which no protocol version mentions.
- **Does the boosted row keep the decision that LightGBM uses the regression's inputs?**
  The existing row stays as it is; the new one is a second row with its own name.
- **TabPFN licence and token**: someone has to accept the terms. Is a non-commercial
  licence acceptable for a hackathon entry and for the later product?
- **New environments**: up to three (`models_stat/`, `models_tab/`, `models_nf/`).
  CLAUDE.md lists three today.
- **Is retraining a neural network 52 times in keeping with "call each model once per
  cutoff"?** It is, but it is the expensive reading; training once on data before the
  first scored origin would be a different, weaker row.

Unverified:

- All runtimes. Nothing was timed.
- Per-file commit dates of every tabular checkpoint; the dates above are repository
  creation or modification dates and file-name dates.
- What data TabPFN-TS-3 was fine-tuned on (the report PDF was too large to fetch:
  https://priorlabs.ai/reports/tabpfn-3). If it includes public load series, row 5 has
  the same leakage question as the time-series models.
- Whether TabPFN v2's pretraining is purely synthetic (memory), and TabDPT's training
  tables (search summary).
- Whether `TabICLForecaster` accepts covariates (its README describes it as
  univariate). Row 4 avoids the question by using `TabICLRegressor` on our own table.
- Whether `tabicl` or `neuralforecast` resolve alongside FoundationForecast's pins in
  `models_ff/`.
- Whether MSTL's default trend forecaster in statsforecast 2.1.1 can take temperature;
  the index page says "if trend forecaster supports".
- Methods of the GEFCom2012 winner and of the GEFCom2017 and Enefit top entries (search
  summaries; the overview papers are behind a publisher page that refused the fetch).
- Years of GitHub release dates for neuralforecast, statsforecast, AutoGluon and
  LightGBM (pages show day and month); the latest versions' years are confirmed on PyPI
  where a PyPI date is given above.
- Current leaderboard positions on GIFT-Eval, fev-bench and TabArena.
- AutoGluon's preset membership beyond `medium_quality`, and whether its tabular
  forecasters can use TabPFN or Mitra as the regressor.
- LightGBM's linear-leaf option as another answer to the trend problem (memory).
- CARTE, Nori, TabDPT-Turbo and TS-ICL were not investigated beyond the lines above.
