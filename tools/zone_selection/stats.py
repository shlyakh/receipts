"""Descriptive statistics per PJM sub-BA zone and the distance used by the protocol-v2 zone
selection rule (notes/zone_selection.md). Load only. No model is fitted or run.

    uv run --project core python tools/zone_selection/stats.py

Refuses to run if a raw file does not match results/zone_selection/raw_manifest.json.
Writes zone_stats.csv, anomaly_corr.csv and shapes.csv to results/zone_selection/."""

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parent.parent.parent
RAW = ROOT / "data" / "zone_selection_raw"  # git-ignored; hashes in results/zone_selection
OUT = ROOT / "results" / "zone_selection"
EIA = RAW
manifest = json.loads((OUT / "raw_manifest.json").read_text())
bad_files = [
    k for k, v in manifest.items() if hashlib.sha256((RAW / k).read_bytes()).hexdigest() != v
]
if bad_files:
    sys.exit(f"raw files do not match raw_manifest.json: {bad_files[:5]}")
proto = yaml.safe_load((ROOT / "protocol.yaml").read_text())
scored = proto["origins"]["scored"]
names = dict(json.loads((OUT / "pjm_zones.json").read_text()))
full = pd.date_range("2023-11-01T00", "2026-11-11T05", freq="h", tz="UTC")
FLAG, MAXFILL = 3.0, 3


def load(z):
    rows = []
    for p in sorted((EIA / z).glob("2*.json")):
        rows += json.loads(p.read_text())["data"]
    raw = pd.DataFrame(rows)
    raw["ds"] = pd.to_datetime(raw["period"], format="%Y-%m-%dT%H", utc=True)
    raw["y"] = pd.to_numeric(raw["value"], errors="coerce")
    ndup = int(raw.duplicated("ds").sum())
    s = raw.drop_duplicates("ds").set_index("ds")["y"].reindex(full)
    return s, ndup


def clean(s):
    """The v1 flag and gap rules of protocol.yaml, written afresh."""
    med = s.groupby(s.index.hour).transform(
        lambda x: x.rolling(7, center=True, min_periods=4).median()
    )
    r = s / med
    flagged = s.notna() & ((s <= 0) | (r > FLAG) | (r < 1 / FLAG))
    s2 = s.mask(flagged)
    na = s2.isna()
    rid = (na != na.shift()).cumsum()
    rl = na.groupby(rid).transform("sum")
    fill = na & (rl <= MAXFILL)
    out = s2.where(~fill, s2.interpolate(method="time", limit_area="inside"))
    return out, flagged


rows, shapes, anoms = [], {}, {}
for z in names:
    s, ndup = load(z)
    c, flagged = clean(s)
    loc = c.tz_convert("America/New_York")
    hist = slice("2023-11-10", "2025-11-09")
    sc = slice("2025-11-10", "2026-11-09")
    # windows usable under the v1 drop rule (actuals complete and 168 h lag complete)
    ok = 0
    bad = []
    for o in scored:
        t0 = pd.Timestamp(o, tz="America/New_York").tz_convert("UTC")
        h = pd.date_range(t0 + pd.Timedelta(hours=1), periods=168, freq="h")
        lag = h - pd.Timedelta(hours=168)
        if h[-1] <= c.index[-1] and c.reindex(h).notna().all() and c.reindex(lag).notna().all():
            ok += 1
        else:
            bad.append(o)
    na = c.isna()
    rid = (na != na.shift()).cumsum()
    runs = na.groupby(rid).sum()
    longruns = runs[runs > MAXFILL]
    # stuck values: runs of >= 6 identical consecutive raw values
    same = s.diff() == 0
    sid = (same != same.shift()).cumsum()
    stuck = same.groupby(sid).sum()
    stuck = int((stuck[stuck >= 5] + 1).sum())
    y1 = loc["2023-11-01":"2024-10-31"]
    y2 = loc["2024-11-01":"2025-10-31"]
    y3 = loc["2025-11-01":"2026-10-31"]
    pre = loc["2023-11-01":"2025-10-31"]  # selection period: before the first scored origin
    mon = pre.groupby(pre.index.month).mean()
    summer = pre[pre.index.month.isin([6, 7, 8])]
    winter = pre[pre.index.month.isin([12, 1, 2])]
    shoulder = mon[[4, 5, 10]].mean()
    wd = pre[pre.index.dayofweek < 5].mean()
    we = pre[pre.index.dayofweek >= 5].mean()
    d = pre.resample("D")
    dmin, dmax, dmean = d.min(), d.max(), d.mean()

    def shape(x):
        g = x.groupby(x.index.hour).mean()
        return g / g.mean()

    shs, shw = shape(summer), shape(winter)
    shapes[z] = (shs, shw)
    an = dmean / dmean.rolling(29, center=True, min_periods=15).mean() - 1
    anoms[z] = an
    # monthly growth same-month: robust to missing chunks
    rows.append(
        dict(
            zone=z,
            name=names[z].replace(" zone", ""),
            raw_missing_hist=int(s[hist].isna().sum()),
            raw_missing_scored=int(s[sc].isna().sum()),
            nonpos=int((s <= 0).sum()),
            flagged=int(flagged.sum()),
            dup=ndup,
            stuck_hours=stuck,
            long_gap_runs=len(longruns),
            long_gap_hours=int(longruns.sum()),
            missing_after_fill_pct=round(100 * c.isna().mean(), 3),
            scored_windows_ok=ok,
            dropped=",".join(bad),
            mean_y1=y1.mean(),
            mean_y2=y2.mean(),
            mean_y3=y3.mean(),
            growth_y2=y2.mean() / y1.mean() - 1,
            growth_y3=y3.mean() / y2.mean() - 1,
            # growth in the low-weather months (Apr, May, Oct), less weather noise
            growth_shoulder_y2=y2[y2.index.month.isin([4, 5, 10])].mean()
            / y1[y1.index.month.isin([4, 5, 10])].mean()
            - 1,
            growth_shoulder_y3=y3[y3.index.month.isin([4, 5, 10])].mean()
            / y2[y2.index.month.isin([4, 5, 10])].mean()
            - 1,
            peak_summer=summer.max(),
            peak_winter=winter.max(),
            sw_peak_ratio=summer.max() / winter.max(),
            sw_p99_ratio=summer.quantile(0.99) / winter.quantile(0.99),
            summer_over_shoulder=mon[[7, 8]].mean() / shoulder,
            winter_over_shoulder=mon[[1, 2]].mean() / shoulder,
            wd_we=wd / we,
            daily_min_over_max=(dmin / dmax).mean(),
            load_factor=pre.mean() / pre.max(),
            peak_hr_summer=int(shs.idxmax()),
            peak_hr_winter=int(shw.idxmax()),
            shape_range_summer=shs.max() - shs.min(),
            shape_range_winter=shw.max() - shw.min(),
            cv_daily=dmean.std() / dmean.mean(),
            first=str(s.first_valid_index()),
            last=str(s.last_valid_index()),
        )
    )
