"""Score the protocol-v1.2 weather regimes (protocol-v1.2.yaml). All rows are secondary.

    uv run --project core python -m harness.score_weather gate
    uv run --project core python -m harness.score_weather scored   # only after tag protocol-v1.2

Reads results/<set>/weather_v12/forecasts/ (scored set: results/weather_v12/forecasts/)
and writes next to it: windows.parquet, leaderboard.csv, dropped_windows.csv,
stats.csv (the registered comparisons) and temperature_error_by_lead.csv.

Drop rule, scoped per regime: a window incomplete for any forecaster is dropped for every
forecaster in that zone AND THAT REGIME only. The v1 and v1.1 rows live in other files
and are scored by harness.score, so nothing here can change their n_windows.

Registered comparisons (protocol-v1.2.yaml, fixed before scoring), per zone, ratio of
mean window MAE with the protocol's paired whole-week bootstrap:
  - within each regime: Chronos-2 with temperature vs the lag regression with
    temperature, and vs Vanilla with trend
  - each model's forecast-regime MAE / its oracle_era5 MAE, on the weeks both regimes keep
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fetch import verify_manifest  # noqa: E402

from harness.data import ROOT, V12_REGIMES, Data, horizon_index, load_protocol, origins  # noqa: E402
from harness.run import V12_DIR, require_frozen_v12  # noqa: E402
from harness.score import leaderboard, window_metrics  # noqa: E402
from harness.stats import DAY_COLS, ratio_ci, verdict  # noqa: E402

BASELINE = "lag_regression_temperature"
CHRONOS = "chronos2_temperature"
COMPARATORS = ["lag_regression_temperature", "vanilla_benchmark_trend"]
V12_MODELS = [CHRONOS, *COMPARATORS]
ORACLE = "oracle_era5"
FORECAST_REGIMES = [r for r in V12_REGIMES if r != ORACLE]


def _lead_matched(table: pd.DataFrame, hz: pd.DatetimeIndex) -> np.ndarray:
    lead = np.arange(len(hz)) // 24
    return table.reindex(index=hz, columns=range(1, 8)).to_numpy()[np.arange(len(hz)), lead]


def temperature_error_by_lead(data: Data, proto: dict, cutoffs: list[pd.Timestamp]) -> pd.DataFrame:
    """Horizon temperature minus ERA5, per source and horizon day, over the given windows.
    The v1 `oracle` series (ECMWF IFS 9 km analysis) is shown for scale."""
    data._load_v12()
    rows = []
    for zone in proto["zones"]:
        for c in cutoffs:
            hz = horizon_index(c)
            truth = data.era5[zone].reindex(hz).to_numpy()
            src = {
                "forecast_gfs (HRRR d1, GFS d2-7)": _lead_matched(data.forecast[zone], hz),
                "forecast_ifs (ecmwf_ifs025)": _lead_matched(
                    data.forecast_v12["forecast_ifs"][zone], hz
                ),
                "forecast_aifs (ecmwf_aifs025_single)": _lead_matched(
                    data.forecast_v12["forecast_aifs"][zone], hz
                ),
                "v1 oracle (IFS 9 km analysis)": data.oracle[zone].reindex(hz).to_numpy(),
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
    return (
        df.groupby(["unique_id", "source", "day"])["err"]
        .agg(
            n="size",
            mae=lambda e: e.abs().mean(),
            rmse=lambda e: np.sqrt((e**2).mean()),
            bias="mean",
        )
        .reset_index()
    )


def registered_comparisons(win: pd.DataFrame, proto: dict) -> pd.DataFrame:
    draws, seed = proto["bootstrap"]["draws"], proto["bootstrap"]["seed"]
    bar = proto["primary_comparison"]["bar"]
    wide = win.set_index(["unique_id", "regime", "model", "cutoff"]).sort_index()
    have = set(win["model"])
    rows = []

    def compare(kind, zone, a_model, a_regime, b_model, b_regime, label_regime):
        if not {a_model, b_model} <= have:
            return
        a = wide.loc[(zone, a_regime, a_model)]
        b = wide.loc[(zone, b_regime, b_model)]
        weeks = a.index.intersection(b.index)  # paired: the weeks both arms keep
        a, b = a.loc[weeks], b.loc[weeks]
        for col in ["mae", *DAY_COLS]:
            r, lo, hi = ratio_ci(a[col].to_numpy(), b[col].to_numpy(), draws, seed)
            rows.append(
                {
                    "kind": kind,
                    "unique_id": zone,
                    "regime": label_regime,
                    "model_a": a_model,
                    "model_b": b_model,
                    "metric": col,
                    "n_windows": len(weeks),
                    "ratio": r,
                    "ci90_low": lo,
                    "ci90_high": hi,
                    "reading_10pct_bar": verdict(lo, hi, bar)
                    if kind != "forecast_vs_oracle_era5"
                    else "",
                    "label": "secondary (protocol-v1.2)",
                }
            )

    for zone in proto["zones"]:
        for regime in V12_REGIMES:
            for comp in COMPARATORS:
                compare("chronos2_vs_" + comp, zone, CHRONOS, regime, comp, regime, regime)
        for m in V12_MODELS:
            for regime in FORECAST_REGIMES:
                compare("forecast_vs_oracle_era5", zone, m, regime, m, ORACLE, regime)
    return pd.DataFrame(rows)


def main() -> None:
    which = sys.argv[1] if len(sys.argv) > 1 else ""
    if which not in ("gate", "ordering_gate", "scored"):
        sys.exit(__doc__)
    verify_manifest()
    proto = load_protocol()
    if which == "scored":
        require_frozen_v12(proto)
    out = (ROOT / "results" if which == "scored" else ROOT / "results" / which) / V12_DIR
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
    lb["label"] = f"secondary (protocol-v1.2{', gate only' if which != 'scored' else ''})"
    lb.round(4).to_csv(out / "leaderboard.csv", index=False)
    show = ["model", "unique_id", "regime", "n_windows", "mae", "mape", "ratio_vs_baseline"]
    print(lb[show].round(3).to_string(index=False))
    print(f"\ndropped (zone, regime, cutoff): {len(drop)}")
    for z, r, c in sorted(drop):
        print(f"  {z} {r} {c}")

    stats = registered_comparisons(win, proto)
    if len(stats):
        stats.round(4).to_csv(out / "stats.csv", index=False)
        head = stats[stats["metric"] == "mae"].drop(columns=["metric", "label"])
        print("\n" + head.round(3).to_string(index=False))

    te = temperature_error_by_lead(data, proto, origins(proto, which))
    te.round(3).to_csv(out / "temperature_error_by_lead.csv", index=False)
    print("\ntemperature RMSE vs ERA5 by horizon day, C")
    print(te.pivot_table(index=["unique_id", "source"], columns="day", values="rmse").round(2))


if __name__ == "__main__":
    main()
