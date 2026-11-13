"""Foundation models through FoundationForecast, one leaderboard row per model.

    uv run --project models_ff python models_ff/run_ff.py timesfm25 gate
    uv run --project models_ff python models_ff/run_ff.py timesfm25 scored

Reads only data/model_inputs/<set>.parquet, which the harness writes. The harness owns
the cutoffs: this script loops over the cutoffs in that file and calls the model once
per cutoff with both zones. Weights come from the pinned snapshot in models_cache/
(models/pins.json); the library is never given a bare repo id.

Settings are fixed in SPECS before any scored run and are not tuned. All models here
get 2,048 hours of context, the same as the direct Chronos-2 adapter.
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
from importlib.metadata import version
from pathlib import Path

import numpy as np
import pandas as pd
from foundationforecast import FoundationForecast
from foundationforecast.models import TimesFM, Timestral

ROOT = Path(__file__).resolve().parent.parent
CONTEXT_HOURS = 2048
QUANTILES = [0.1, 0.9]

# name -> repo id, constructor, whether it takes temperature as a known-future covariate
SPECS = {
    # The library's TimesFM 2.5 wrapper has no covariate path, so the row is univariate.
    "timesfm25": {
        "repo_id": "google/timesfm-2.5-200m-pytorch",
        "build": lambda path: TimesFM(repo_id=path, context_length=CONTEXT_HOURS, alias="m"),
        "temperature": False,
    },
    # Library defaults: symmetric averaging and clipping at zero.
    "timestral_temperature": {
        "repo_id": "mistralai/Timestral-209M",
        "build": lambda path: Timestral(repo_id=path, context_length=CONTEXT_HOURS, alias="m"),
        "temperature": True,
    },
}


def git(*a: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *a], cwd=ROOT, capture_output=True, text=True)


def git_commit() -> str:
    dirty = "-dirty" if git("status", "--porcelain", "--untracked-files=no").stdout.strip() else ""
    return git("rev-parse", "--short", "HEAD").stdout.strip() + dirty


def main() -> None:
    name, which = (sys.argv + ["", ""])[1:3]
    if name not in SPECS or which not in ("gate", "ordering_gate", "scored"):
        sys.exit(__doc__)
    commit = git_commit()
    if which == "scored":
        if git("diff", "--quiet", "protocol-v1", "--", "protocol.yaml").returncode != 0:
            sys.exit("protocol.yaml differs from the protocol-v1 tag; refusing to score")
        if commit.endswith("-dirty"):
            sys.exit("commit the code before a scored run")
    spec = SPECS[name]
    pin = json.loads((ROOT / "models" / "pins.json").read_text())[spec["repo_id"]]
    folder = "models--" + spec["repo_id"].replace("/", "--")
    snapshot = ROOT / "models_cache" / folder / "snapshots" / pin["revision"]
    assert snapshot.is_dir(), f"pinned snapshot missing: {snapshot}"
    ff = FoundationForecast(models=[spec["build"](str(snapshot))])

    inputs = pd.read_parquet(ROOT / "data" / "model_inputs" / f"{which}.parquet")
    inputs["ds_utc"] = inputs["ds"]
    inputs["ds"] = inputs["ds"].dt.tz_localize(None)  # UTC wall time for the library

    def predict(win: pd.DataFrame) -> tuple[pd.DataFrame, float]:
        hist = win[~win["is_horizon"]].groupby("unique_id").tail(CONTEXT_HOURS)
        fut = win[win["is_horizon"]]
        t0 = time.perf_counter()
        if spec["temperature"]:
            fc = ff.forecast(
                df=hist[["unique_id", "ds", "y", "T"]],
                h=168,
                freq="h",
                quantiles=QUANTILES,
                X_df=fut[["unique_id", "ds", "T"]],
            )
        else:
            fc = ff.forecast(
                df=hist[["unique_id", "ds", "y"]], h=168, freq="h", quantiles=QUANTILES
            )
        runtime = (time.perf_counter() - t0) / win["unique_id"].nunique()
        fc = fc.rename(columns={"m": "y_hat", "m-q-10": "q10", "m-q-90": "q90"})
        out = fut[["unique_id", "ds", "ds_utc"]].merge(fc, on=["unique_id", "ds"])
        assert len(out) == len(fut), "forecast timestamps do not match the horizon"
        assert np.isfinite(out[["y_hat", "q10", "q90"]].to_numpy()).all(), "non-finite forecast"
        return out.drop(columns="ds").rename(columns={"ds_utc": "ds"}), runtime

    parts = []
    cutoffs = sorted(inputs["cutoff"].unique())
    for i, cutoff in enumerate(cutoffs):
        at = inputs[inputs["cutoff"] == cutoff]
        if spec["temperature"]:
            for regime, win in at.groupby("regime"):
                out, rt = predict(win)
                parts.append(out.assign(regime=regime, cutoff=cutoff, runtime_s=rt))
        else:  # no weather: the inputs are the same in both regimes, so predict once
            out, rt = predict(at[at["regime"] == "oracle"])
            for regime in sorted(at["regime"].unique()):
                parts.append(out.assign(regime=regime, cutoff=cutoff, runtime_s=rt))
        if (i + 1) % 10 == 0 or i + 1 == len(cutoffs):
            print(f"{i + 1}/{len(cutoffs)} cutoffs", flush=True)

    df = pd.concat(parts, ignore_index=True)
    df["model"] = name
    df["weather"] = "temperature" if spec["temperature"] else "none"
    df["git_commit"] = commit
    df["protocol_version"] = "protocol-v1"
    df["weights_revision"] = pin["revision"]
    df["weights_date"] = pin["weights_date"]
    df["context_hours"] = CONTEXT_HOURS
    df["library"] = f"foundationforecast {version('foundationforecast')}"
    keep = [
        "model",
        "unique_id",
        "regime",
        "cutoff",
        "ds",
        "y_hat",
        "q10",
        "q90",
        "runtime_s",
        "git_commit",
        "protocol_version",
        "weather",
        "weights_revision",
        "weights_date",
        "context_hours",
        "library",
    ]
    base = ROOT / "results" if which == "scored" else ROOT / "results" / which
    (base / "forecasts").mkdir(parents=True, exist_ok=True)
    df[keep].to_parquet(base / "forecasts" / f"{name}.parquet", index=False)
    print(name, len(df), "rows, mean runtime per series", round(df["runtime_s"].mean(), 2), "s")


if __name__ == "__main__":
    main()
