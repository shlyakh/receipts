"""Write the exact inputs a foundation model may see, one file per origin set.

    uv run --project core python -m harness.export_inputs gate

The models/ environment reads only this file, so it cannot see anything the harness
did not hand it (CLAUDE.md rules 1 to 3). For every zone, regime and cutoff the file
holds CONTEXT_HOURS rows up to the cutoff (y and T) and 168 horizon rows (T only).
Output: data/model_inputs/<set>.parquet with columns
unique_id, regime, cutoff, ds, y, T, is_horizon.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fetch import verify_manifest  # noqa: E402
from harness.data import ROOT, Data, load_protocol, origins  # noqa: E402
from harness.run import REGIMES, require_frozen  # noqa: E402

CONTEXT_HOURS = 4096


def main() -> None:
    which = sys.argv[1] if len(sys.argv) > 1 else ""
    if which not in ("gate", "ordering_gate", "scored"):
        sys.exit(__doc__)
    proto = load_protocol()
    verify_manifest()
    if which == "scored":
        require_frozen(proto)
    data = Data()
    frames = []
    for regime in REGIMES:
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
    df.to_parquet(out / f"{which}.parquet", index=False)
    print(
        f"{which}: {df.groupby(['unique_id', 'regime', 'cutoff']).ngroups} windows, {len(df)} rows"
    )


if __name__ == "__main__":
    main()
