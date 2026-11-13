"""Fill a scorecard's receipt from the scored results. Numbers come only from results/.

    uv run --project core python tools/receipt.py scorecards/claude/item-02.json \
        chronos2_temperature --claimed "..." --mismatch "..."
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from harness.data import load_protocol  # noqa: E402
from harness.stats import verdict  # noqa: E402

from tools.validate_scorecard import errors  # noqa: E402

# protocol verdicts -> receipt wording (a transfer test, never true / false). What
# "transfers" means depends on what was claimed.
WORDS = {
    "tie": {  # the claim: model and regression are about equal
        "practical_tie": "transfers",
        "worth_switching": "does_not_transfer",
        "regression_clearly_better": "does_not_transfer",
        "inconclusive": "partially",
    },
    "model_better": {  # the claim: the model beats a regression-like baseline
        "worth_switching": "transfers",
        "practical_tie": "does_not_transfer",
        "regression_clearly_better": "does_not_transfer",
        "inconclusive": "partially",
    },
}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("scorecard")
    ap.add_argument("model")
    ap.add_argument("--claimed", required=True)
    ap.add_argument("--mismatch", required=True)
    ap.add_argument("--claim-kind", required=True, choices=sorted(WORDS))
    a = ap.parse_args()
    proto = load_protocol()
    bar = proto["primary_comparison"]["bar"]
    st = pd.read_parquet(ROOT / "results" / "stats.parquet")
    lb = pd.read_parquet(ROOT / "results" / "leaderboard.parquet")
    rows = st[(st["kind"] == "vs_baseline") & (st["model_a"] == a.model) & (st["metric"] == "mae")]
    if rows.empty:
        sys.exit(f"{a.model} has no scored row; run it first")
    measured = [
        {
            "zone": r.unique_id,
            "regime": r.regime,
            "error_ratio": round(float(r.ratio), 3),
            "ci90": [round(float(r.ci90_low), 3), round(float(r.ci90_high), 3)],
        }
        for r in rows.sort_values(["regime", "unique_id"]).itertuples()
    ]
    # The verdict is read in the protocol's primary regime only.
    regime = proto["primary_comparison"]["regime"]
    per_zone = {
        m["zone"]: verdict(m["ci90"][0], m["ci90"][1], bar)
        for m in measured
        if m["regime"] == regime
    }
    words = {WORDS[a.claim_kind][v] for v in per_zone.values()}
    lrow = lb[lb["model"] == a.model].iloc[0]
    n_after = lrow["n_windows_after_weights"]
    if pd.notna(n_after) and n_after < lrow["n_windows"] / 2:
        overall = "untestable"  # mostly weeks the model may have been trained on
    else:
        overall = words.pop() if len(words) == 1 else "partially"
    card = json.loads(Path(a.scorecard).read_text())
    card["receipt"] = {
        "claimed": a.claimed,
        "measured": measured,
        "horizon_mismatch": a.mismatch,
        "n_windows": int(lrow["n_windows"]),
        "n_windows_after_weights": None if pd.isna(n_after) else int(n_after),
        "verdict": overall,
    }
    errs = errors(card)
    if errs:
        sys.exit("scorecard would be invalid:\n" + "\n".join(errs))
    Path(a.scorecard).write_text(json.dumps(card, indent=1) + "\n")
    print(json.dumps({"per_zone": per_zone, "verdict": overall}))


if __name__ == "__main__":
    main()
