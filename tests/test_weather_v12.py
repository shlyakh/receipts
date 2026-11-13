"""Gate checks for the protocol-v1.2 weather regimes (protocol-v1.2.yaml).
Gate origins only, never the scored ones.

uv run --project core pytest tests -q
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import fetch  # noqa: E402
from harness.baselines import lag_regression_temperature, vanilla_benchmark_trend  # noqa: E402
from harness.data import V12_PARQUET, V12_REGIMES, Data, horizon_index, load_protocol, origins  # noqa: E402

PROTO = load_protocol()
GATE = origins(PROTO, "gate")
H = pd.Timedelta(hours=1)
FORECAST = ("forecast_gfs", "forecast_ifs", "forecast_aifs")
V12_MODELS = {
    "lag_regression_temperature": lag_regression_temperature,
    "vanilla_benchmark_trend": vanilla_benchmark_trend,
}


@pytest.fixture(scope="module")
def data() -> Data:
    d = Data()
    d._load_v12()
    return d


def source_tables(data: Data, zone: str) -> dict[str, pd.DataFrame]:
    """The lead table each forecast regime reads (forecast_gfs: the v1 forecast table)."""
    return {"forecast_gfs": data.forecast[zone]} | {
        r: data.forecast_v12[r][zone] for r in ("forecast_ifs", "forecast_aifs")
    }


def test_fetch_and_harness_agree_on_files():
    assert fetch.V12_PARQUET == V12_PARQUET
    assert set(fetch.V12_FORECAST_MODELS) | {"oracle_era5", "forecast_gfs"} == set(V12_REGIMES)


@pytest.mark.parametrize("regime", V12_REGIMES)
def test_v12_inputs_stop_at_cutoff_and_history_is_era5(data, regime):
    for zone in PROTO["zones"]:
        for c in GATE:
            temp = data.temperature(zone, c, regime)
            assert temp.index.max() == c + 168 * H
            assert temp.index.is_unique and temp.index.is_monotonic_increasing
            # History is ERA5 in every v1.2 regime, never the v1 oracle series.
            assert temp.loc[:c].equals(data.era5[zone].loc[:c])
            assert not np.allclose(
                temp.loc[c - 167 * H : c].to_numpy(), data.oracle[zone].loc[c - 167 * H : c]
            )
            assert temp.loc[c + H :].notna().all()  # gate origins are complete in every regime


@pytest.mark.parametrize("regime", FORECAST)
def test_v12_forecast_regimes_use_lead_matched_values(data, regime):
    zone, c = "JC", GATE[0]
    hz = horizon_index(c)
    temp = data.temperature(zone, c, regime).reindex(hz)
    tab = source_tables(data, zone)[regime]
    for k in range(1, 8):
        hours = hz[24 * (k - 1) : 24 * k]
        expected = tab.loc[hours, k]
        assert np.allclose(temp.loc[hours].to_numpy(), expected.to_numpy(), equal_nan=True)
    assert not np.allclose(temp.to_numpy(), data.era5[zone].reindex(hz).to_numpy())


def test_forecast_gfs_horizon_equals_v1_forecast_regime(data):
    """forecast_gfs differs from the v1 forecast regime only in its history."""
    for zone in PROTO["zones"]:
        for c in GATE:
            a = data.temperature(zone, c, "forecast_gfs")
            b = data.temperature(zone, c, "forecast")
            assert a.loc[c + H :].equals(b.loc[c + H :])
            assert a.loc[:c].equals(data.era5[zone].loc[:c])


def test_v1_regimes_are_unchanged_by_v12(data):
    """Loading the v1.2 tables must not alter what the v1 regimes return."""
    fresh = Data()
    for zone in PROTO["zones"]:
        for regime in ("oracle", "forecast"):
            pd.testing.assert_series_equal(
                fresh.temperature(zone, GATE[0], regime), data.temperature(zone, GATE[0], regime)
            )


@pytest.mark.parametrize("regime", V12_REGIMES)
def test_v12_forecasts_ignore_everything_after_the_cutoff(data, regime):
    """Corrupt all load after the cutoff, all ERA5 after the cutoff (or after the horizon
    for oracle_era5), every value of the other sources, and every value of the regime's
    own source except the lead-matched horizon values. The v1 oracle series is corrupted
    everywhere: no v1.2 regime may read it."""
    zone, c = "DOM", GATE[1]
    hz = horizon_index(c)
    before = {
        m: fn(data.history(zone, c), data.temperature(zone, c, regime), c)
        for m, fn in V12_MODELS.items()
    }
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
        tables = source_tables(data, zone)
        if regime == "oracle_era5":
            data.era5[zone].loc[hz[-1] + H :] = 99.0
        else:
            data.era5[zone].loc[c + H :] = 99.0
        for r, tab in tables.items():
            if r != regime:
                tab.loc[:] = 99.0
                continue
            for k in range(1, 8):  # every lead except the matched one
                other = hz.delete(slice(24 * (k - 1), 24 * k))
                tab.loc[tab.index.intersection(other), k] = 99.0
            tab.loc[tab.index.difference(hz)] = 99.0  # and every hour outside the horizon
        for m, fn in V12_MODELS.items():
            after = fn(data.history(zone, c), data.temperature(zone, c, regime), c)
            pd.testing.assert_series_equal(before[m], after)
    finally:
        y0, e0, o0, f0, v0 = saved
        data.y[zone], data.era5[zone], data.oracle[zone], data.forecast[zone] = y0, e0, o0, f0
        for r, t in v0.items():
            data.forecast_v12[r][zone] = t
