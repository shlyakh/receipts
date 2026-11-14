# Calendar and holiday inputs: who gets them, and what they are worth here

Written 2026-11-13 after Yuri asked why the benchmark does not use the calendar with
holidays, and whether every method can use it. Exploratory; nothing here is a registered
result.

## What each row uses today

| Row | Calendar it uses | Holidays |
|-----|------------------|----------|
| `seasonal_naive` | none | no |
| `lag_regression`, `lag_regression_temperature`, `lightgbm_temperature` | hour, day of week, year-end (24 Dec to 2 Jan) | yes, US federal |
| `vanilla_benchmark`, `vanilla_benchmark_trend` | month, weekday, hour | no (as published) |
| `lightgbm_competition` | 13 calendar features | yes, with holiday name and days to and from |
| `chronos2*`, `timesfm25*`, `timestral_temperature` | none supplied; the model sees timestamps or the load pattern only | no |
| `tabpfn_ts_v2_temperature` (not scored) | the package's automatic calendar features | none supplied by us |

So the calendar is used, but unevenly. The frozen baseline has a holiday term; the
primary challenger (Chronos-2 with temperature) gets no calendar at all; the field's
standard (Vanilla) has no holiday term. Rule 3 ("same inputs for every model") was
written for temperature only and says nothing about the calendar.

## Can every method use it?

The calendar is known in advance, so it raises no lookahead question and is the same in
every weather regime.

- Regressions and LightGBM: yes, as columns.
- Chronos-2: yes. The installed package (chronos-forecasting 2.3.2) accepts any number of
  known-future covariates, numeric or categorical (checked in its documentation and by
  the run below).
- TabPFN-TS: yes, as feature columns.
- TimesFM 2.5: only through its linear covariate add-on (`models_ff/timesfm25_xreg.py`).
- Timestral through FoundationForecast: not checked.
- Univariate rows: no, by definition.

## Check 1: how large is the holiday effect in the scored results?

From the stored protocol-v1 and v1.3 forecasts, forecast weather, the 48 kept weeks.
Twelve federal holidays fall in them (288 of 8,064 hours per zone, 3.6%). Mean absolute
error in MW:

| Row | DOM holiday | DOM other | JC holiday | JC other |
|-----|------------:|----------:|-----------:|---------:|
| Chronos-2 with temperature | 784 | 732 | 209 | 218 |
| Timestral with temperature | 702 | 658 | 186 | 186 |
| Lag regression with temperature (has a holiday term) | 981 | 1,006 | 301 | 265 |
| Vanilla with trend (no holiday term) | 730 | 778 | 240 | 218 |
| LightGBM competition (rich holiday features) | 708 | 715 | 200 | 204 |
| Lag regression, no weather | 2,208 | 1,508 | 581 | 341 |

Reading: Chronos-2 with temperature is 7% worse on holidays on DOM and 4% better on JC.
If its holiday error fell to its ordinary-day level, the DOM weekly error would drop by
about 0.25% and JC would not change. Holidays cannot move the headline ratios much on
this benchmark. Limits: 12 days; days next to a holiday and the Christmas week are
counted as ordinary.

## Check 2: does Chronos-2 improve when handed the calendar? (gate origins only)

Run from the scratchpad on the six gate origins (four kept weeks, one holiday, Columbus
Day), `forecast_aifs` regime, pinned weights, CPU. The temperature-only run reproduced
the stored gate row exactly.

| Chronos-2 covariates | DOM MAE | JC MAE |
|----------------------|--------:|-------:|
| temperature | 322 | 86 |
| temperature, holiday, year-end | 368 | 104 |
| temperature, holiday, year-end, day of week, hour | 401 | 110 |

On these four weeks the calendar made Chronos-2 worse, by 14 to 28%. Four weeks check
the pipeline and are not evidence, but they show the gain is not guaranteed for a
zero-shot model: a holiday flag is zero for almost all of an 85-day context and the
year-end flag is constant in it.

## Consequence for the requirements

See decision 30 in `DECISIONS.md` and the `calendar` block of `protocol-v2-draft.yaml`.
