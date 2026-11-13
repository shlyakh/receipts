"""Gate checks for the protocol-v1.3 rows (protocol-v1.3.yaml). Gate origins only.

uv run --project core pytest tests -q

lightgbm_competition is also in harness.baselines.MODELS, so tests/test_gates.py checks it
in the v1 regimes. Here: the same corruption check in the four v1.2 regimes, and the
rule that a window with incomplete horizon temperature is not forecast. The TabPFN
adapter is checked in tests/test_tabpfn_lookahead.py (models_ff environment).
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from harness.baselines import MODEL_PROTOCOL, lightgbm_competition  # noqa: E402
from harness.data import V12_REGIMES, Data, horizon_index, load_protocol, origins  # noqa: E402
from harness.v13 import NEW_ROWS, V13_REGIMES  # noqa: E402

PROTO = load_protocol()
GATE = origins(PROTO, "gate")
H = pd.Timedelta(hours=1)


@pytest.fixture(scope="module")
def data() -> Data:
    d = Data()
    d._load_v12()
    return d


def test_rows_carry_v13_label_and_six_regimes():
    assert all(MODEL_PROTOCOL[m] == "protocol-v1.3" for m in NEW_ROWS)
    assert V13_REGIMES == ["oracle", "forecast", *V12_REGIMES]


@pytest.mark.parametrize("regime", V12_REGIMES)
def test_lightgbm_competition_ignores_everything_after_the_cutoff_v12(data, regime):
    """Corrupt load after the cutoff, ERA5 after the cutoff (after the horizon for
    oracle_era5), the v1 oracle series everywhere, every other source, and every value of
    the regime's own source except the lead-matched horizon values."""
    zone, c = "JC", GATE[2]
    hz = horizon_index(c)
    before = lightgbm_competition(data.history(zone, c), data.temperature(zone, c, regime), c)
    saved = (
        data.y[zone].copy(),
        data.era5[zone].copy(),
        data.oracle[zone].copy(),
        data.forecast[zone].copy(),
        {r: data.forecast_v12[r][zone].copy() for r in ("forecast_ifs", "forecast_aifs")},
    )
    try:
        data.y[zone].loc[c + H :] = -9999.0
        data.oracle[zone].loc[:] = 99.0
        if regime == "oracle_era5":
            data.era5[zone].loc[hz[-1] + H :] = 99.0
        else:
            data.era5[zone].loc[c + H :] = 99.0
        tables = {"forecast_gfs": data.forecast[zone]} | {
            r: data.forecast_v12[r][zone] for r in ("forecast_ifs", "forecast_aifs")
        }
        for r, tab in tables.items():
            if r != regime:
                tab.loc[:] = 99.0
                continue
            for k in range(1, 8):
                other = hz.delete(slice(24 * (k - 1), 24 * k))
                tab.loc[tab.index.intersection(other), k] = 99.0
            tab.loc[tab.index.difference(hz)] = 99.0
        after = lightgbm_competition(data.history(zone, c), data.temperature(zone, c, regime), c)
        pd.testing.assert_series_equal(before, after)
    finally:
        y0, e0, o0, f0, v0 = saved
        data.y[zone], data.era5[zone], data.oracle[zone], data.forecast[zone] = y0, e0, o0, f0
        for r, t in v0.items():
            data.forecast_v12[r][zone] = t


def test_incomplete_horizon_temperature_is_not_forecast(data):
    zone, c = "DOM", GATE[0]
    temp = data.temperature(zone, c, "forecast").copy()
    temp.loc[c + 30 * H] = np.nan
    out = lightgbm_competition(data.history(zone, c), temp, c)
    assert len(out) == 168 and out.isna().all()
