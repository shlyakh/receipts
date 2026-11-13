"""TabPFN-TS with the TabPFN v2 regressor, temperature as a known covariate, LOCAL mode only.

    uv run --project models_ff python models_ff/tabpfn_ts_v2.py gate
    uv run --project models_ff python models_ff/tabpfn_ts_v2.py gate --limit 1
    uv run --project models_ff python models_ff/tabpfn_ts_v2.py scored   # at tag protocol-v1.3

Reads only data/model_inputs/<set>.parquet (v1 regimes) and <set>_weather_v12.parquet (the
four v1.2 regimes), which the harness writes (harness.export_inputs <set> [--v12]). The
harness owns the cutoffs: this script loops over the cutoffs in those files and calls the
model once per cutoff, zone and regime. A zone-window whose horizon temperature is
incomplete is not forecast (y_hat missing). Row written: tabpfn_ts_v2_temperature
(protocol-v1.3), to results/models_v13/forecasts/ (gate set: results/gate/models_v13/).

Resumable: each finished cutoff is saved under <out>/partial/; a restarted run (for
example after a reboot) skips the cutoffs already saved and only assembles the final file
once every cutoff is done. This changes nothing in the definition.

Settings, fixed on 2026-11-13 before any run and not tuned (protocol-v1.3.yaml):
  - `tabpfn_time_series.TabPFNTSPipeline` (installed 1.4.0), mode LOCAL, called directly
    (not through FoundationForecast, whose wrapper selects cloud mode without CUDA).
  - checkpoint `tabpfn-v2-regressor-2noar4o2.ckpt` from Prior-Labs/TabPFN-v2-reg at the
    revision in models/pins.json: the checkpoint the TabPFN-TS releases 0.1.x to 1.0.x used
    by default (their defaults.py, read on GitHub on 2026-11-13).
  - context 4,096 hours (the v2-era default `max_context_length`; the TabPFN-TS paper found
    no gain beyond it); the package's default features (known-covariate lags, running
    index, calendar, automatic seasonal terms); temperature `T` as the one known covariate.
  - point forecast = median of TabPFN's output; quantiles 0.1, 0.5, 0.9.
  - CPU (`device="cpu"`), `ignore_pretraining_limits=True` (the library refuses more than
    1,000 rows on CPU otherwise), other TabPFNRegressor settings at their defaults.

No data may leave this machine. Before anything is imported: telemetry off, Hugging Face
offline. Then every socket connection to a network address raises, the cloud client's
entry points raise, and checkpoint download raises; the pipeline is checked to hold the
local regressor. Any attempt to use the cloud path therefore fails loudly.
"""

from __future__ import annotations

import os

os.environ["TABPFN_DISABLE_TELEMETRY"] = "1"
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"

import socket  # noqa: E402


class NetworkForbidden(RuntimeError):
    pass


def _refuse(*_a, **_k):
    raise NetworkForbidden("tabpfn_ts_v2: network access attempted; this adapter is local only")


_connect = socket.socket.connect


def _guarded_connect(self, address):
    if self.family in (socket.AF_INET, socket.AF_INET6):
        _refuse()
    return _connect(self, address)


socket.socket.connect = _guarded_connect  # type: ignore[method-assign]
socket.socket.connect_ex = lambda self, address: _refuse()  # type: ignore[method-assign]
socket.create_connection = _refuse  # type: ignore[assignment]

import json  # noqa: E402
import subprocess  # noqa: E402
import sys  # noqa: E402
import time  # noqa: E402
from importlib.metadata import version  # noqa: E402
from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import tabpfn.model_loading  # noqa: E402
import tabpfn_client  # noqa: E402
from tabpfn import TabPFNRegressor  # noqa: E402
from tabpfn_time_series import TabPFNMode, TabPFNTSPipeline  # noqa: E402

# The cloud client and the checkpoint downloader must never run.
tabpfn_client.init = _refuse
tabpfn_client.TabPFNRegressor.fit = _refuse
tabpfn_client.TabPFNRegressor.predict = _refuse
tabpfn.model_loading.download_model = _refuse

