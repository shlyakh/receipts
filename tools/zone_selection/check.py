"""Extra checks on the eight zones looked at closely: shared gaps, level breaks, and that
DOM and JC match the repository's processed load.

    uv run --project core python tools/zone_selection/check.py
"""

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent.parent
EIA = ROOT / "data" / "zone_selection_raw"
full = pd.date_range("2023-11-01T00", "2026-11-11T05", freq="h", tz="UTC")
out = {}
for z in ["DOM", "JC", "AEP", "AE", "CE", "AP", "PE", "PEP"]:
    rows = []
    for p in sorted((EIA / z).glob("2*.json")):
        rows += json.loads(p.read_text())["data"]
    r = pd.DataFrame(rows)
    r["ds"] = pd.to_datetime(r["period"], format="%Y-%m-%dT%H", utc=True)
    out[z] = pd.to_numeric(r["value"]).set_axis(r["ds"]).reindex(full)
d = pd.DataFrame(out)
print("missing UTC days:", sorted({str(t.date()) for t in d.index[d["AEP"].isna()]}))
print("same missing hours in all:", all((d[c].isna() == d["DOM"].isna()).all() for c in d))
print("max |hourly change| / median load:")
print((d.diff().abs().max() / d.median()).round(3))
print("min / median:")
print((d.min() / d.median()).round(3))
m = d.resample("QS").mean().round(0)
print(m)
# compare with repo processed load for DOM, JC
rep = pd.read_parquet(ROOT / "data" / "processed" / "load.parquet")
for z in ["DOM", "JC"]:
    a = rep[rep.unique_id == z].set_index("ds")["y"].reindex(full)
    b = d[z]
    k = a.notna() & b.notna()
    print(z, "max abs diff vs repo:", float((a[k] - b[k]).abs().max()), "n", int(k.sum()))
