"""Download raw load and weather, hash it, and build the processed parquet files.

Usage (from the repo root):
    uv run --project core python fetch.py download   # raw files + fetch_manifest.json
    uv run --project core python fetch.py process    # data/processed/*.parquet
    uv run --project core python fetch.py verify     # check raw files against the manifest

Zones, stations and date ranges come from protocol.yaml.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd
import requests
import yaml

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
MANIFEST = ROOT / "fetch_manifest.json"
QUALITY_LOG = ROOT / "data" / "quality_log.csv"

EIA_URL = "https://api.eia.gov/v2/electricity/rto/region-sub-ba-data/data/"
EIA_PAGE = 5000
WEATHER_VARS = ["temperature_2m", "wind_speed_10m", "shortwave_radiation", "dew_point_2m"]
LEAD_DAYS = range(1, 8)
MAX_FILL_RUN = 3
FLAG_FACTOR = 3.0
PREVIOUS_RUNS_CHUNK_DAYS = 92


def load_protocol() -> dict:
    return yaml.safe_load((ROOT / "protocol.yaml").read_text())


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def get_json(url: str, params: list[tuple[str, str]] | dict, tries: int = 5) -> dict:
    for attempt in range(tries):
        try:
            r = requests.get(url, params=params, timeout=180)
        except requests.exceptions.RequestException as exc:
            # Report the exception type only: its text can carry the request URL.
            if attempt < tries - 1:
                time.sleep(15 * (attempt + 1))
                continue
            raise RuntimeError(f"{url} failed: {type(exc).__name__}") from None
        if r.status_code == 200:
            return r.json()
        if r.status_code in (429, 500, 502, 503, 504) and attempt < tries - 1:
            time.sleep(15 * (attempt + 1))
            continue
        # Never echo the request URL: it carries the API key.
        raise RuntimeError(f"{url} returned HTTP {r.status_code}")
    raise RuntimeError("unreachable")


# ------------------------------------------------------------------ download


def download_eia(proto: dict) -> None:
    from dotenv import load_dotenv

    load_dotenv(ROOT / ".env")
    key = os.environ.get("EIA_API_KEY")
    if not key:
        sys.exit("EIA_API_KEY is missing from .env")
    cfg = proto["load"]
    for zone in proto["zones"]:
        out = RAW / "eia" / zone
        out.mkdir(parents=True, exist_ok=True)
        offset, total = 0, None
        while total is None or offset < total:
            params = [
                ("api_key", key),
                ("frequency", cfg["frequency"]),
                ("data[0]", "value"),
                ("facets[parent][]", cfg["facets"]["parent"]),
                ("facets[subba][]", zone),
                ("start", cfg["start"]),
                ("end", cfg["end"]),
                ("sort[0][column]", "period"),
                ("sort[0][direction]", "asc"),
                ("offset", str(offset)),
                ("length", str(EIA_PAGE)),
            ]
            resp = get_json(EIA_URL, params)["response"]
            total = int(resp["total"])
            # Keep only the data rows and the total: the full body echoes the request.
            page = {"total": total, "offset": offset, "data": resp["data"]}
            (out / f"offset_{offset:06d}.json").write_text(json.dumps(page))
            print(f"EIA {zone}: {offset + len(resp['data'])}/{total}")
            if not resp["data"]:
                break
            offset += EIA_PAGE
            time.sleep(0.5)


def date_chunks(start: str, end: str, days: int) -> list[tuple[str, str]]:
    out, a, stop = [], pd.Timestamp(start), pd.Timestamp(end)
    while a <= stop:
        b = min(a + pd.Timedelta(days=days - 1), stop)
        out.append((a.strftime("%Y-%m-%d"), b.strftime("%Y-%m-%d")))
        a = b + pd.Timedelta(days=1)
    return out


def download_weather(proto: dict) -> None:
    """One archive file per station; Previous Runs in date chunks. Existing files are kept."""
    w = proto["weather"]
    out = RAW / "openmeteo"
    out.mkdir(parents=True, exist_ok=True)
    prev_vars = []
    for v in WEATHER_VARS:
        prev_vars += [f"{v}_previous_day{k}" for k in LEAD_DAYS]
    chunks = date_chunks(
        w["previous_runs"]["start_date"], w["previous_runs"]["end_date"], PREVIOUS_RUNS_CHUNK_DAYS
    )
    for zone, stations in w["stations"].items():
        for s in stations:
            base = {"latitude": s["lat"], "longitude": s["lon"], "timezone": "GMT"}
            path = out / f"archive_{zone}_{s['name']}.json"
            if not path.exists():
                arch = get_json(
                    w["archive"]["endpoint"],
                    base
                    | {
                        "hourly": ",".join(WEATHER_VARS),
                        "start_date": w["archive"]["start_date"],
                        "end_date": w["archive"]["end_date"],
                    },
                )
                path.write_text(json.dumps(arch))
                print(f"archive {zone} {s['name']}: {len(arch['hourly']['time'])} hours")
                time.sleep(10)
            for a, b in chunks:
                path = out / f"previous_runs_{zone}_{s['name']}_{a}.json"
                if path.exists():
                    continue
                prev = get_json(
                    w["previous_runs"]["endpoint"],
                    base | {"hourly": ",".join(prev_vars), "start_date": a, "end_date": b},
                )
                path.write_text(json.dumps(prev))
                print(f"previous runs {zone} {s['name']} {a}: {len(prev['hourly']['time'])} hours")
                time.sleep(5)


def write_manifest() -> None:
    files = sorted(p for p in RAW.rglob("*.json"))
    manifest = {
        "written_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "files": {
            str(p.relative_to(ROOT)): {"sha256": sha256(p), "bytes": p.stat().st_size}
            for p in files
        },
    }
    MANIFEST.write_text(json.dumps(manifest, indent=1) + "\n")
    print(f"manifest: {len(files)} files")


def verify_manifest() -> None:
    """Raise if any raw file is missing, changed, or not listed (CLAUDE.md rule 6)."""
    if not MANIFEST.exists():
        raise RuntimeError("fetch_manifest.json is missing")
    listed = json.loads(MANIFEST.read_text())["files"]
    on_disk = {str(p.relative_to(ROOT)) for p in RAW.rglob("*.json")}
    problems = [f"not in manifest: {p}" for p in sorted(on_disk - set(listed))]
    for rel, meta in listed.items():
        path = ROOT / rel
        if not path.exists():
            problems.append(f"missing: {rel}")
        elif sha256(path) != meta["sha256"]:
            problems.append(f"hash mismatch: {rel}")
    if problems:
        raise RuntimeError("raw data does not match fetch_manifest.json:\n" + "\n".join(problems))


# ------------------------------------------------------------------- process


def process_load(proto: dict) -> pd.DataFrame:
    cfg = proto["load"]
    full = pd.date_range(
        pd.Timestamp(cfg["start"], tz="UTC"), pd.Timestamp(cfg["end"], tz="UTC"), freq="h"
    )
    frames, log = [], []
    for zone in proto["zones"]:
        rows = []
        for page in sorted((RAW / "eia" / zone).glob("offset_*.json")):
            rows += json.loads(page.read_text())["data"]
        raw = pd.DataFrame(rows)
        raw["ds"] = pd.to_datetime(raw["period"], format="%Y-%m-%dT%H", utc=True)
        raw["y"] = pd.to_numeric(raw["value"], errors="coerce")
        dup = raw[raw.duplicated("ds", keep="first")]
        for r in dup.itertuples():
            log.append((zone, r.ds, "duplicate_dropped", r.y, np.nan))
        s = raw.drop_duplicates("ds", keep="first").set_index("ds")["y"].reindex(full)

        for ts in s.index[s.isna()]:
            log.append((zone, ts, "missing", np.nan, np.nan))

        # Flag rule: gross errors only. A value is flagged when it is <= 0, or more
        # than FLAG_FACTOR times (or less than 1/FLAG_FACTOR of) the median of the same
        # hour of day over the surrounding 7 days. Real peaks must survive this.
        same_hour_median = s.groupby(s.index.hour).transform(
            lambda x: x.rolling(7, center=True, min_periods=4).median()
        )
        ratio = s / same_hour_median
        flagged = s.notna() & ((s <= 0) | (ratio > FLAG_FACTOR) | (ratio < 1 / FLAG_FACTOR))
        for ts in s.index[flagged]:
            log.append((zone, ts, "flagged", s[ts], same_hour_median[ts]))
        s = s.mask(flagged)

        # Fill runs of <= MAX_FILL_RUN missing hours by linear interpolation.
        isna = s.isna()
        run_id = (isna != isna.shift()).cumsum()
        run_len = isna.groupby(run_id).transform("sum")
        fillable = isna & (run_len <= MAX_FILL_RUN)
        interp = s.interpolate(method="time", limit_area="inside")
        filled = s.where(~fillable, interp)
        for ts in s.index[fillable & filled.notna()]:
            log.append((zone, ts, "filled_interpolated", np.nan, filled[ts]))
        frames.append(pd.DataFrame({"unique_id": zone, "ds": full, "y": filled.to_numpy()}))

    load = pd.concat(frames, ignore_index=True)
    qlog = pd.DataFrame(
        log, columns=["unique_id", "ds", "action", "raw_value", "reference_or_fill"]
    )
    qlog.sort_values(["unique_id", "ds", "action"]).to_csv(QUALITY_LOG, index=False)
    return load


def _station_frame(path: Path) -> pd.DataFrame:
    h = json.loads(path.read_text())["hourly"]
    df = pd.DataFrame(h)
    df["ds"] = pd.to_datetime(df.pop("time"), utc=True)
    return df.set_index("ds")


def process_weather(proto: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Average stations to one series per zone.

    weather_oracle:   unique_id, ds, <var>                (reanalysis)
    weather_forecast: unique_id, ds, lead_day, <var>      (forecast made lead_day days earlier)
    """
    oracle, forecast = [], []
    for zone, stations in proto["weather"]["stations"].items():
        arch = [
            _station_frame(RAW / "openmeteo" / f"archive_{zone}_{s['name']}.json") for s in stations
        ]
        prev = [
            pd.concat(
                _station_frame(f)
                for f in sorted(
                    (RAW / "openmeteo").glob(f"previous_runs_{zone}_{s['name']}_*.json")
                )
            )
            for s in stations
        ]
        # skipna=False: a zone value exists only when every station has one.
        a = sum(arch) / len(arch)
        a = a.reset_index()
        a.insert(0, "unique_id", zone)
        oracle.append(a)
        p = sum(prev) / len(prev)
        for k in LEAD_DAYS:
            cols = {f"{v}_previous_day{k}": v for v in WEATHER_VARS}
            part = p[list(cols)].rename(columns=cols).reset_index()
            part.insert(0, "unique_id", zone)
            part.insert(2, "lead_day", k)
            forecast.append(part)
    return pd.concat(oracle, ignore_index=True), pd.concat(forecast, ignore_index=True)


def process() -> None:
    verify_manifest()
    proto = load_protocol()
    PROCESSED.mkdir(parents=True, exist_ok=True)
    load = process_load(proto)
    load.to_parquet(PROCESSED / "load.parquet", index=False)
    oracle, forecast = process_weather(proto)
    oracle.to_parquet(PROCESSED / "weather_oracle.parquet", index=False)
    forecast.to_parquet(PROCESSED / "weather_forecast.parquet", index=False)
    print("load", load.shape, "missing after fill:", int(load.y.isna().sum()))
    print("oracle", oracle.shape, "forecast", forecast.shape)


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "download":
        proto = load_protocol()
        download_eia(proto)
        download_weather(proto)
        write_manifest()
    elif cmd == "download-weather":
        download_weather(load_protocol())
        write_manifest()
    elif cmd == "process":
        process()
    elif cmd == "verify":
        verify_manifest()
        print("raw files match fetch_manifest.json")
    else:
        sys.exit(__doc__)