df = pd.DataFrame(rows).set_index("zone")
A = pd.DataFrame(anoms)
df["corr_DOM"] = A.corr()["DOM"]
df["corr_JC"] = A.corr()["JC"]
S = pd.DataFrame({z: pd.concat([a, b]).to_numpy() for z, (a, b) in shapes.items()})
df["shape_rmse_DOM"] = [np.sqrt(((S[z] - S["DOM"]) ** 2).mean()) for z in df.index]
df["shape_rmse_JC"] = [np.sqrt(((S[z] - S["JC"]) ** 2).mean()) for z in df.index]
# standardised distance on pre-window features
feat = pd.DataFrame(
    {
        "log_mean": np.log(df.mean_y2),
        "growth": df.growth_shoulder_y2,
        "sw_peak": df.sw_peak_ratio,
        "summer_sh": df.summer_over_shoulder,
        "winter_sh": df.winter_over_shoulder,
        "wd_we": df.wd_we,
        "min_max": df.daily_min_over_max,
    }
)
Z = (feat - feat.mean()) / feat.std()
for ref in ["DOM", "JC"]:
    df[f"dist_{ref}"] = np.sqrt(((Z - Z.loc[ref]) ** 2).sum(axis=1))
    df[f"dist_noscale_{ref}"] = np.sqrt(
        ((Z.drop(columns="log_mean") - Z.drop(columns="log_mean").loc[ref]) ** 2).sum(axis=1)
    )
df.to_csv(OUT / "zone_stats.csv")
A.corr().round(3).to_csv(OUT / "anomaly_corr.csv")
S.to_csv(OUT / "shapes.csv")
pd.set_option("display.width", 250)
pd.set_option("display.max_columns", 60)
pd.set_option("display.float_format", lambda v: f"{v:.3f}")
q = [
    "raw_missing_hist",
    "raw_missing_scored",
    "nonpos",
    "flagged",
    "dup",
    "stuck_hours",
    "long_gap_runs",
    "long_gap_hours",
    "missing_after_fill_pct",
    "scored_windows_ok",
    "last",
]
print(df[q])
print(df[["dropped"]].drop_duplicates())
print(
    df[
        [
            "mean_y1",
            "mean_y2",
            "mean_y3",
            "growth_y2",
            "growth_y3",
            "growth_shoulder_y2",
            "growth_shoulder_y3",
        ]
    ].round(3)
)
print(
    df[
        [
            "peak_summer",
            "peak_winter",
            "sw_peak_ratio",
            "sw_p99_ratio",
            "summer_over_shoulder",
            "winter_over_shoulder",
            "wd_we",
            "daily_min_over_max",
            "load_factor",
            "peak_hr_summer",
            "peak_hr_winter",
            "cv_daily",
        ]
    ]
)
print(
    df[
        [
            "corr_DOM",
            "corr_JC",
            "shape_rmse_DOM",
            "shape_rmse_JC",
            "dist_DOM",
            "dist_JC",
            "dist_noscale_DOM",
            "dist_noscale_JC",
        ]
    ]
)
