# Task brief: Friday Nov 13

Precondition: every acceptance criterion in `TONIGHT.md` passes.
Still infrastructure only. No You.com agent code (see the phase gate in `CLAUDE.md`).
Experimenting with Claude and other LLMs for the judge prototype is fine.

## 1. Foundation-model rows (morning, hard stop at 12:00)

- Create the `models/` environment. Install `foundationforecast` and
  `chronos-forecasting`.
- Verify before use (rule 7): model class names, how known-future covariates are
  passed, quantile output. Record findings in `notes/foundationforecast.md`.
- Time ONE window per model on this laptop before any full run. Record seconds per
  forecast in the same notes file.
- Load every model at a pinned Hugging Face revision. Each leaderboard row carries
  the revision hash, its commit date, and `n_windows_after_weights` (scored windows
  that start after that date).

**Required (the headline):**

1. Chronos-2 via the direct adapter, with temperature and without, both regimes,
   both zones, all 52 windows.

**Stretch, in this order, until 12:00. Target: 2 to 3 models in total.**

2. Chronos-2 via FoundationForecast: must agree closely with row 1 on 3 windows
   (cross-check only; not a separate leaderboard model).
3. TimesFM 2.5 (label "univariate" if run without covariates).
4. Timestral-209M. If its id failed the overnight check, the next
   covariate-capable model in `REFERENCE.md` takes its place.
5. Chronos-2 with a 48-hour data gap: context ends 48 hours before the cutoff,
   forecast 216 hours, score the same 168. Weather inputs unchanged.
   Pre-registered secondary; it measures how much the idealised cutoff helps.
6. Anything else in `REFERENCE.md` (t0-gamma, TiRex-2, Kumo Forecast, TimesFM-3
   with its non-commercial flag).

- For each covariate-capable model also add a "no weather" row, so the weather gain
  can be reported the same way as for the regression.
- Whatever is not finished by 12:00 is not on Saturday's leaderboard.

## 2. Statistics

- Primary: error ratio of Chronos-2 with temperature vs. the lag regression with
  temperature, forecast regime, per zone, with its outcome sentence from
  `protocol.yaml`.
- Secondary, labelled as such: oracle regime; per-lead-day ratio (day 1 to 7);
  weather gain per forecaster; other models; the 48-hour-gap row; for any model
  whose weights postdate part of the window, the ratio on the post-weights windows.
- Intervals: resample whole weeks, 2,000 draws, seed from `protocol.yaml`, same
  resampled weeks for both arms; 90% percentile intervals.
- Leakage statement per model: "N of 52 scored weeks postdate the weights". Check
  the Chronos-2 and TimesFM 2.5 weight dates; both are believed to predate the
  whole window, but that is unverified.

## 3. Spec and schema (midday)

- Write `spec.yaml` and `schemas/scorecard.schema.json` from `REFERENCE.md`.
- Missing-source rule, written into `spec.yaml`: a claim with no primary source is
  capped at `PARTIAL`, unless the candidate is itself a runnable model release.
- **Yuri labels the 11 items blind** (from title, claim and sources, without the
  proposed labels), about 15 minutes. Keep both columns in `eval/items.yaml`:
  `label_proposed` and `label_yuri`. Ground truth is `label_yuri`. List the
  disagreements in `eval/results.md`.
- Give every item a non-LinkedIn primary URL, or drop it from the set.

## 4. Rough `/judge` prototype (midday)

- A project skill at `.claude/skills/judge/SKILL.md`. Input: one item id or URL.
  Output: one scorecard JSON in `scorecards/`, validated against the schema.
- Search provider today: Claude's own web search and fetch. All retrieved material
  goes through the evidence ledger (`evidence/*.jsonl`); the judge reads the ledger.
- Rules for the judge: cite a primary source for every claim; when none can be
  found, say so; LinkedIn is not a source (a LinkedIn URL is stored as an
  identifier and never fetched).
- Run it on the evaluation set. Write the agreement table (judge label vs.
  `label_yuri`) to `eval/results.md`, with each miss explained. This is a
  regression test, not an accuracy figure. Fix prompts once. Do not tune until it
  matches.
- This prototype is for learning. Saturday's `/judge` is written fresh against
  You.com; only the schema, the evaluation set and the lessons carry over.
- Open the zip in Zenodo record 24161799 and confirm the GB weather-study ratios
  and gains against `weather_study/RESULTS.md`. Update `notes/moran.md`.
- Optional: install the `reviewer-2` and `stats-reviewer` agents from
  `dgilford/ai-science-toolkit` and use them as the evidence-strength critic.

## 5. Saturday readiness (afternoon / evening)

- You.com: create the API key, connect the MCP server, make one search call and one
  research call, write down the exact tool names. Check that the Zenodo record for
  item-02 is findable through You.com search. Nothing more.
- Pre-download every model's weights. Confirm the harness runs with Wi-Fi off.
- Record a backup screen capture of the harness producing a leaderboard row.
- Update `README.md`: what exists as of Friday night, with commit hashes.
- Optional: headless invocation of the judge from a shell script (only needed if
  the dashboard button survives Saturday's cuts).

## Acceptance criteria

- [ ] Leaderboard has Chronos-2 with and without temperature for both zones and
      both regimes, with the primary ratio, its interval and its outcome sentence.
- [ ] Every model row carries a pinned revision and `n_windows_after_weights`.
- [ ] `spec.yaml` and the scorecard schema exist; items labelled blind by Yuri.
- [ ] `/judge` produced schema-valid scorecards for the evaluation set; agreement
      table written with misses explained.
- [ ] You.com MCP smoke test passed; tool names recorded.
- [ ] Harness runs offline.
