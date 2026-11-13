"""Run and score the protocol-v1.3 model rows (protocol-v1.3.yaml). All rows are secondary.

    uv run --project core python -m harness.v13 run gate      # lightgbm_competition, gate origins
    uv run --project core python -m harness.v13 run scored    # once, after tag protocol-v1.3
    uv run --project core python -m harness.v13 score gate
    uv run --project core python -m harness.v13 score scored

Rows run here: lightgbm_competition (core). tabpfn_ts_v2_temperature runs in models_ff/
(models_ff/tabpfn_ts_v2.py) and writes to the same folder; `score` picks up whatever rows
are present.

Six regimes: the v1 pair (oracle, forecast) and the four v1.2 regimes. Output goes only to
results/models_v13/ (gate set: results/gate/models_v13/). harness.score and
harness.score_weather never read that folder, so no v1, v1.1 or v1.2 file can change.

Windows: a v1.3 row is scored on exactly the (zone, regime, cutoff) windows that the
existing scoring kept (results/windows.parquet for the v1 regimes, under the v1 drop rule;
results/weather_v12/windows.parquet for the v1.2 regimes, under the per-regime rule). Those
files are read, never written. A kept window that a v1.3 row did not complete is dropped
for that row's comparisons only and listed in dropped_windows.csv.

Registered comparisons (fixed before scoring), per zone and regime, ratio of mean window
MAE with the protocol's paired whole-week bootstrap, read against the 10% bar:
  each v1.3 row vs lag_regression_temperature; each v1.3 row vs vanilla_benchmark_trend;
  chronos2_temperature vs each v1.3 row.
"""

from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

import pandas as pd
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fetch import verify_manifest  # noqa: E402

from harness.baselines import MODELS  # noqa: E402
from harness.data import ROOT, V12_REGIMES, Data, load_protocol, origins  # noqa: E402
from harness.run import REGIMES, V12_DIR, git, git_commit, require_frozen  # noqa: E402
from harness.score import leaderboard, window_metrics  # noqa: E402
from harness.stats import DAY_COLS, ratio_ci, verdict  # noqa: E402

VERSION = "protocol-v1.3"
PROTOCOL_FILE = "protocol-v1.3.yaml"
FROZEN_FILES = ["protocol.yaml", "protocol-v1.1.yaml", "protocol-v1.2.yaml", PROTOCOL_FILE]
V13_DIR = "models_v13"
V13_REGIMES = [*REGIMES, *V12_REGIMES]
CORE_ROWS = ["lightgbm_competition"]
NEW_ROWS = ["lightgbm_competition", "tabpfn_ts_v2_temperature"]
BASELINE = "lag_regression_temperature"
VANILLA = "vanilla_benchmark_trend"
CHRONOS = "chronos2_temperature"
# The v1 verdict rule with neutral names: arm A is model_a, arm B is model_b.
READING = {
    "worth_switching": "A_better_beyond_bar",
    "regression_clearly_better": "B_better_beyond_bar",
    "practical_tie": "practical_tie",
    "inconclusive": "inconclusive",
}


def out_dir(which: str) -> Path:
    return (ROOT / "results" if which == "scored" else ROOT / "results" / which) / V13_DIR


def require_frozen_v13(proto: dict, out_file: Path | None = None) -> None:
    """Scored v1.3 rows run only at the tag protocol-v1.3, from a clean tree, against
    unchanged protocol files, and only once (rules 5 and 12)."""
    require_frozen(proto)
    v13 = yaml.safe_load((ROOT / PROTOCOL_FILE).read_text())
    if v13.get("version") != VERSION or v13.get("status") != "frozen":
        sys.exit(f"{PROTOCOL_FILE} is not marked frozen: scored origins must not be run yet")
    if not git("tag", "--list", VERSION):
        sys.exit(f"git tag {VERSION} does not exist: scored origins must not be run yet")
    if subprocess.run(
        ["git", "diff", "--quiet", VERSION, "--", *FROZEN_FILES], cwd=ROOT, check=False
    ).returncode:
        sys.exit(f"a protocol file differs from tag {VERSION}")
    if out_file is not None:
        if git_commit().endswith("-dirty"):
            sys.exit("commit the code before a scored run")
        if out_file.exists():
            sys.exit(f"{out_file} exists: the scored set is run once")


def run(which: str, limit: int | None) -> None:
    proto = load_protocol()
    verify_manifest()
    out = out_dir(which) / "forecasts"
    if which == "scored":
        if limit:
            sys.exit("--limit is for the gate set; the scored set is run whole, once")
        for name in CORE_ROWS:
            require_frozen_v13(proto, out / f"{name}.parquet")
    cutoffs = origins(proto, which)[:limit]
    data = Data()
    commit = git_commit()
    out.mkdir(parents=True, exist_ok=True)
    for name in CORE_ROWS:
        fn, _ = MODELS[name]
        frames = []
        for regime in V13_REGIMES:
            for zone in proto["zones"]:
                for cutoff in cutoffs:
                    hist = data.history(zone, cutoff)
                    temp = data.temperature(zone, cutoff, regime)
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
            print(f"{name} {regime} done", flush=True)
        df = pd.concat(frames, ignore_index=True)
        df["git_commit"] = commit
        df["protocol_version"] = VERSION
        df["weather"] = "temperature"
        df.to_parquet(out / f"{name}.parquet", index=False)
        print(f"{name}: {len(cutoffs)} origins x {len(proto['zones'])} zones x 6 regimes")


