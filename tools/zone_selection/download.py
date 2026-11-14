"""Download every PJM sub-BA load series from EIA-930, 2023-11-01 to 2026-11-13, for the
protocol-v2 zone selection (notes/zone_selection.md). Separate from fetch.py and data/raw:
these files are used only to describe zones, never by the harness.

    uv run --project core python tools/zone_selection/download.py

Skips chunks already on disk. Never prints the key or the request URL. Then writes
results/zone_selection/raw_manifest.json (SHA-256 of every raw file)."""

import hashlib
import json
import os
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd
import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent.parent
RAW = ROOT / "data" / "zone_selection_raw"  # git-ignored; hashes in results/zone_selection
OUT = ROOT / "results" / "zone_selection"
load_dotenv(ROOT / ".env")
KEY = os.environ["EIA_API_KEY"]
URL = "https://api.eia.gov/v2/electricity/rto/region-sub-ba-data/data/"
zones = [z for z, _ in json.loads((OUT / "pjm_zones.json").read_text())]
edges = list(pd.date_range("2023-11-01", "2026-11-14", freq="200D")) + [pd.Timestamp("2026-11-14")]
chunks = list(zip(edges[:-1], edges[1:], strict=True))
jobs = [(z, a, b - pd.Timedelta(hours=1)) for z in zones for a, b in chunks]


def run(job):
    z, a, b = job
    f = RAW / z / f"{a:%Y%m%d}.json"
    if f.exists():
        return "skip"
    f.parent.mkdir(parents=True, exist_ok=True)
    p = [
        ("api_key", KEY),
        ("frequency", "hourly"),
        ("data[0]", "value"),
        ("facets[parent][]", "PJM"),
        ("facets[subba][]", z),
        ("start", f"{a:%Y-%m-%dT%H}"),
        ("end", f"{b:%Y-%m-%dT%H}"),
        ("sort[0][column]", "period"),
        ("sort[0][direction]", "asc"),
        ("offset", "0"),
        ("length", "5000"),
    ]
    err = "?"
    for i in range(6):
        try:
            r = requests.get(URL, params=p, timeout=240)
            if r.status_code == 200:
                resp = r.json()["response"]
                assert int(resp["total"]) <= 5000
                f.write_text(json.dumps({"total": int(resp["total"]), "data": resp["data"]}))
                return f"{z} {a:%Y%m%d} {resp['total']}"
            err = f"HTTP {r.status_code}"
        except requests.RequestException as e:
            err = type(e).__name__
        time.sleep(3 * (i + 1))
    return f"{z} {a:%Y%m%d} FAILED {err}"


with ThreadPoolExecutor(6) as ex:
    for res in ex.map(run, jobs):
        if res != "skip":
            print(res, flush=True)
manifest = {
    str(p.relative_to(RAW)): hashlib.sha256(p.read_bytes()).hexdigest()
    for p in sorted(RAW.glob("*/2*.json"))
}
(OUT / "raw_manifest.json").write_text(json.dumps(manifest, indent=1) + "\n")
print("done,", len(manifest), "files hashed")
