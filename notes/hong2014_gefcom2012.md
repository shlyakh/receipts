# Hong, Pinson and Fan (2014): Global Energy Forecasting Competition 2012

- Citation: T. Hong, P. Pinson, S. Fan, "Global Energy Forecasting Competition 2012",
  International Journal of Forecasting 30 (2014) 357-363.
- DOI: https://doi.org/10.1016/j.ijforecast.2013.07.001
- Read in full on 2026-11-13 from a copy supplied by Yuri. The paper itself is not
  stored in this repository (CLAUDE.md rule 9: URLs and short paraphrases only).
- Why it matters here: it is the primary source for Tao's Vanilla Benchmark, the row
  `vanilla_benchmark_trend` in `protocol-v1.1.yaml`.

## What the paper states (paraphrased)

### The benchmark model (section 2.3)

A multiple linear regression with an intercept and these terms, referring back to
Hong's 2010 dissertation:

- Main effects: a trend (a number that increases by one with each observation in time
  order), temperature of the current hour, its square and its cube, month (12 classes),
  weekday (7 classes) and hour (24 classes).
- Interactions: hour by weekday; temperature, its square and its cube each by month;
  temperature, its square and its cube each by hour.

**So the original benchmark does include a linear trend.** This settles the point that
`BASELINES.md` had recorded as found in search summaries only.

How the organisers ran it:

- Fitted on the full 4.5 years of history (less the eight weeks held out).
- One model per weather station (11 stations) for each zone; the station with the best
  fit is used for that zone.
- No holiday terms, no data cleansing, no ensembling (table 2).
- For the forecast week the temperature input was the average of the same date and hour
  over the previous four years, because no temperature forecast was supplied.

### The competition

- Load track: hourly load for a US utility with 20 zones plus the system total; eight
  held-out weeks to backcast with actual temperatures and one week to forecast without
  them. Score: a weighted root mean square error.
- The benchmark was one submission and finished behind every selected entry in the
  results table (table 3). It is a bar to beat, not a strong model.
- Methods of the leading entries (table 2): regression with cleansing and holiday terms,
  gradient boosting with Gaussian processes, semi-parametric and additive models with
  splines, random forests, neural networks. Most used holiday effects and some form of
  weather-station selection.
- The organisers note that all reporting teams forecast temperature and load separately
  and simply fed one into the other, and that a rolling forecast origin was left out of
  the design.

## How our row differs from the original

| Aspect | Original benchmark | Our `vanilla_benchmark_trend` |
|---|---|---|
| Terms | as above, with trend | same terms, with trend |
| Training window | 4.5 years | trailing 730 days (from Ziel and Liu 2016) |
| Temperature | best-fitting single station of 11 | average of the zone's stations |
| Forecast-week temperature | four-year average for that date and hour | the regime's temperature (forecast or actual) |
| Refit | once | at every weekly origin |

The no-trend row `vanilla_benchmark` follows the equation as printed in Ziel and Liu
(2016) and is therefore a variant, not the original form.

## Consequences

- The trend form is the faithful one. Both rows stay as registered and scored under
  `protocol-v1.1`; nothing is rerun.
- The planned `protocol-v2` can name Vanilla with trend as the primary baseline on a
  verified basis.
- Stronger classical rungs suggested by the leading entries (holiday terms, station
  selection, additive models) remain open; see `notes/classical_baselines.md`.
