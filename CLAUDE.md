# Receipts for Forecasting Papers

A "live data scientist" agent: it finds newly published forecasting methods, judges
them against a written problem spec with citations, and for runnable ones measures
them on our own benchmark ("claimed vs. measured").

Benchmark: PJM hourly load, zones JC and DOM, week-ahead (168 h).

Read `DECISIONS.md` (fixed choices) and `REFERENCE.md` (endpoints, formulas, schemas)
before writing code. Task briefs, in order: `TONIGHT.md` (Thu), `FRIDAY.md` (Fri),
`HACKATHON.md` (Sat). Do one brief at a time; do not start the next until the
current one's acceptance criteria pass. `notes/moran.md` describes the study whose
design the backtest mirrors.

## Phase gate

- Thu Nov 12 / Fri Nov 13, 2026: infrastructure only (data, harness, baselines,
  foundation-model rows, spec, scorecard schema, rough `/judge` prototype).
- Sat Nov 14 (hackathon): the You.com-powered agent.
- Do NOT write any You.com integration, `/scan`, `/run-candidate`, or dashboard code
  before Saturday. If a task seems to need it, stop and ask.

## Hard rules

1. **The harness owns the cutoffs.** Forecast origins come from `protocol.yaml`, never
   inferred from data or from a library's cross-validation helper. Loop over cutoffs
   and call each model once per cutoff.
2. **No lookahead.** For a cutoff `c`, a model may see load up to `c` and only the
   weather that the active regime allows for hours `c+1 .. c+168`.
3. **Same inputs for every model.** Within a weather regime, every model (regression,
   LightGBM, foundation models) gets the identical temperature series. A model that
   cannot use covariates is labelled "univariate" on the leaderboard.
4. **Two weather regimes, always reported separately:** `oracle` (reanalysis actuals)
   and `forecast` (lead-matched archived forecasts). Never mix them in one row.
5. **Protocol is frozen.** After `protocol.yaml` is tagged `protocol-v1`, do not edit
   it. Changes go in a new version plus a dated line in `DEVIATIONS.md`.
6. **Raw data is hashed.** `fetch.py` writes SHA-256 hashes to `fetch_manifest.json`;
   scoring refuses to run if a raw file does not match.
7. **Verify, don't trust.** Items listed under "Unverified" in `REFERENCE.md` must be
   checked against the installed package or the live API before use. Say what you
   found.
8. **Secrets** live in `.env` (git-ignored). Never print, log, or commit them.
9. **Third-party material.** Write our own code. Do not copy code from
   `AndyMoran/gb-weather-private` (no licence stated). Do not commit the text of
   other people's posts or articles; store URLs and short paraphrased claims.
10. **LinkedIn** is not a source (decision 21). No login, no crawling, no fetching
    post pages, no snippets as evidence. A stored LinkedIn URL is an identifier
    only. If a task seems to need LinkedIn content, stop and ask.
11. **One primary comparison.** `protocol.yaml` names it (Chronos-2 with temperature
    vs. the lag regression with temperature, forecast regime, per zone). Every
    other result is labelled secondary and never changes the outcome sentence.
12. **Gate, tag, then score once.** Before `protocol-v1` is tagged, code runs only
    on the gate origins listed in the protocol. The 52 scored origins are run once,
    after the tag.
13. **Pin model weights.** Load every foundation model at a recorded Hugging Face
    revision; the leaderboard row carries the revision and its date.

## Environment

- Python 3.12, managed with `uv`.
- Two environments that exchange parquet files, so a model dependency cannot break
  the baselines:
  - `core/`: pandas, pyarrow, requests, holidays, statsmodels, lightgbm
  - `models/`: chronos-forecasting and other direct model adapters
  - `models_ff/`: FoundationForecast from GitHub at a pinned commit (it conflicts with
    `models/`, so it has its own environment)
- Mac laptop. Default to CPU. Use MPS only after one window matches CPU output.

## Layout

```
protocol.yaml          frozen backtest definition
spec.yaml              problem spec the judge scores against (Friday)
fetch.py               data + weather pull, writes fetch_manifest.json
harness/               backtest loop, metrics, model adapters
data/raw/              untouched downloads (git-ignored)
data/processed/        parquet: load, weather_oracle, weather_forecast
results/               leaderboard.parquet, per-window forecasts
eval/items.yaml        11 labelled candidates for testing the judge
notes/                 moran.md and other reading notes
schemas/               scorecard JSON schema (Friday)
scorecards/ evidence/  judge output and the search evidence ledger (Friday)
.claude/skills/        judge (Friday); scan, run-candidate (Saturday)
```

## Conventions

- Long format: `unique_id, ds, y`; timestamps stored in UTC, converted once.
- Every leaderboard row carries: model, zone, regime, n_windows, metrics, runtime,
  git commit, protocol version, and for foundation models the weights revision,
  its date and `n_windows_after_weights`.
- The receipt is a transfer test: say "transfers / does not transfer", never
  "the claim is true / false". Name the baseline "temperature-only regression".
- Small commits with plain messages. Run the harness on 2 windows before any full run.
- When something cannot be done as specified, stop and report; do not substitute a
  different method silently.
