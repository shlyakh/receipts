# Testing newly released models on data they cannot have seen

Research pass on Nov 13, 2026, for the open research task in `DECISIONS.md`. Power
figures are the research agent's own arithmetic, not from a source. Items marked
(unverified) were not confirmed on a page it opened.

## How others handle leakage

- Across 22 models and 401 datasets, only 6% of datasets appear in no pretraining
  corpus; correlated series overlapping in time also leak ("indirect leakage"). The
  paper calls for test periods after the latest training cutoff among compared models.
  https://arxiv.org/html/2510.13654v3
- Live benchmarks register forecasts before the truth exists and admit a model only
  after its release, some on energy series. https://arxiv.org/html/2512.20761v2
- Memorisation diagnostics are weak so far (https://arxiv.org/html/2605.26161), and a
  post-release hold-out removes memorisation of a window but not familiarity with a
  domain (https://arxiv.org/abs/2609.10357).
- Disclosed training data: Chronos-2 lists a 370-series electricity set, smart-meter and
  building sets, and no PJM or EIA series (https://arxiv.org/html/2510.15821). Timestral
  does not name its real datasets or cutoff. Nobody discloses EIA-930, which is not
  proof of absence.

## Options

| Option | What it lets us claim | What it does not show | Effort |
|---|---|---|---|
| 1. Prospective panel: frozen code and weights, about 20 zones across several operators, weekly origins | measured on data that did not exist at release | anything about JC and DOM alone within 4 to 6 months | medium |
| 2. Semi-synthetic replay: a load model plus block-bootstrapped real residuals, driven by shifted weather, from two generator families | the ranking holds on look-alike load that cannot be memorised | real-world accuracy | 1 to 2 days after validation |
| 3. Memorisation probe on transformed real data (zone differences, permuted weeks) | no sign that the result depends on recall | absence of leakage | hours |
| 4. Fully generative or bottom-up building simulation | — | not recommended: unvalidated, weeks of work | high |

- Power for option 1: pooling K zones multiplies effective weeks by K / (1 + (K-1)ρ),
  where ρ is the correlation of weekly error differences between zones. Twenty zones
  give 3x at ρ = 0.3 and 1.9x at ρ = 0.5; other operators lower ρ more than extra PJM
  zones do. Daily origins give about 1.5x, because adjacent windows share 144 hours.
- Operators already simulate this way: PJM fits hourly regressions per zone and replays
  31 weather years, each shifted, for 403 scenarios.
  https://www.pjm.com/-/media/DotCom/planning/res-adeq/load-forecast/load-forecast-supplement-2026.pdf
- Bias by construction: a simulator built from a regression is easy for a regression.
  General guidance is to vary the generating mechanism and prefer resampling real data
  (https://pmc.ncbi.nlm.nih.gov/articles/PMC6492164/ ,
  https://pmc.ncbi.nlm.nih.gov/articles/PMC12129352/). In practice: two generator
  families, neither a competitor; keep real residuals; check that real pre-release
  rankings are reproduced.
- Replayed weather years still correlate with that year's public load (indirect
  leakage). Training priors such as Gaussian-process synthetic data are circular.
- No newly started public US hourly zonal series was found.

## One-day validation experiment proposed

On origins before the scored window (2023 to 2024), where Chronos-2 and TimesFM 2.5 can
be scored on real data (a new protocol version; the 52 scored origins are not re-run):

1. Fit two generators on 2019 to 2022 only: an additive/spline model and a similar-day
   analog model, each adding block-bootstrapped real residuals.
2. Simulate the same origins, driven by calendar-shifted weather.
3. Pass if, per zone, the simulated error ratio falls inside the real 90% interval and
   model order is preserved under both generators. Fail if the ratio moves when the
   generator family changes.
4. Also compare each model's error on real against transformed pre-release weeks; a
   large gap suggests recall.
