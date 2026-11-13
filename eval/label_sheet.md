# Blind labelling sheet

For each item pick one label and write it next to `label_yuri:` in `eval/items.yaml`
(or just send me the 11 labels). Do not open `eval/items.yaml` first: it holds the proposed labels.

Judge against: PJM zonal hourly load, a week ahead, weather as an input (`spec.yaml`).

- **ACCEPT_RUN**: relevant, has a primary source, and we can run it on our benchmark now
- **ACCEPT_STAGE3**: relevant and sourced, but running it needs real work
- **PARTIAL**: relevant, but evidence is thin or the primary source is missing
- **REJECT**: off target, or no usable support

## item-01: NVIDIA Kumo Forecast available in FoundationForecast

- Type: library_feature
- Claim: Point-forecast model usable through one API, with conformal prediction intervals added on top.
- Primary sources: https://huggingface.co/nvidia/Kumo-Forecast, https://github.com/NVIDIA/Kumo-TS, https://github.com/TimeCopilot/foundationforecast, https://docs.timecopilot.dev/foundationforecast/examples/kumo-family/
- Your label: 

## item-02: Weather and zero-shot models on GB electricity demand (pre-registered backtest)

- Type: practitioner_backtest
- Claim: Given the same weather, the best zero-shot model roughly ties a plain weather regression; weather improves every forecaster.
- Primary sources: https://zenodo.org/records/24161799, https://github.com/AndyMoran/gb-foundation-model-tests
- Your label: 

## item-03: open-predico, open-source repo for energy forecasting competitions

- Type: practitioner_backtest
- Claim: t0-gamma was the best commercially usable model in the author's wind-generation backtest.
- Primary sources: https://github.com/arnaud-vs/open-predico, https://huggingface.co/spaces/open-predico/dashboard
- Your label: 

## item-04: Conformal prediction across all FoundationForecast models

- Type: library_feature
- Claim: Calibrated intervals for any model from its historical errors, without retraining.
- Primary sources: https://docs.timecopilot.dev/foundationforecast/examples/conformal-prediction/, https://github.com/TimeCopilot/foundationforecast
- Your label: 

## item-05: WeatherNext 3 vs physics-based weather forecasts (ML6 study)

- Type: vendor_claim
- Claim: Lower error than a physics model on wind speed, solar irradiance and temperature; lower imbalance costs for wind and solar farms.
- Primary sources: https://www.ml6.eu/en/blog/googles-weathernext-3-better-weather-forecast-lower-imbalance-costs
- Your label: 

## item-06: System imbalance forecast beating the Belgian grid operator (ML6)

- Type: vendor_claim
- Claim: Lower error than the operator's own imbalance forecast using public data only.
- Primary sources: none found (no non-LinkedIn URL)
- Your label: 

## item-07: Chronos-2 vs Timestral-209M on a Swiss town's load (alitiq)

- Type: practitioner_backtest
- Claim: Timestral slightly ahead of Chronos-2 day-ahead on a 15-minute grid with weather and calendar covariates; Chronos-2 slightly ahead on the hourly grid.
- Primary sources: none found (no non-LinkedIn URL)
- Your label: 

## item-08: LoRA-reprogrammed small LLM for household demand

- Type: practitioner_backtest
- Claim: The reprogrammed LLM loses to zero-shot Chronos and ties simple neural baselines.
- Primary sources: none found (no non-LinkedIn URL)
- Your label: 

## item-09: The Forecasting Company t0 model family

- Type: model_release
- Claim: Open-weight probabilistic model with known-future covariates, near the top of a public benchmark, usable commercially.
- Primary sources: https://huggingface.co/theforecastingcompany/t0-gamma, https://huggingface.co/theforecastingcompany/t0-beta, https://arxiv.org/abs/2609.24559
- Your label: 

## item-10: TimesFM-3 release

- Type: model_release
- Claim: Native multivariate forecasting with past-only and known-future covariates, full horizon in one pass.
- Primary sources: https://github.com/google-research/timesfm, https://huggingface.co/google/timesfm-3.0-pytorch, https://research.google/blog/timesfm-3-a-zero-shot-foundation-model-for-multivariate-forecasting/
- Your label: 

## item-11: Video review of Timestral and t0-gamma topping a public benchmark

- Type: paper
- Claim: Both models lead a general benchmark; synthetic training data is increasingly important.
- Primary sources: https://mistral.ai/news/timestral/, https://github.com/mistralai/timestral
- Your label: 
