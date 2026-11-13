---
name: run-candidate
description: Run a judged candidate on the frozen benchmark and write its receipt. Use for "/run-candidate <candidate id>".
---

# /run-candidate <candidate_id> [provider]

Only for scorecards labelled `ACCEPT_RUN`. Read `CLAUDE.md` hard rules 1 to 5, 12, 13.

1. Read `scorecards/<provider>/<candidate_id>.json`. Find the model row it needs.
   - Already on the leaderboard (`results/leaderboard.csv`): skip to step 5.
   - `ff_native_exog` or `ff_univariate`: add an entry to `SPECS` in
     `models_ff/run_ff.py` (settings fixed now, context 2,048 hours, never tuned).
   - `direct_adapter`: stop and report what adapter is needed. Do not improvise one.
2. Pin the weights: look up the repository's current commit, then
   `uv run --project models python models/download.py <repo_id> <full sha>`.
   Note the weights date it prints.
3. Gate first: `uv run --project models_ff python models_ff/run_ff.py <name> gate`,
   then `uv run --project core python -m harness.score gate`. Check the row is
   complete and plausible. If it fails, stop and report; do not touch the scored set.
4. Commit the code. Then score once:
   `uv run --project models_ff python models_ff/run_ff.py <name> scored`
   `uv run --project core python -m harness.score scored`
   `uv run --project core python -m harness.stats scored`
   A model is run on the scored weeks once. If its file already exists in
   `results/forecasts/`, do not run it again.
5. Write the receipt:
   `uv run --project core python tools/receipt.py scorecards/<provider>/<candidate_id>.json <model_name> --claim-kind <tie|model_better> --claimed "<claim, paraphrased>" --mismatch "<how the claim's setup differs from ours>"`
   The tool fills the measured ratios, intervals, weeks after the weights and the
   verdict from `results/`; it never takes numbers from you.
6. Report the receipt: claimed, measured per zone with the 90% range, the verdict,
   the setup mismatch, and the count of weeks after the weights. Say "transfers" or
   "does not transfer", never "true" or "false".
