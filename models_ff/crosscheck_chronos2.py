"""Cross-check: Chronos-2 through FoundationForecast against the direct adapter.

    uv run --project models_ff python models_ff/crosscheck_chronos2.py gate

Gate origins only. This is not a leaderboard row (FRIDAY.md, stretch row 2); it tests
whether the library reproduces `models/chronos2.py` on identical inputs. Same settings
as the direct adapter: 2,048 hours of context, temperature as past and known-future
covariate, both zones per call, median point forecast, CPU, the pinned weights snapshot.
Writes results/<set>/crosscheck/chronos2_ff.parquet with both forecasts side by side.
"""

from __future__ import annotations

import json
import sys
import time
from importlib.metadata import version
from pathlib import Path

import pandas as pd
from foundationforecast import FoundationForecast
from foundationforecast.models import Chronos

ROOT = Path(__file__).resolve().parent.parent
REPO_ID = "amazon/chronos-2"
CONTEXT_HOURS = 2048
ALIAS = "Chronos-2"


def main() -> None:
    which = sys.argv[1] if len(sys.argv) > 1 else ""
    if which not in ("gate", "ordering_gate"):  # never the scored origins
        sys.exit(__doc__)
    pin = json.loads((ROOT / "models" / "pins.json").read_text())[REPO_ID]
    snapshot = ROOT / "models_cache" / "models--amazon--chronos-2" / "snapshots" / pin["revision"]
    assert snapshot.is_dir(), f"pinned snapshot missing: {snapshot}"
    ff = FoundationForecast(models=[Chronos(repo_id=str(snapshot), alias=ALIAS)])

    inputs = pd.read_parquet(ROOT / "data" / "model_inputs" / f"{which}.parquet")
    inputs["ds_utc"] = inputs["ds"]
    inputs["ds"] = inputs["ds"].dt.tz_localize(None)  # UTC wall time for the library

    def predict(win: pd.DataFrame, use_temperature: bool) -> tuple[pd.DataFrame, float]:
        hist = win[~win["is_horizon"]].groupby("unique_id").tail(CONTEXT_HOURS)
        fut = win[win["is_horizon"]]
        t0 = time.perf_counter()
        if use_temperature:
            fc = ff.forecast(
                df=hist[["unique_id", "ds", "y", "T"]],
                h=168,
                freq="h",
                X_df=fut[["unique_id", "ds", "T"]],
            )
        else:
            fc = ff.forecast(df=hist[["unique_id", "ds", "y"]], h=168, freq="h")
        runtime = (time.perf_counter() - t0) / win["unique_id"].nunique()
        out = fut[["unique_id", "ds", "ds_utc"]].merge(fc, on=["unique_id", "ds"])
        assert len(out) == len(fut), "forecast timestamps do not match the horizon"
        return out.rename(columns={ALIAS: "y_hat_ff"}), runtime

    parts = []
    for cutoff in sorted(inputs["cutoff"].unique()):
        at = inputs[inputs["cutoff"] == cutoff]
        for regime, win in at.groupby("regime"):
            out, rt = predict(win, use_temperature=True)
            parts.append(
                out.assign(model="chronos2_temperature", regime=regime, cutoff=cutoff, runtime_s=rt)
            )
        out, rt = predict(at[at["regime"] == "oracle"], use_temperature=False)
        for regime in sorted(at["regime"].unique()):
            parts.append(out.assign(model="chronos2", regime=regime, cutoff=cutoff, runtime_s=rt))
        print(pd.Timestamp(cutoff).date(), flush=True)

    ffdf = pd.concat(parts, ignore_index=True).drop(columns="ds").rename(columns={"ds_utc": "ds"})
    keys = ["model", "unique_id", "regime", "cutoff", "ds"]
    direct = pd.concat(
        pd.read_parquet(ROOT / "results" / which / "forecasts" / f"{m}.parquet")
        for m in ("chronos2_temperature", "chronos2")
    )[keys + ["y_hat"]].rename(columns={"y_hat": "y_hat_direct"})
    both = ffdf[keys + ["y_hat_ff", "runtime_s"]].merge(direct, on=keys, validate="one_to_one")
    assert len(both) == len(ffdf) == len(direct), "the two adapters cover different rows"
    both["foundationforecast_version"] = version("foundationforecast")
    both["weights_revision"] = pin["revision"]
    dest = ROOT / "results" / which / "crosscheck"
    dest.mkdir(parents=True, exist_ok=True)
    both.to_parquet(dest / "chronos2_ff.parquet", index=False)

    both["abs_diff"] = (both["y_hat_ff"] - both["y_hat_direct"]).abs()
    both["rel_diff"] = both["abs_diff"] / both["y_hat_direct"].abs()
    summary = both.groupby(["model", "unique_id", "regime"]).agg(
        hours=("abs_diff", "size"),
        max_abs_mw=("abs_diff", "max"),
        mean_abs_mw=("abs_diff", "mean"),
        max_rel=("rel_diff", "max"),
        runtime_s=("runtime_s", "mean"),
    )
    print(summary.to_string(float_format=lambda v: f"{v:.6g}"))


if __name__ == "__main__":
    main()
