"""Collect what the dashboard page shows into dashboard/data.js.

    uv run --project core python dashboard/build_data.py

Reads results/ and data/processed/ only; computes nothing new except display rounding.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from harness.data import Data, load_protocol  # noqa: E402

LABELS = {
    "seasonal_naive": ("Same hour last week", "simple", ""),
    "lag_regression": ("Regression, no weather", "simple", ""),
    "lag_regression_temperature": ("Regression + temperature", "baseline", "the baseline"),
    "lightgbm_temperature": ("LightGBM + temperature", "simple", ""),
    "vanilla_benchmark": ("Vanilla benchmark", "simple", ""),
    "vanilla_benchmark_trend": ("Vanilla benchmark with trend", "standard", "field standard"),
    "chronos2": ("Chronos-2, no weather", "fm", ""),
    "chronos2_temperature": ("Chronos-2 + temperature", "primary", "primary comparison"),
    "chronos2_temperature_gap48": ("Chronos-2 + temperature, 2-day data delay", "fm", ""),
    "timesfm25": ("TimesFM 2.5, no weather", "fm", "univariate"),
    "timesfm25_temperature": ("TimesFM 2.5 + temperature", "fm", ""),
    "timestral_temperature": ("Timestral + temperature", "flagged", "not out-of-sample"),
}


def main() -> None:
    proto = load_protocol()
    res = ROOT / "results"
    lb = pd.read_parquet(res / "leaderboard.parquet")
    st = pd.read_parquet(res / "stats.parquet")
    win = pd.read_parquet(res / "windows.parquet")
    base = proto["baseline_model"]

    vs = st[(st["kind"] == "vs_baseline") & (st["metric"] == "mae")].set_index(
        ["model_a", "unique_id", "regime"]
    )
    board = []
    for r in lb.itertuples():
        label, group, note = LABELS[r.model]
        key = (r.model, r.unique_id, r.regime)
        board.append(
            {
                "model": r.model,
                "label": label,
                "group": group,
                "note": note,
                "zone": r.unique_id,
                "regime": r.regime,
                "mae": round(r.mae, 1),
                "mape": round(r.mape, 2),
                "ratio": round(r.ratio_vs_baseline, 3),
                "lo": round(vs.loc[key, "ci90_low"], 3) if key in vs.index else None,
                "hi": round(vs.loc[key, "ci90_high"], 3) if key in vs.index else None,
                "n": int(r.n_windows),
                "n_after": None
                if pd.isna(r.n_windows_after_weights)
                else int(r.n_windows_after_weights),
                "weights_date": None if pd.isna(r.weights_date) else str(r.weights_date)[:10],
                "protocol": r.protocol_version,
            }
        )

    days = st[
        (st["kind"] == "vs_baseline")
        & (st["model_a"] == "chronos2_temperature")
        & (st["regime"] == "forecast")
        & (st["metric"] != "mae")
    ]
    per_day = {
        z: [
            {
                "day": int(r.metric[-1]),
                "ratio": round(r.ratio, 3),
                "lo": round(r.ci90_low, 3),
                "hi": round(r.ci90_high, 3),
            }
            for r in g.sort_values("metric").itertuples()
        ]
        for z, g in days.groupby("unique_id")
    }

    data = Data()
    fc = {
        m: pd.read_parquet(res / "forecasts" / f"{m}.parquet")
        for m in (base, "chronos2_temperature")
    }
    kept = sorted(win["cutoff"].unique())
    weeks = []
    for cutoff in kept[::4]:
        entry = {"start": str(pd.Timestamp(cutoff).tz_convert(proto["timezone"]).date())}
        for zone in proto["zones"]:
            entry[zone] = {"actual": [round(v) for v in data.actuals(zone, cutoff)]}
            for m, df in fc.items():
                g = df[
                    (df["unique_id"] == zone)
                    & (df["cutoff"] == cutoff)
                    & (df["regime"] == "forecast")
                ].sort_values("ds")
                entry[zone][m] = [round(v) for v in g["y_hat"]]
        weeks.append(entry)

    zones = {}
    last = pd.Timestamp(max(kept)) + pd.Timedelta(hours=168)
    for zone in proto["zones"]:
        y = data.y[zone].loc[last - pd.Timedelta(days=365) : last]
        zones[zone] = {
            "mean_mw": round(float(y.mean())),
            "peak_mw": round(float(y.max())),
            "stations": proto["weather"]["stations"][zone],
        }

    # Zones chosen for protocol-v2 (decision 33): display only, nothing has been run on them.
    draft = yaml.safe_load((ROOT / "protocol-v2-draft.yaml").read_text())
    zstats = pd.read_csv(ROOT / "results" / "zone_selection" / "zone_stats.csv", index_col=0)
    next_zones = {
        z: {
            "name": v["name"],
            "matches": v["matches"],
            "mean_mw": round(float(zstats.loc[z, "mean_y2"])),  # Nov 2024 to Oct 2025
            "peak_mw": round(
                float(max(zstats.loc[z, "peak_summer"], zstats.loc[z, "peak_winter"]))
            ),
            "summer_winter_peak": round(float(zstats.loc[z, "sw_peak_ratio"]), 2),
            "stations": v["weather_points"],
        }
        for z, v in draft["zones"]["selected"].items()
    }

    # What the scan found: the latest candidates file per provider, and every hit with
    # the reason it was kept or dropped (paraphrased notes only).
    scan = {}
    for prov_dir in sorted((ROOT / "candidates").iterdir()):
        files = sorted(prov_dir.glob("scan_*.jsonl"))
        if not files:
            continue
        latest = files[-1]
        stem = latest.stem.replace("scan_", "scan-").replace("_run", "-run")
        ledger = ROOT / "evidence" / prov_dir.name / f"{stem}.jsonl"
        hits = [json.loads(x) for x in ledger.read_text().splitlines()] if ledger.exists() else []
        scan[prov_dir.name] = {
            "file": str(latest.relative_to(ROOT)),
            "candidates": [json.loads(x) for x in latest.read_text().splitlines()],
            "hits": [
                {
                    "url": h["url"],
                    "title": h["title"],
                    "published_at": h["published_at"],
                    "status": h["note"].split(".")[0].split(":")[0].split(" ")[0].upper(),
                    "note": h["note"],
                }
                for h in hits
            ],
        }
    feeds_files = sorted((ROOT / "candidates" / "feeds").glob("feeds_*.jsonl"))
    feed_counts = {}
    if feeds_files:
        for x in feeds_files[-1].read_text().splitlines():
            src = json.loads(x)["source"]
            feed_counts[src] = feed_counts.get(src, 0) + 1
    spec = yaml.safe_load((ROOT / "spec.yaml").read_text())

    out = {
        "scan": scan,
        "feed_counts": feed_counts,
        "scan_window_days": spec["scan"]["window_days"],
        "built_from_commit": lb["git_commit"].dropna().unique().tolist(),
        "protocol": sorted(lb["protocol_version"].dropna().unique().tolist()),
        "bar": proto["primary_comparison"]["bar"],
        "n_windows": int(lb["n_windows"].max()),
        "first_week": str(pd.Timestamp(min(kept)).tz_convert(proto["timezone"]).date()),
        "last_week": str(pd.Timestamp(max(kept)).tz_convert(proto["timezone"]).date()),
        "board": board,
        "per_day": per_day,
        "weeks": weeks,
        "zones": zones,
        "next_zones": next_zones,
        "primary_text": (res / "primary.md").read_text(),
        # Chronos-2 with temperature against the field's standard benchmark (protocol-v1.1)
        "vs_standard": {
            r.unique_id: {
                "ratio": round(r.ratio, 3),
                "lo": round(r.ci90_low, 3),
                "hi": round(r.ci90_high, 3),
            }
            for r in st[
                (st["kind"] == "vs_vanilla_trend")
                & (st["model_a"] == "chronos2_temperature")
                & (st["regime"] == "forecast")
                & (st["metric"] == "mae")
            ].itertuples()
        },
        # GB study, weather_study/RESULTS.md in Zenodo record 24161799 (notes/moran.md)
        "claim": {
            "ratio": 0.966,
            "lo": 0.931,
            "hi": 1.001,
            "level": 0.90,
            "n_days": 960,
            "horizon": "day-ahead",
            "url": "https://zenodo.org/records/24161799",
        },
    }
    out["weather_v12"] = weather_v12(res / "weather_v12")
    out["protocol"] = sorted(set(out["protocol"]) | set(out["weather_v12"]["protocol"]))
    (ROOT / "dashboard" / "data.js").write_text("window.DATA = " + json.dumps(out) + ";\n")
    print("data.js:", len(board), "leaderboard rows,", len(weeks), "sample weeks")


def weather_v12(d: Path) -> dict:
    """protocol-v1.2 (secondary): three models under four weather sources, ERA5 truth."""
    lb = pd.read_csv(d / "leaderboard.csv")
    st = pd.read_csv(d / "stats.csv")
    te = pd.read_csv(d / "temperature_error_by_lead.csv")
    rows = [
        {
            "model": r.model,
            "zone": r.unique_id,
            "regime": r.regime,
            "n": int(r.n_windows),
            "mae": round(r.mae, 1),
            "protocol": r.protocol_version,
        }
        for r in lb.itertuples()
    ]
    pairs = [
        {
            "kind": r.kind,
            "zone": r.unique_id,
            "regime": r.regime,
            "n": int(r.n_windows),
            "ratio": round(r.ratio, 3),
            "lo": round(r.ci90_low, 3),
            "hi": round(r.ci90_high, 3),
            "reading": r.reading_10pct_bar,
        }
        for r in st[
            st["kind"].isin(
                [
                    "chronos2_vs_vanilla_benchmark_trend",
                    "chronos2_vs_lag_regression_temperature",
                ]
            )
            & (st["metric"] == "mae")
        ].itertuples()
    ]
    temp = [
        {
            "zone": r.unique_id,
            "source": r.source.split(" ")[0] if r.source.startswith("forecast_") else "v1_oracle",
            "day": int(r.day),
            "n": int(r.n),
            "rmse": round(r.rmse, 2),
        }
        for r in te.itertuples()
    ]
    return {
        "protocol": sorted(lb["protocol_version"].dropna().unique().tolist()),
        "rows": rows,
        "pairs": pairs,
        "temp_rmse": temp,
    }


if __name__ == "__main__":
    main()
