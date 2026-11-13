"""TimesFM 2.5 with temperature, through the timesfm package's own covariate method.

    uv run --project models_ff python models_ff/timesfm25_xreg.py gate
    uv run --project models_ff python models_ff/timesfm25_xreg.py scored

A direct adapter: FoundationForecast's TimesFM 2.5 wrapper takes no covariates, because
the model has no covariate input. `forecast_with_covariates` adds one outside the model:
a linear regression of load on the covariate, with TimesFM forecasting the residual.

Settings, fixed on 2026-11-13 before any scored run and not tuned. They follow the GB
study's (notes/moran.md): mode "xreg + timesfm", temperature as the one dynamic
numerical covariate, ridge 0, CPU. Context 2,048 hours, as for every other model here.
Missing load hours in the context are filled by linear interpolation, which is what the
package's plain `forecast` does by itself. Row written: timesfm25_temperature.
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
import timesfm

ROOT = Path(__file__).resolve().parent.parent
REPO_ID = "google/timesfm-2.5-200m-pytorch"
NAME = "timesfm25_temperature"
CONTEXT_HOURS = 2048
H = 168


def git(*a: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *a], cwd=ROOT, capture_output=True, text=True)


def main() -> None:
    which = sys.argv[1] if len(sys.argv) > 1 else ""
    if which not in ("gate", "ordering_gate", "scored"):
        sys.exit(__doc__)
    dirty = "-dirty" if git("status", "--porcelain", "--untracked-files=no").stdout.strip() else ""
    commit = git("rev-parse", "--short", "HEAD").stdout.strip() + dirty
    if which == "scored":
        if git("diff", "--quiet", "protocol-v1", "--", "protocol.yaml").returncode != 0:
            sys.exit("protocol.yaml differs from the protocol-v1 tag; refusing to score")
        if dirty:
            sys.exit("commit the code before a scored run")
    pin = json.loads((ROOT / "models" / "pins.json").read_text())[REPO_ID]
    folder = "models--" + REPO_ID.replace("/", "--")
    snapshot = ROOT / "models_cache" / folder / "snapshots" / pin["revision"]
    assert snapshot.is_dir(), f"pinned snapshot missing: {snapshot}"
    model = timesfm.TimesFM_2p5_200M_torch.from_pretrained(str(snapshot))
    model.compile(
        timesfm.ForecastConfig(
            max_context=CONTEXT_HOURS,
            max_horizon=H,
            normalize_inputs=True,
            use_continuous_quantile_head=True,
            fix_quantile_crossing=True,
            return_backcast=True,  # required by forecast_with_covariates
        )
    )

    inputs = pd.read_parquet(ROOT / "data" / "model_inputs" / f"{which}.parquet")
    parts = []
    cutoffs = sorted(inputs["cutoff"].unique())
    for i, cutoff in enumerate(cutoffs):
        at = inputs[inputs["cutoff"] == cutoff]
        for regime, win in at.groupby("regime"):
            zones = sorted(win["unique_id"].unique())
            contexts, temps, futures = [], [], []
            for zone in zones:
                z = win[win["unique_id"] == zone].sort_values("ds")
                hist = z[~z["is_horizon"]].tail(CONTEXT_HOURS)
                fut = z[z["is_horizon"]]
                assert len(hist) == CONTEXT_HOURS and len(fut) == H
                y = hist["y"].interpolate(limit_direction="both").to_numpy(dtype=np.float32)
                contexts.append(y)
                temps.append(np.concatenate([hist["T"].to_numpy(), fut["T"].to_numpy()]))
                futures.append(fut)
            t0 = time.perf_counter()
            point, _ = model.forecast_with_covariates(
                inputs=contexts,
                dynamic_numerical_covariates={"T": temps},
                xreg_mode="xreg + timesfm",
                ridge=0.0,
                force_on_cpu=True,
            )
            runtime = (time.perf_counter() - t0) / len(zones)
            for fut, p in zip(futures, point, strict=True):
                p = np.asarray(p, dtype=float).reshape(-1)
                assert p.shape == (H,) and np.isfinite(p).all(), "bad forecast shape or values"
                parts.append(
                    fut[["unique_id", "ds"]].assign(
                        y_hat=p, regime=regime, cutoff=cutoff, runtime_s=runtime
                    )
                )
        if (i + 1) % 10 == 0 or i + 1 == len(cutoffs):
            print(f"{i + 1}/{len(cutoffs)} cutoffs", flush=True)

    df = pd.concat(parts, ignore_index=True)
    df["model"] = NAME
    df["weather"] = "temperature"
    df["git_commit"] = commit
    df["protocol_version"] = "protocol-v1"
    df["weights_revision"] = pin["revision"]
    df["weights_date"] = pin["weights_date"]
    df["context_hours"] = CONTEXT_HOURS
    df["library"] = f"timecopilot-timesfm {version('timecopilot-timesfm')}"
    base = ROOT / "results" if which == "scored" else ROOT / "results" / which
    (base / "forecasts").mkdir(parents=True, exist_ok=True)
    df.to_parquet(base / "forecasts" / f"{NAME}.parquet", index=False)
    print(NAME, len(df), "rows, mean runtime per series", round(df["runtime_s"].mean(), 2), "s")


if __name__ == "__main__":
    main()
