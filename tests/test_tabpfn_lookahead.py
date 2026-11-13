"""Lookahead and local-only checks for the TabPFN-TS adapter (models_ff/tabpfn_ts_v2.py).
Gate origins only. Runs in the models_ff environment; skipped in core:

    uv run --project models_ff --with pytest pytest tests/test_tabpfn_lookahead.py -q

The pipeline's predict_df is replaced by a recorder, so the test sees exactly what the
adapter hands TabPFN and does not run the model. The model can only use what it is given.
"""

from __future__ import annotations

import socket
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

pytest.importorskip("tabpfn_time_series")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "models_ff"))

import tabpfn_ts_v2 as adapter  # noqa: E402

INPUTS = ROOT / "data" / "model_inputs" / "gate.parquet"


class Recorder:
    def __init__(self) -> None:
        self.calls: list[tuple[pd.DataFrame, pd.DataFrame]] = []

    def predict_df(self, context, future_df=None, quantiles=None):
        self.calls.append((context.copy(), future_df.copy()))
        out = future_df[["item_id", "timestamp"]].copy()
        for col in ["target", *quantiles]:
            out[col] = 1.0
        return out


@pytest.fixture(scope="module")
def windows() -> pd.DataFrame:
    if not INPUTS.exists():
        pytest.skip("run `harness.export_inputs gate` first")
    return pd.read_parquet(INPUTS)


@pytest.mark.parametrize("regime", ["oracle", "forecast"])
def test_adapter_ignores_load_after_cutoff(windows, regime):
    cutoff = sorted(windows["cutoff"].unique())[1]
    for zone in ["JC", "DOM"]:
        win = windows[
            (windows["cutoff"] == cutoff)
            & (windows["regime"] == regime)
            & (windows["unique_id"] == zone)
        ]
        rec = Recorder()
        adapter.forecast_window(rec, win)
        bad = win.copy()
        bad.loc[bad["ds"] > cutoff, "y"] = -9999.0  # load after the cutoff
        adapter.forecast_window(rec, bad)
        (ctx, fut), (ctx2, fut2) = rec.calls
        pd.testing.assert_frame_equal(ctx, ctx2)
        pd.testing.assert_frame_equal(fut, fut2)
        last = cutoff.tz_convert("UTC").tz_localize(None)
        assert ctx["timestamp"].max() == last
        assert len(ctx) == adapter.CONTEXT_HOURS
        assert "target" not in fut.columns  # no load enters the horizon frame
        assert len(fut) == 168 and fut["timestamp"].min() == last + pd.Timedelta(hours=1)
        # Horizon temperature is exactly the regime's series from the harness.
        hz = win[win["ds"] > cutoff].sort_values("ds")
        assert np.allclose(fut["T"].to_numpy(), hz["T"].to_numpy())


def test_pipeline_is_local_and_network_is_refused():
    pipe = adapter.build_pipeline()  # raises unless the local regressor is selected
    assert pipe.predictor.inference_routine.__self__.model_class is adapter.TabPFNRegressor
    with pytest.raises(adapter.NetworkForbidden):
        socket.create_connection(("huggingface.co", 443), timeout=1)
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        with pytest.raises(adapter.NetworkForbidden):
            s.connect(("1.1.1.1", 443))
    finally:
        s.close()
    import tabpfn_client

    with pytest.raises(adapter.NetworkForbidden):
        tabpfn_client.init()
