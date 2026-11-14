"""Scan, judge and run candidates in one command, each step a recorded headless run.

    uv run --project core python tools/pipeline.py claude                 # reuse the latest scan
    uv run --project core python tools/pipeline.py claude --scan --judge 5
    uv run --project core python tools/pipeline.py claude --only timestral timesfm-3

Steps (each is `claude -p "/<skill> ..."` through tools/run_skill.py):
  1. scan            only with --scan; otherwise the latest candidates/<provider>/scan_*.jsonl
  2. judge           the first --judge candidates that have no scorecard yet (the file is
                     ordered by fit to the spec), or exactly the ids given with --only
  3. run-candidate   every scorecard of this run's candidates labelled ACCEPT_RUN with no
                     receipt. Headless runs do not start model runs: if the model row is
                     not on the leaderboard the step stops and says what is needed.
Writes runs/pipeline_<id>.json (committed) and prints one line per candidate.
"""

from __future__ import annotations

import argparse
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tools.run_skill import run  # noqa: E402

NO_MODEL_RUNS = (
    "Headless pipeline run. If the model row this scorecard needs is already in "
    "results/leaderboard.csv, write the receipt (step 5) and report. If it is not, do NOT "
    "download weights, change code or run any model: stop and report which model row is "
    "missing and which steps of the skill a person has to run."
)


def scorecard(provider: str, cid: str) -> dict | None:
    path = ROOT / "scorecards" / provider / f"{cid}.json"
    return json.loads(path.read_text()) if path.exists() else None


def step(meta: dict) -> dict:
    keep = ("run_id", "exit_code", "timed_out", "is_error", "num_turns", "total_cost_usd")
    return {k: meta.get(k) for k in keep} | {"wall_seconds": meta.get("wall_seconds")}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("provider", choices=["claude", "youcom"])
    ap.add_argument("--scan", action="store_true", help="run a new scan first")
    ap.add_argument("--judge", type=int, default=2, help="how many unjudged candidates to judge")
    ap.add_argument("--only", nargs="+", default=[], help="candidate ids to process")
    ap.add_argument("--parallel", type=int, default=2, help="judge runs at the same time")
    ap.add_argument("--model", default="", help="model for every step; default is the CLI's own")
    a = ap.parse_args()
    started = datetime.now(UTC)
    out: dict = {"provider": a.provider, "started_at": started.isoformat(timespec="seconds")}

    if a.scan:
        out["scan"] = step(run("scan", a.provider, [], model=a.model))
    files = sorted(
        (ROOT / "candidates" / a.provider).glob("scan_*.jsonl"), key=lambda p: p.stat().st_mtime
    )
    if not files:
        sys.exit(f"no candidates file for {a.provider}: run with --scan")
    out["candidates_file"] = str(files[-1].relative_to(ROOT))
    cands = [json.loads(x) for x in files[-1].read_text().splitlines() if x.strip()]
    ids = [c["candidate_id"] for c in cands]
    if a.only:
        missing = [i for i in a.only if i not in ids]
        if missing:
            sys.exit(f"not in {out['candidates_file']}: {missing}")
        chosen = a.only
    else:
        chosen = [i for i in ids if scorecard(a.provider, i) is None][: a.judge]
    rows = {i: {"candidate_id": i} for i in chosen}

    to_judge = [i for i in chosen if scorecard(a.provider, i) is None]
    with ThreadPoolExecutor(max(1, a.parallel)) as pool:
        metas = pool.map(lambda i: run("judge", a.provider, [i], model=a.model), to_judge)
        for i, m in zip(to_judge, metas, strict=True):
            rows[i]["judge"] = step(m)

    for i in chosen:  # one at a time: receipts read and write the shared results
        card = scorecard(a.provider, i)
        if card and card.get("label") == "ACCEPT_RUN" and not card.get("receipt"):
            m = run("run-candidate", a.provider, [i], note=NO_MODEL_RUNS, model=a.model)
            rows[i]["run_candidate"] = step(m)
            rows[i]["run_candidate_report"] = m.get("result")

    for i in chosen:
        card = scorecard(a.provider, i) or {}
        receipt = card.get("receipt") or {}
        rows[i] |= {
            "label": card.get("label"),
            "runnable_class": card.get("runnable_class"),
            "receipt_verdict": receipt.get("verdict"),
        }
    out["candidates"] = list(rows.values())
    steps = [out.get("scan")] + [
        r.get(k) for r in rows.values() for k in ("judge", "run_candidate")
    ]
    out["total_cost_usd"] = round(sum(s["total_cost_usd"] or 0 for s in steps if s), 2)
    pid = f"pipeline_{started:%Y%m%dT%H%M%S}_{a.provider}"
    (ROOT / "runs" / f"{pid}.json").write_text(json.dumps(out, indent=1) + "\n")
    print(f"{pid}: {out['candidates_file']}, estimated cost ${out['total_cost_usd']}")
    for r in out["candidates"]:
        label = r["label"] or "not judged"
        verdict = r["receipt_verdict"] or "none"
        print(f"  {r['candidate_id']}: {label} ({r['runnable_class']}), receipt: {verdict}")


if __name__ == "__main__":
    main()
