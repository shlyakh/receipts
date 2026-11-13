# How the baselines were chosen

A record of the method, kept so it can become a reusable research skill. It has two
parts: what was done first, and the search for standards that corrected it.

## Round 1: baselines from recent publications (Nov 12)

The first baseline set mirrored one recent study (the GB demand backtest,
`notes/moran.md`): same hour last week, a per-hour regression on the 7-day lag and
calendar, the same with temperature, and LightGBM on the same inputs. The regression
with temperature was fixed as the baseline of the primary comparison in `protocol.yaml`.

Weakness, noticed on Nov 13: none of this came from review papers, competitions or
operator practice, so "beats the baseline" could mean "beats a weak baseline".

## Round 2: search for the field's standards (Nov 13)

Procedure (the part to turn into a skill):

1. **Search four kinds of source**: tutorial and review papers; forecasting competitions
   and their overview papers; operator documentation; textbook and benchmark-suite
   examples.
2. **Extract from each**: the named benchmark, the winning method, the inputs, the
   horizon and the training window.
3. **Admission rule**: a method is "standard" if it is an organiser's benchmark in at
   least one competition, or is named in at least two independent reviews, or is
   documented operator practice.
4. **Filter** by fit to our horizon (a week ahead) and inputs (temperature only).
5. **Order into a ladder**: naive, univariate classical, field benchmark, tuned field
   benchmark, strong classical, tuned machine learning, operator forecast.
6. **Verify before implementing**: open the source and read the equation. Do not
   implement from a summary.
7. **Register before scoring**: write the definition into a protocol version, run the
   gate origins, tag, then score once.
8. **Record**: sources with URLs, the rule that admitted each method, exclusions with
   reasons, every tuning choice, and what could not be verified.

## What the search found

Full notes with sources: `notes/classical_baselines.md`.

| Rung | Method | Admitted by | Status here |
|---|---|---|---|
| 1 | Same hour last week | reviews call it a weak bar for aggregate load | scored (protocol-v1) |
| 2 | Double-seasonal exponential smoothing | reviews; short-lead method | not run |
| 3 | Lag regression with temperature | one recent study only | scored; the frozen primary baseline |
| 4 | Tao's Vanilla Benchmark | organiser's benchmark in GEFCom2012, 2014, 2017 | **scored (protocol-v1.1), two forms** |
| 5 | Vanilla + recency + holiday terms | a cited extension, 12 to 21% better | not run |
| 6 | Additive model (GAM) | operator use; competition winner | not run |
| 7 | Tuned LightGBM with rung 5 and 6 features | competition entries | partly (untuned LightGBM scored) |
| ref | PJM's own forecast | operator practice | no week-ahead archive found (unverified) |

## What was verified and what was not

- Verified from the paper (Ziel and Liu 2016, equations 10 and 11,
  https://arxiv.org/abs/1603.01376): the Vanilla equation, the 24-month training
  window, the absence of holiday terms and lagged load, and the use of an averaged
  temperature series.
- Not verified from an opened page: that the original GEFCom2012 form includes a linear
  trend (found in search summaries only). Both forms were therefore registered and
  scored.
- A decision made at the gate stage, before scoring: the gate origins showed the form
  without trend far behind on DOM. That prompted registering the trend form as a second
  row. It was not chosen after seeing scored results.

## What it changed

Vanilla with trend beats the frozen baseline by 23% on DOM and 18% on JC. Against it,
Chronos-2 with temperature is at 0.946 on DOM and 0.997 on JC (`results/README.md`). The
lesson for the skill: run the standards search before freezing the primary baseline.

## Limits of this round

- One search pass by one agent; queries were not logged individually.
- Rungs 5 and 6, the strong classical bar, are not run.
- The trailing-year window of the lag regression was never compared with two years.
