"""Score the draft protocol-v1.2 weather regimes (drafts/protocol-v1.2_weather.yaml).
Gate and ordering_gate sets only: these regimes are a draft and are never scored.

    uv run --project core python -m harness.score_weather gate

Reads results/<set>/weather_v12/forecasts/ and writes, in results/<set>/weather_v12/:
windows.parquet, leaderboard.csv, dropped_windows.csv and temperature_error_by_lead.csv.

Drop rule, scoped per regime: a window incomplete for any forecaster is dropped for every
forecaster in that zone AND THAT REGIME only. The v1 and v1.1 rows live in other files
and are scored by harness.score, so nothing here can change their n_windows.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fetch import verify_manifest  # noqa: E402

from harness.data import ROOT, V12_REGIMES, Data, horizon_index, load_protocol, origins  # noqa: E402
from harness.score import leaderboard, window_metrics  # noqa: E402

BASELINE = "lag_regression_temperature"


def temperature_error_by_lead(data: Data, proto: dict, cutoffs: list[pd.Timestamp]) -> pd.DataFrame:
    """Horizon temperature minus ERA5, per source and horizon day, over the given windows.
    `gfs_best_match` is the v1 forecast regime's series (HRRR day 1, GFS days 2 to 7);
    `ifs_9km_analysis` is the v1 `oracle` series, shown for scale."""
    data._load_v12()
    rows = []
    for zone in proto["zones"]:
        for c in cutoffs:
            hz = horizon_index(c)
            truth = data.era5[zone].reindex(hz).to_numpy()
            lead = np.arange(len(hz)) // 24
            src = {
                "gfs_best_match (v1 forecast)": data.forecast[zone]
                .reindex(index=hz, columns=range(1, 8))
                .to_numpy()[np.arange(len(hz)), lead],
                "ecmwf_ifs025 (forecast_ifs)": data.forecast_v12["forecast_ifs"][zone]
                .reindex(index=hz, columns=range(1, 8))
                .to_numpy()[np.arange(len(hz)), lead],
                "ecmwf_aifs025_single (forecast_aifs)": data.forecast_v12["forecast_aifs"][zone]
                .reindex(index=hz, columns=range(1, 8))
                .to_numpy()[np.arange(len(hz)), lead],
                "ifs_9km_analysis (v1 oracle)": data.oracle[zone].reindex(hz).to_numpy(),
            }
            for name, v in src.items():
                for k in range(7):
                    sl = slice(24 * k, 24 * (k + 1))
                    rows.append(
                        {"unique_id": zone, "cutoff": c, "source": name, "day": k + 1}
                        | {"err": list(v[sl] - truth[sl])}
                    )
    df = pd.DataFrame(rows).explode("err")
    df["err"] = df["err"].astype(float)
    df = df.dropna(subset=["err"])
    out = (
        df.groupby(["unique_id", "source", "day"])["err"]
        .agg(
            n="size",
            mae=lambda e: e.abs().mean(),
            rmse=lambda e: np.sqrt((e**2).mean()),
            bias="mean",
        )
        .reset_index()
    )
    return out


def main() -> None:
    which = sys.argv[1] if len(sys.argv) > 1 else ""
    if which not in ("gate", "ordering_gate"):
        sys.exit(__doc__)
    verify_manifest()
    proto = load_protocol()
    out = ROOT / "results" / which / "weather_v12"
    fc = pd.concat(pd.read_parquet(p) for p in sorted((out / "forecasts").glob("*.parquet")))
    assert set(fc["regime"]) <= set(V12_REGIMES), "v1 rows must not be scored here"
    for col in ("weights_revision", "weights_date"):
        if col not in fc:
            fc[col] = None
    data = Data()
    win = window_metrics(fc, data)

    bad = win.loc[~win["complete"], ["unique_id", "regime", "cutoff", "model"]]
    bad.to_csv(out / "dropped_windows.csv", index=False)
    drop = set(map(tuple, bad[["unique_id", "regime", "cutoff"]].drop_duplicates().to_numpy()))
    keys = zip(win["unique_id"], win["regime"], win["cutoff"], strict=True)
    win = win[[k not in drop for k in keys]].drop(columns="complete")
    win.to_parquet(out / "windows.parquet", index=False)

    lb = leaderboard(win, BASELINE).sort_values(["unique_id", "regime", "model"])
    lb["label"] = "secondary (draft protocol-v1.2, gate only)"
    lb.round(4).to_csv(out / "leaderboard.csv", index=False)
    show = ["model", "unique_id", "regime", "n_windows", "mae", "mape", "ratio_vs_baseline"]
    print(lb[show].round(3).to_string(index=False))
    print(f"\ndropped (zone, regime, cutoff): {sorted(drop)}")

    te = temperature_error_by_lead(data, proto, origins(proto, which))
    te.round(3).to_csv(out / "temperature_error_by_lead.csv", index=False)
    print("\ntemperature RMSE vs ERA5 by horizon day, C")
    print(te.pivot_table(index=["unique_id", "source"], columns="day", values="rmse").round(2))


if __name__ == "__main__":
    main()