ROOT = Path(__file__).resolve().parent.parent
NAME = "tabpfn_ts_v2_temperature"
PROTOCOL = "protocol-v1.3"
REPO_ID = "Prior-Labs/TabPFN-v2-reg"
CHECKPOINT = "tabpfn-v2-regressor-2noar4o2.ckpt"
CONTEXT_HOURS = 4096
H = 168
QUANTILES = [0.1, 0.5, 0.9]
REGIMES = ["oracle", "forecast", "oracle_era5", "forecast_gfs", "forecast_ifs", "forecast_aifs"]


def checkpoint_path() -> tuple[Path, dict]:
    pin = json.loads((ROOT / "models" / "pins.json").read_text())[REPO_ID]
    folder = "models--" + REPO_ID.replace("/", "--")
    path = ROOT / "models_cache" / folder / "snapshots" / pin["revision"] / CHECKPOINT
    if not path.is_file():  # tabpfn would otherwise try to download it
        raise FileNotFoundError(f"pinned checkpoint missing: {path}")
    return path, pin


def build_pipeline() -> TabPFNTSPipeline:
    path, _ = checkpoint_path()
    pipe = TabPFNTSPipeline(
        max_context_length=CONTEXT_HOURS,
        tabpfn_mode=TabPFNMode.LOCAL,
        tabpfn_output_selection="median",
        tabpfn_model_config={
            "model_path": str(path),
            "device": "cpu",
            "ignore_pretraining_limits": True,
        },
        compile=False,
    )
    adapter = pipe.predictor.inference_routine.__self__
    if adapter.model_class is not TabPFNRegressor:
        raise RuntimeError(f"not the local regressor: {adapter.model_class!r}")
    if type(pipe.predictor._worker).__name__ != "CPUParallelWorker":
        raise RuntimeError(f"unexpected worker {type(pipe.predictor._worker).__name__}")
    if Path(adapter.model_config["model_path"]).resolve() != path.resolve():
        raise RuntimeError("model_path was changed by the library")
    return pipe


def forecast_window(pipe: TabPFNTSPipeline, win: pd.DataFrame) -> pd.DataFrame:
    """One zone, regime and cutoff. Load is read only from rows at or before the cutoff;
    the horizon rows contribute their timestamps and temperature only."""
    win = win.sort_values("ds")
    cutoff = win["cutoff"].iloc[0]
    past = win[win["ds"] <= cutoff].tail(CONTEXT_HOURS)
    fut = win[win["ds"] > cutoff]
    assert len(fut) == H and fut["ds"].iloc[0] == cutoff + pd.Timedelta(hours=1)
    ts = lambda s: s.dt.tz_convert("UTC").dt.tz_localize(None)  # noqa: E731
    context = pd.DataFrame(
        {"item_id": 0, "timestamp": ts(past["ds"]), "target": past["y"], "T": past["T"]}
    )
    future = pd.DataFrame({"item_id": 0, "timestamp": ts(fut["ds"]), "T": fut["T"]})
    pred = pipe.predict_df(context, future_df=future, quantiles=QUANTILES)
    pred = pred.reset_index() if "timestamp" not in pred.columns else pred
    assert (pred["timestamp"].to_numpy() == future["timestamp"].to_numpy()).all(), "timestamps"
    out = pd.DataFrame(
        {
            "ds": fut["ds"].to_numpy(),
            "y_hat": pred["target"].to_numpy(),
            "q10": pred[0.1].to_numpy(),
            "q90": pred[0.9].to_numpy(),
        }
    )
    assert np.isfinite(out[["y_hat", "q10", "q90"]].to_numpy()).all(), "non-finite forecast"
    return out


def git(*a: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *a], cwd=ROOT, capture_output=True, text=True)


def require_frozen_v13(out_file: Path) -> str:
    """Scored run: at tag protocol-v1.3, clean tree, unchanged protocol files, once."""
    if not git("tag", "--list", PROTOCOL).stdout.strip():
        sys.exit(f"git tag {PROTOCOL} does not exist: scored origins must not be run yet")
    files = ["protocol.yaml", "protocol-v1.1.yaml", "protocol-v1.2.yaml", "protocol-v1.3.yaml"]
    if git("diff", "--quiet", PROTOCOL, "--", *files).returncode != 0:
        sys.exit(f"a protocol file differs from tag {PROTOCOL}")
    if git("status", "--porcelain", "--untracked-files=no").stdout.strip():
        sys.exit("commit the code before a scored run")
    if out_file.exists():
        sys.exit(f"{out_file} exists: the scored set is run once")
    return git("rev-parse", "--short", "HEAD").stdout.strip()


