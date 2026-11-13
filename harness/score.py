"""Score every forecast file and write the leaderboard. The scored set lives in
results/, the gate set in results/gate/.

    uv run --project core python -m harness.score gate
    uv run --project core python -m harness.score scored

Outputs: windows.parquet (one row per model, zone, regime, cutoff),
leaderboard.parquet and leaderboard.csv, dropped_windows.csv.

A window that cannot be built for one forecaster is dropped for every forecaster in
that zone, in both regimes, and listed.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fetch import verify_manifest  # noqa: E402

from harness.data import ROOT, Data, load_protocol  # noqa: E402

LAG = pd.Timedelta(hours=168)


def mase_scale(y: pd.Series, cutoff: pd.Timestamp, days: int = 365) -> float:
    """In-sample seasonal-naive-168 MAE over the trailing `days` before the cutoff."""
    window = y.loc[cutoff - pd.Timedelta(days=days) + pd.Timedelta(hours=1) : cutoff]
    lagged = y.reindex(window.index - LAG).to_numpy()
    return float(np.nanmean(np.abs(window.to_numpy() - lagged)))


def window_metrics(fc: pd.DataFrame, data: Data) -> pd.DataFrame:
    rows = []
    for (model, zone, regime, cutoff), g in fc.groupby(["model", "unique_id", "regime", "cutoff"]):
        g = g.sort_values("ds")
        y = data.actuals(zone, cutoff).to_numpy()
        e = g["y_hat"].to_numpy() - y
        complete = bool(np.isfinite(e).all()) and len(e) == 168
        row = {
            "model": model,
            "unique_id": zone,
            "regime": regime,
            "cutoff": cutoff,
            "complete": complete,
            "weather": g["weather"].iloc[0],
            "runtime_s": g["runtime_s"].iloc[0],
            "git_commit": g["git_commit"].iloc[0],
            "protocol_version": g["protocol_version"].iloc[0],
            # Foundation models only (rule 13); empty for the baselines.
            "weights_revision": g["weights_revision"].iloc[0],
            "weights_date": g["weights_date"].iloc[0],
        }
        if complete:
            ae = np.abs(e)
            row |= {
                "mae": ae.mean(),
                "rmse": np.sqrt((e**2).mean()),
                "mape": (ae / np.abs(y)).mean() * 100,
                "mase": ae.mean() / mase_scale(data.y[zone], cutoff),
            }
            row |= {f"mae_day{k + 1}": ae[24 * k : 24 * (k + 1)].mean() for k in range(7)}
        rows.append(row)
    return pd.DataFrame(rows)


def leaderboard(win: pd.DataFrame, baseline: str) -> pd.DataFrame:
    day_cols = [f"mae_day{k}" for k in range(1, 8)]
    win = win.assign(after_weights=win["cutoff"] > pd.to_datetime(win["weights_date"], utc=True))
    agg = (
        win.groupby(["model", "unique_id", "regime"])
        .agg(
            n_windows=("mae", "size"),
            weather=("weather", "first"),
            mape=("mape", "mean"),
            mae=("mae", "mean"),
            rmse=("rmse", "mean"),
            mase=("mase", "mean"),
            **{c: (c, "mean") for c in day_cols},
            runtime_s=("runtime_s", "mean"),
            git_commit=("git_commit", "first"),
            protocol_version=("protocol_version", "first"),
            weights_revision=("weights_revision", "first"),
            weights_date=("weights_date", "first"),
            n_windows_after_weights=("after_weights", "sum"),
        )
        .reset_index()
    )
    agg.loc[agg["weights_date"].isna(), "n_windows_after_weights"] = np.nan
    base = agg[agg["model"] == baseline].set_index(["unique_id", "regime"])
    key = pd.MultiIndex.from_frame(agg[["unique_id", "regime"]])
    agg["ratio_vs_baseline"] = agg["mae"].to_numpy() / base["mae"].reindex(key).to_numpy()
    for c in day_cols:
        agg[c.replace("mae", "ratio")] = agg[c].to_numpy() / base[c].reindex(key).to_numpy()
    return agg


def main() -> None:
    which = sys.argv[1] if len(sys.argv) > 1 else ""
    if which not in ("gate", "ordering_gate", "scored"):
        sys.exit(__doc__)
    verify_manifest()
    proto = load_protocol()
    out = ROOT / "results" if which == "scored" else ROOT / "results" / which
    fc = pd.concat(pd.read_parquet(p) for p in sorted((out / "forecasts").glob("*.parquet")))
    for col in ("weights_revision", "weights_date"):
        if col not in fc:
            fc[col] = None
    win = window_metrics(fc, Data())

    bad = win.loc[~win["complete"], ["unique_id", "cutoff", "model", "regime"]]
    bad.to_csv(out / "dropped_windows.csv", index=False)
    drop = set(map(tuple, bad[["unique_id", "cutoff"]].drop_duplicates().to_numpy()))
    keep = [(z, c) not in drop for z, c in zip(win["unique_id"], win["cutoff"], strict=True)]
    win = win[keep].drop(columns="complete")
    win.to_parquet(out / "windows.parquet", index=False)

    lb = leaderboard(win, proto["baseline_model"])
    order = {m: i for i, m in enumerate(proto["leaderboard_order"])}
    lb["_o"] = lb["model"].map(order).fillna(len(order))
    lb = lb.sort_values(["unique_id", "regime", "_o"]).drop(columns="_o")
    lb.to_parquet(out / "leaderboard.parquet", index=False)
    lb.round(4).to_csv(out / "leaderboard.csv", index=False)

    show = ["model", "unique_id", "regime", "n_windows", "mae", "mape", "mase", "ratio_vs_baseline"]
    print(lb[show].round(3).to_string(index=False))
    print(f"\ndropped (zone, cutoff) pairs: {len(drop)}")


if __name__ == "__main__":
    main()
