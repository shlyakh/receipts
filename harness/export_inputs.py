"""Write the exact inputs a foundation model may see, one file per origin set.

    uv run --project core python -m harness.export_inputs gate
    uv run --project core python -m harness.export_inputs gate --v12   # protocol-v1.2 regimes

The models/ environment reads only this file, so it cannot see anything the harness
did not hand it (CLAUDE.md rules 1 to 3). For every zone, regime and cutoff the file
holds CONTEXT_HOURS rows up to the cutoff (y and T) and 168 horizon rows (T only).
Output: data/model_inputs/<set>.parquet with columns
unique_id, regime, cutoff, ds, y, T, is_horizon. With --v12 the four protocol-v1.2
weather regimes go to data/model_inputs/<set>_weather_v12.parquet instead (ERA5 history,
the regime's horizon series); the v1 file is not touched.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fetch import verify_manifest  # noqa: E402

from harness.data import ROOT, V12_REGIMES, Data, load_protocol, origins  # noqa: E402
from harness.run import REGIMES, require_frozen, require_frozen_v12  # noqa: E402

CONTEXT_HOURS = 4096


def main() -> None:
    which = sys.argv[1] if len(sys.argv) > 1 else ""
    v12 = sys.argv[2:] == ["--v12"]
    if which not in ("gate", "ordering_gate", "scored") or (sys.argv[2:] and not v12):
        sys.exit(__doc__)
    proto = load_protocol()
    verify_manifest()
    if which == "scored":
        require_frozen_v12(proto) if v12 else require_frozen(proto)
    data = Data()
    frames = []
    for regime in V12_REGIMES if v12 else REGIMES:
        for zone in proto["zones"]:
            for cutoff in origins(proto, which):
                temp = data.temperature(zone, cutoff, regime)  # ends at cutoff + 168 h
                idx = temp.index[-(CONTEXT_HOURS + 168) :]
                y = data.history(zone, cutoff).reindex(idx)  # missing over the horizon
                frames.append(
                    pd.DataFrame(
                        {
                            "unique_id": zone,
                            "regime": regime,
                            "cutoff": cutoff,
                            "ds": idx,
                            "y": y.to_numpy(),
                            "T": temp.reindex(idx).to_numpy(),
                            "is_horizon": np.asarray(idx > cutoff),
                        }
                    )
                )
    df = pd.concat(frames, ignore_index=True)
    assert df.loc[df["is_horizon"], "y"].isna().all()  # no load after the cutoff leaves here
    out = ROOT / "data" / "model_inputs"
    out.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out / f"{which}{'_weather_v12' if v12 else ''}.parquet", index=False)
    print(
        f"{which}: {df.groupby(['unique_id', 'regime', 'cutoff']).ngroups} windows, {len(df)} rows"
    )


if __name__ == "__main__":
    main()
