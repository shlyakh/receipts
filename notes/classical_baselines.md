# Standard baselines for week-ahead hourly load forecasting

Research pass on Nov 13, 2026. Claims marked (unverified) were not confirmed on a page
the research agent opened. Adding any rung below changes the frozen protocol, so it
needs a new protocol version and a line in `DEVIATIONS.md`.

## What the field treats as standard

- **Tao's Vanilla Benchmark.** One multiple linear regression with no lagged load:
  month, day of week by hour, and a cubic temperature polynomial interacted with month
  and with hour, fitted on the most recent 24 months. It was the named benchmark in
  GEFCom2012, 2014 and 2017. Equations: https://arxiv.org/pdf/1603.01376
- **Recency extension.** Adds lagged hourly temperatures and daily moving-average
  temperatures, with their number chosen on a validation year; reported 12 to 21%
  better than Vanilla.
  https://econpapers.repec.org/RePEc:eee:intfor:v:32:y:2016:i:3:p:585-597
- **Additive models (GAMs).** Calendar, lagged demand and forecast temperature through
  smooth terms; documented up to seven days ahead and used by an operator.
  https://econpapers.repec.org/RePEc:msh:ebswps:2010-17
- **Exponential smoothing with two seasonal cycles** (Taylor): a short-lead method; it
  beat a weather-based model only to about 5 hours ahead. Useful as a univariate rung.
  https://blog.drhongtao.com/2018/12/temperature-based-models-vs-time-series-models.html
- **Operator practice.** PJM forecasts seven days ahead for 22 zones with eight models,
  mostly neural networks, on about 30 weather stations; a similar-day lookup often does
  best on holidays. https://insidelines.pjm.com/?p=2804
- No study was found that compares foundation models with Vanilla or a GAM; their
  comparators are seasonal naive, SARIMA, Prophet or deep networks.
- PJM's published historical forecasts are day-ahead and same-day, not week-ahead
  (https://www.pjm.com/markets-and-operations/data-dictionary.aspx). Whether 7-day
  vintages are archived anywhere is (unverified).

## Baseline ladder proposed

| # | Method | Have it? | Effort | What a result against it means |
|---|---|---|---|---|
| 1 | Same hour last week | yes | 0 | losing means something is broken |
| 2 | Double-seasonal Holt-Winters or MSTL | no | 2 h | fair bar for models without weather |
| 3 | Current lag-168 regression with temperature | yes | 0 | continuity with the headline |
| 4 | Tao's Vanilla Benchmark, 2 to 3 years of training | no | 2 to 3 h | the field's minimum bar |
| 5 | Vanilla + recency + holiday terms | no | half a day | beats a tuned regression |
| 6 | GAM: temperature smooths, smoothed temperature, hour by day type, lag-168 load | no | 1 day | the strong classical bar |
| 7 | LightGBM, tuned, with the features of rungs 5 and 6 | partly | half a day | beats tuned machine learning |
| ref | PJM's own forecast, if a 7-day archive exists | (unverified) | ? | operational value |

Temperature alone is enough for every rung. The rung the literature would most readily
accept as "the baseline to beat" is rung 4; rungs 5 and 6 carry the strong claim.

## Repeatable procedure for another problem

1. Search four kinds of source: tutorial and review papers, competitions and their
   overview papers, operator documentation, textbook and benchmark-suite examples.
2. From each, extract the named benchmark, the winning method, inputs, horizon and
   training window.
3. Call a method standard if it is an organiser's benchmark in a competition, or named
   in two independent reviews, or documented operator practice.
4. Filter by horizon and input fit; order into a ladder.
5. Record queries and dates, a URL per method, the rule that admitted it, exclusions
   with reasons, every tuning choice, and what could not be verified.

## Ways baselines get weakened (check ours against these)

- Training window: a single trailing year cannot separate season from temperature
  (the agent's inference); Vanilla is specified with two years.
- Only naive baselines; a smoothing method used beyond its horizon; no holiday
  handling; a single weather station; untuned recency terms; actual temperature used in
  the forecast period; uneven tuning effort between baseline and challenger.
