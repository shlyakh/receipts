# Task brief: Friday Nov 13

Precondition: every acceptance criterion in `TONIGHT.md` passes.
Still infrastructure only. No You.com agent code (see the phase gate in `CLAUDE.md`).

## 1. Foundation-model rows (morning)

- Create the `models/` environment. Install `foundationforecast` and
  `chronos-forecasting`.
- Verify before use (rule 7): model class names, how known-future covariates are
  passed, quantile output. Record findings in `notes/foundationforecast.md`.
- Time ONE window per model on this laptop before any full run. Record seconds per
  forecast in the same notes file.
- Rows, in this order, both weather regimes, harness-owned cutoff loop:
  1. Chronos-2 via the direct adapter (the fallback; also the cross-check)
  2. Chronos-2 via FoundationForecast: must agree closely with row 1 on 3 windows
  3. Timestral-209M
  4. t0-gamma (gated: needs `HF_TOKEN` and accepted terms)
  5. TiRex-2
  6. TimesFM 2.5 (label "univariate" if run without covariates)
  7. Kumo Forecast (univariate; intervals via conformal)
  8. TimesFM-3 last (non-commercial weights; flag on the leaderboard)
- For covariate-capable models also add a "no weather" row, so the weather gain per
  model can be reported the same way as for the regression.
- Optional: calendar terms as extra covariates for Chronos-2 and Timestral.
- Stop adding models when the time budget for full runs is spent. Rows 1 to 4 are
  the minimum for the demo.

## 2. Statistics

- Error ratio vs. the lag regression with weather, per zone and regime.
- Weather gain per forecaster: with weather / without weather.
- Intervals: resample whole weeks, 2,000 draws, seed from `protocol.yaml`, same
  resampled weeks for both arms; 90% percentile intervals.

## 3. Spec and schema (midday)

- Write `spec.yaml` and `schemas/scorecard.schema.json` from `REFERENCE.md`.
- Yuri confirms or overrules the labels in `eval/items.yaml`.

## 4. Rough `/judge` prototype (midday)

- A project skill at `.claude/skills/judge/SKILL.md`. Input: one item id or URL.
  Output: one scorecard JSON in `scorecards/`, validated against the schema.
- Search provider today: Claude's own web search and fetch. All retrieved material
  goes through the evidence ledger (`evidence/*.jsonl`); the judge reads the ledger.
- Rules for the judge: cite a primary source for every claim; when none can be
  found, say so; never read LinkedIn pages directly.
- Run it on all 11 items. Write the agreement table (judge label vs. ground truth)
  to `eval/results.md`. Fix prompts once. Do not tune until it matches.
- Optional: install the `reviewer-2` and `stats-reviewer` agents from
  `dgilford/ai-science-toolkit` and use them as the evidence-strength critic.

## 5. Saturday readiness (afternoon / evening)

- You.com: create the API key, connect the MCP server, make one search call and one
  research call, write down the exact tool names. Nothing more.
- Test headless invocation of the judge from a shell script (the dashboard's button
  path on Saturday).
- Pre-download every model's weights. Confirm the harness runs with Wi-Fi off.
- Record a backup screen capture of the harness producing a leaderboard row.
- Update `README.md`: what exists as of Friday night, with commit hashes.

## Acceptance criteria

- [ ] Leaderboard has at least rows 1 to 4 for both zones and both regimes, with
      ratios and intervals.
- [ ] `spec.yaml` and the scorecard schema exist; labels confirmed.
- [ ] `/judge` produced 11 schema-valid scorecards; agreement table written.
- [ ] You.com MCP smoke test passed; tool names recorded.
- [ ] Harness runs offline.
