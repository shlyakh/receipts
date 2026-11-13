"""Backtest loop. The harness owns the cutoffs (CLAUDE.md rule 1): it reads them from
protocol.yaml and calls each model once per cutoff.

    uv run --project core python -m harness.run gate            # the 4 gate origins
    uv run --project core python -m harness.run scored          # the 52 scored origins
    uv run --project core python -m harness.run gate --limit 2  # smoke test

Forecasts go to results/forecasts/<model>.parquet (gate set: results/gate/forecasts/) with columns
model, unique_id, regime, cutoff, ds, y_hat, runtime_s, git_commit, protocol_version.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fetch import verify_manifest  # noqa: E402

from harness.baselines import MODEL_PROTOCOL, MODELS  # noqa: E402
from harness.data import ROOT, V12_REGIMES, Data, load_protocol, origins  # noqa: E402

REGIMES = ["oracle", "forecast"]
V12_DIR = "weather_v12"  # draft protocol-v1.2 rows: results/<set>/weather_v12/forecasts/
V12_VERSION = "protocol-v1.2-draft"


def git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=ROOT, capture_output=True, text=True, check=False
    ).stdout.strip()


def git_commit() -> str:
    dirty = "-dirty" if git("status", "--porcelain", "--untracked-files=no") else ""
    return git("rev-parse", "--short", "HEAD") + dirty


def require_frozen(proto: dict) -> None:
    """The scored set runs only against the tagged, unchanged protocol (rule 5)."""
    tag = proto["version"]
    if proto.get("status") != "frozen":
        sys.exit("protocol.yaml is not marked frozen: scored origins must not be run yet")
    if not git("tag", "--list", tag):
        sys.exit(f"git tag {tag} does not exist: scored origins must not be run yet")
    if subprocess.run(
        ["git", "diff", "--quiet", tag, "--", "protocol.yaml"], cwd=ROOT, check=False
    ).returncode:
        sys.exit(f"protocol.yaml differs from tag {tag}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("which", choices=["gate", "ordering_gate", "scored"])
    ap.add_argument("--limit", type=int, help="run only the first N origins (smoke test)")
    ap.add_argument("--models", nargs="*", default=list(MODELS))
    ap.add_argument(
        "--regimes",
        nargs="*",
        choices=REGIMES + list(V12_REGIMES),
        default=REGIMES,
        help="default: the v1 regimes. The draft v1.2 regimes must be run on their own and "
        "write to a separate folder, so the v1 drop rule never sees them",
    )
    args = ap.parse_args()
    regimes = args.regimes
    v12 = bool(set(regimes) & set(V12_REGIMES))
    if v12 and not set(regimes) <= set(V12_REGIMES):
        sys.exit("run the v1 and the draft v1.2 regimes separately")

    proto = load_protocol()
    verify_manifest()
    if args.which == "scored":
        if args.limit:
            sys.exit("--limit is for the gate set; the scored set is run whole, once")
        if v12:
            sys.exit("the v1.2 weather regimes are a draft: scored origins must not be run")
        require_frozen(proto)

    cutoffs = origins(proto, args.which)[: args.limit]
    data = Data()
    commit = git_commit()
    out_dir = ROOT / "results" if args.which == "scored" else ROOT / "results" / args.which
    out_dir = (out_dir / V12_DIR if v12 else out_dir) / "forecasts"
    out_dir.mkdir(parents=True, exist_ok=True)

    for name in args.models:
        fn, uses_weather = MODELS[name]
        frames = []
        for regime in regimes:
            for zone in proto["zones"]:
                for cutoff in cutoffs:
                    hist = data.history(zone, cutoff)
                    temp = data.temperature(zone, cutoff, regime) if uses_weather else None
                    t0 = time.perf_counter()
                    y_hat = fn(hist, temp, cutoff)
                    runtime = time.perf_counter() - t0
                    assert len(y_hat) == proto["horizon_hours"]
                    frames.append(
                        pd.DataFrame(
                            {
                                "model": name,
                                "unique_id": zone,
                                "regime": regime,
                                "cutoff": cutoff,
                                "ds": y_hat.index,
                                "y_hat": y_hat.to_numpy(),
                                "runtime_s": runtime,
                            }
                        )
                    )
        df = pd.concat(frames, ignore_index=True)
        df["git_commit"] = commit
        df["protocol_version"] = V12_VERSION if v12 else MODEL_PROTOCOL.get(name, proto["version"])
        df["weather"] = "temperature" if uses_weather else "none"
        df.to_parquet(out_dir / f"{name}.parquet", index=False)
        print(
            f"{name}: {len(cutoffs)} origins x {len(proto['zones'])} zones x {len(regimes)} regimes"
        )


if __name__ == "__main__":
    main()