def reference_windows(which: str) -> pd.DataFrame:
    """The windows the existing scoring kept, for the three comparator rows (read only)."""
    base = ROOT / "results" if which == "scored" else ROOT / "results" / which
    v1 = pd.read_parquet(base / "windows.parquet")
    v12 = pd.read_parquet(base / V12_DIR / "windows.parquet")
    ref = pd.concat([v1[v1["regime"].isin(REGIMES)], v12[v12["regime"].isin(V12_REGIMES)]])
    return ref[ref["model"].isin([BASELINE, VANILLA, CHRONOS])]


def registered_comparisons(win: pd.DataFrame, proto: dict, rows: list[str]) -> pd.DataFrame:
    draws, seed = proto["bootstrap"]["draws"], proto["bootstrap"]["seed"]
    bar = proto["primary_comparison"]["bar"]
    wide = win.set_index(["unique_id", "regime", "model", "cutoff"]).sort_index()
    out = []
    for zone in proto["zones"]:
        for regime in V13_REGIMES:
            pairs = []
            for new in rows:
                pairs += [(new, BASELINE), (new, VANILLA), (CHRONOS, new)]
            for a_model, b_model in pairs:
                try:
                    a = wide.loc[(zone, regime, a_model)]
                    b = wide.loc[(zone, regime, b_model)]
                except KeyError:
                    continue
                weeks = a.index.intersection(b.index)  # paired: the weeks both arms keep
                if not len(weeks):
                    continue
                a, b = a.loc[weeks], b.loc[weeks]
                for col in ["mae", *DAY_COLS]:
                    r, lo, hi = ratio_ci(a[col].to_numpy(), b[col].to_numpy(), draws, seed)
                    out.append(
                        {
                            "unique_id": zone,
                            "regime": regime,
                            "model_a": a_model,
                            "model_b": b_model,
                            "metric": col,
                            "n_windows": len(weeks),
                            "ratio": r,
                            "ci90_low": lo,
                            "ci90_high": hi,
                            "reading_10pct_bar": READING[verdict(lo, hi, bar)],
                            "label": f"secondary ({VERSION})",
                        }
                    )
    return pd.DataFrame(out)


def score(which: str) -> None:
    verify_manifest()
    proto = load_protocol()
    if which == "scored":
        require_frozen_v13(proto)
    out = out_dir(which)
    fc = pd.concat(pd.read_parquet(p) for p in sorted((out / "forecasts").glob("*.parquet")))
    assert set(fc["model"]) <= set(NEW_ROWS), "only v1.3 rows are scored here"
    for col in ("weights_revision", "weights_date"):
        if col not in fc:
            fc[col] = None
    new = window_metrics(fc, Data())
    ref = reference_windows(which)
    kept = set(zip(ref["unique_id"], ref["regime"], ref["cutoff"], strict=True))
    keys = list(zip(new["unique_id"], new["regime"], new["cutoff"], strict=True))
    in_kept = pd.Series([k in kept for k in keys], index=new.index)
    bad = new[in_kept & ~new["complete"]]
    bad[["unique_id", "regime", "cutoff", "model"]].to_csv(out / "dropped_windows.csv", index=False)
    new = new[in_kept & new["complete"]].drop(columns="complete")
    new.to_parquet(out / "windows.parquet", index=False)

    rows = sorted(set(new["model"]), key=NEW_ROWS.index)
    regimes = set(new["regime"])
    both = pd.concat([new, ref[ref["regime"].isin(regimes)]], ignore_index=True)
    lb = leaderboard(both, BASELINE).sort_values(["unique_id", "regime", "mae"])
    lb["label"] = f"secondary ({VERSION}{', gate only' if which != 'scored' else ''})"
    lb.round(4).to_csv(out / "leaderboard.csv", index=False)
    show = ["model", "unique_id", "regime", "n_windows", "mae", "ratio_vs_baseline", "runtime_s"]
    print(lb[show].round(3).to_string(index=False))
    print(f"\nkept windows not completed by a v1.3 row: {len(bad)}")

    stats = registered_comparisons(both, proto, rows)
    stats.round(4).to_csv(out / "stats.csv", index=False)
    head = stats[stats["metric"] == "mae"].drop(columns=["metric", "label"])
    print("\n" + head.round(3).to_string(index=False))


def main() -> None:
    args = sys.argv[1:]
    if len(args) < 2 or args[0] not in ("run", "score") or args[1] not in ("gate", "scored"):
        sys.exit(__doc__)
    limit = int(args[args.index("--limit") + 1]) if "--limit" in args else None
    run(args[1], limit) if args[0] == "run" else score(args[1])


if __name__ == "__main__":
    main()
