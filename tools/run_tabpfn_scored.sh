#!/bin/bash
# Run the deferred TabPFN scored run registered in protocol-v1.3, then score it.
#
#   tools/run_tabpfn_scored.sh
#
# About 50 hours on CPU (624 windows at about 5 minutes). Safe to interrupt: each
# finished cutoff is saved, and running this script again resumes where it stopped.
# The forecast step runs at the tag `protocol-v1.3` (the adapter refuses otherwise);
# the script puts the working tree back on `main` when it ends or is interrupted.
# Nothing is committed or pushed; the last lines say what to commit.
set -euo pipefail

cd "$(dirname "$0")/.."
TAG=protocol-v1.3
OUT=results/models_v13/forecasts/tabpfn_ts_v2_temperature.parquet
LOG_DIR=data/logs
LOG="$LOG_DIR/tabpfn_scored_$(date +%Y%m%d_%H%M%S).log"
mkdir -p "$LOG_DIR"

if [ -n "$(git status --porcelain --untracked-files=no)" ]; then
  echo "Tracked files have uncommitted changes. Commit or stash them first." >&2
  exit 1
fi
if [ "$(git rev-parse --abbrev-ref HEAD)" != "main" ]; then
  echo "Start from the main branch (currently on $(git rev-parse --abbrev-ref HEAD))." >&2
  exit 1
fi

back_to_main() { git switch --quiet main || echo "Could not switch back to main; run: git switch main" >&2; }
trap back_to_main EXIT

if [ -f "$OUT" ]; then
  echo "Forecasts already exist at $OUT; skipping the forecast step."
else
  git switch --quiet --detach "$TAG"
  echo "Forecasting at $TAG. Log: $LOG"
  echo "To stop: Ctrl-C. To resume: run this script again."
  # caffeinate keeps the Mac awake while the run is going.
  caffeinate -i uv run --project models_ff python models_ff/tabpfn_ts_v2.py scored 2>&1 | tee -a "$LOG"
  git switch --quiet main
fi

echo "Scoring."
uv run --project core python -m harness.v13 score scored 2>&1 | tee -a "$LOG"

cat <<EOF

Done. Review, then commit the results:
  git add $OUT results/models_v13
  git status --short results/models_v13
The resume files in results/models_v13/partial/ do not need committing.
EOF