def main() -> None:
    args = sys.argv[1:]
    which = args[0] if args else ""
    limit = int(args[args.index("--limit") + 1]) if "--limit" in args else None
    if which not in ("gate", "scored"):
        sys.exit(__doc__)
    base = (ROOT / "results" if which == "scored" else ROOT / "results" / which) / "models_v13"
    out_file = base / "forecasts" / f"{NAME}.parquet"
    if which == "scored":
        if limit:
            sys.exit("--limit is for the gate set")
        commit = require_frozen_v13(out_file)
    else:
        dirty = git("status", "--porcelain", "--untracked-files=no").stdout.strip()
        commit = git("rev-parse", "--short", "HEAD").stdout.strip() + ("-dirty" if dirty else "")
    _, pin = checkpoint_path()
    pipe = build_pipeline()

    folder = ROOT / "data" / "model_inputs"
    inputs = pd.concat(
        [
            pd.read_parquet(folder / f"{which}.parquet"),
            pd.read_parquet(folder / f"{which}_weather_v12.parquet"),
        ],
        ignore_index=True,
    )
    assert set(inputs["regime"]) == set(REGIMES), sorted(set(inputs["regime"]))
    cutoffs = sorted(inputs["cutoff"].unique())[:limit]
    partial = base / "partial" / NAME
    partial.mkdir(parents=True, exist_ok=True)
    for i, cutoff in enumerate(cutoffs):
        done = partial / f"{pd.Timestamp(cutoff):%Y%m%dT%H}.parquet"
        if done.exists():
            print(f"{i + 1}/{len(cutoffs)} cutoffs (saved earlier)", flush=True)
            continue
        at = inputs[inputs["cutoff"] == cutoff]
        parts = []
        for (regime, zone), win in at.groupby(["regime", "unique_id"]):
            fut = win[win["is_horizon"]]
            if fut["T"].isna().any():  # incomplete horizon temperature: not forecast
                out = pd.DataFrame(
                    {"ds": fut["ds"].to_numpy(), "y_hat": np.nan, "q10": np.nan, "q90": np.nan}
                )
                runtime = np.nan
            else:
                t0 = time.perf_counter()
                out = forecast_window(pipe, win)
                runtime = time.perf_counter() - t0
            parts.append(
                out.assign(unique_id=zone, regime=regime, cutoff=cutoff, runtime_s=runtime)
            )
            print(f"{pd.Timestamp(cutoff):%Y-%m-%d} {regime} {zone}: {runtime:.1f} s", flush=True)
        pd.concat(parts, ignore_index=True).assign(git_commit=commit).to_parquet(done)
        print(f"{i + 1}/{len(cutoffs)} cutoffs", flush=True)

    parts = [pd.read_parquet(partial / f"{pd.Timestamp(c):%Y%m%dT%H}.parquet") for c in cutoffs]
    commits = {c for p in parts for c in p["git_commit"].unique()}
    if len(commits) != 1:
        sys.exit(f"partial files come from different commits: {sorted(commits)}")
    df = pd.concat(parts, ignore_index=True)
    df["model"] = NAME
    df["weather"] = "temperature"
    df["protocol_version"] = PROTOCOL
    df["weights_revision"] = pin["revision"]
    df["weights_date"] = pin["weights_date"]
    df["context_hours"] = CONTEXT_HOURS
    df["library"] = (
        f"tabpfn-time-series {version('tabpfn-time-series')}, tabpfn {version('tabpfn')}, "
        f"{CHECKPOINT}, local cpu"
    )
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
    (base / "forecasts").mkdir(parents=True, exist_ok=True)
    df[keep].to_parquet(out_file, index=False)
    print(NAME, len(df), "rows, mean runtime per window", round(df["runtime_s"].mean(), 1), "s")


if __name__ == "__main__":
    main()
