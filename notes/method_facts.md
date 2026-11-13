# Facts behind the Methods tab descriptions

Checked on Nov 13, 2026 against primary sources fetched that day. Each line is a short
paraphrase, not a quotation. Used in `dashboard/index.html` (Methods tab).

## Verified

| Fact | Source | Paraphrase |
|---|---|---|
| IFS is physics-based | https://www.ecmwf.int/en/forecasts/documentation-and-support/changes-ecmwf-model | ECMWF calls the IFS physics-based: data assimilation plus a global numerical model of the Earth system. |
| AIFS is machine-learned; trained on ERA5 and operational analyses | https://arxiv.org/abs/2406.01465 | ECMWF's AIFS is a data-driven forecast model (graph neural network with a transformer processor), trained on ERA5 reanalysis and on ECMWF operational analyses. |
| AIFS Single operational date and grid | https://www.ecmwf.int/en/forecasts/dataset/aifs-machine-learning-data | AIFS Single operational since 25 Feb 2025 (v2 from 12 May 2026); about 0.25 degree. |
| ERA5 producer, grid, delay | https://cds.climate.copernicus.eu/datasets/reanalysis-era5-single-levels?tab=overview | ERA5 is ECMWF's fifth-generation reanalysis, 0.25 degree for the atmosphere, updated daily about 5 days behind real time; preliminary values can be revised 2 to 3 months later. |
| HRRR | https://rapidrefresh.noaa.gov/hrrr/ | NOAA's hourly-updated 3 km model; HRRRv4 runs to 48 hours every 6 hours. |
| GFS | https://www.emc.ncep.noaa.gov/emc/pages/numerical_forecast_systems/gfs.php | NCEP's global model at about 13 km. |
| Chronos-2 pretraining data | https://huggingface.co/amazon/chronos-2 | Card: subsets of the Chronos Datasets collection and of GIFT-Eval Pretrain, plus synthetic univariate and multivariate series. No load, energy or PJM data named as training data. Max context 8,192. |
| Chronos Datasets contents | https://huggingface.co/datasets/autogluon/chronos_datasets | The collection includes electricity series (e.g. `ercot`, `electricity_15min`, `monash_electricity_hourly`); no PJM set. Which of them Chronos-2 used is not stated. |
| GIFT-Eval Pretrain contents | https://huggingface.co/datasets/Salesforce/GiftEvalPretrain | Card names seven domains but does not list them; energy or load not named. |
| TimesFM 2.5 pretraining data | https://huggingface.co/google/timesfm-2.5-200m-pytorch | Card: GIFT-Eval Pretrain, Wikimedia pageviews (to Nov 2023), Google Trends queries (to end 2022), synthetic and augmented data. Electricity: not stated. Covariates: not stated. |
| Timestral card | https://huggingface.co/mistralai/Timestral-209M | Card: accepts past-only and known-future covariates and up to 32,768 past steps. Pretraining data: not stated. Electricity or PJM: not stated. Release date: not stated. |
| LightGBM is gradient boosting with trees | https://lightgbm.readthedocs.io/en/latest/index.html | LightGBM describes itself as a gradient boosting framework built on tree learners. |
| Gradient boosting adds trees in sequence | https://scikit-learn.org/stable/modules/ensemble.html | In gradient-boosted trees each new tree is fitted to the negative gradients (errors) of the ensemble so far and added to it. |
| Context of TimesFM temperature row and Timestral | `models_ff/timesfm25_xreg.py`, `models_ff/run_ff.py` (our code) | Both use the last 2,048 hours. |

## Not verified (left off the page)

- ERA5 produced "for the Copernicus Climate Change Service": the CDS dataset page and the
  C3S reanalysis page name ECMWF as producer but do not state C3S's role in so many words;
  the ECMWF ERA5 dataset page returned HTTP 401.
- Whether Chronos-2's subset of Chronos Datasets includes the electricity series.
- Timestral pretraining data: no primary source states it (the card says a technical
  report is coming).
- Vanilla benchmark trend term: no primary source could be opened. Tao Hong's blog posts
  on the GEFCom2012 data (https://blog.drhongtao.com/2016/07/gefcom2012-load-forecasting-data.html)
  and on recency effects (https://blog.drhongtao.com/2015/02/load-forecasting-recency-effect-big-data.html)
  do not give the formula; the dissertation record at repository.lib.ncsu.edu blocked the
  fetch; the GEFCom2012 paper (doi 10.1016/j.ijforecast.2013.07.001) is behind a paywall.
  Secondary papers describe a trend term, which is what BASELINES.md already records. The
  page wording ("found only in search summaries") is unchanged.
