"""Gate checks. They use the gate origins only, never the scored ones.

uv run --project core pytest tests -q
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import statsmodels.formula.api as smf

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fetch import verify_manifest  # noqa: E402
from harness.baselines import (  # noqa: E402
    MODELS,
    lag_frame,
    lag_regression_temperature,
)
from harness.data import ROOT, Data, horizon_index, load_protocol, origin_utc, origins  # noqa: E402

PROTO = load_protocol()
GATE = origins(PROTO, "gate")
H = pd.Timedelta(hours=1)


@pytest.fixture(scope="module")
def data() -> Data:
    return Data()


def test_raw_files_match_manifest():
    verify_manifest()


def test_origins_are_local_monday_midnight():
    tz = PROTO["timezone"]
    assert origin_utc("2025-11-10", tz) == pd.Timestamp("2025-11-10 05:00", tz="UTC")  # EST
    assert origin_utc("2026-07-06", tz) == pd.Timestamp("2026-07-06 04:00", tz="UTC")  # EDT
    every = origins(PROTO, "gate") + origins(PROTO, "scored")
    for c in every:
        local = c.tz_convert(tz)
        assert (local.day_of_week, local.hour, local.minute) == (0, 0, 0)
    assert len(set(every)) == 58
    assert max(origins(PROTO, "gate")) < min(origins(PROTO, "scored"))
    diffs = {b - a for a, b in zip(every[:-1], every[1:], strict=True)}
    assert diffs <= {pd.Timedelta(hours=167), pd.Timedelta(hours=168), pd.Timedelta(hours=169)}


def test_first_horizon_hour_is_monday_first_local_hour():
    from harness.data import calendar

    for c in GATE:
        cal = calendar(horizon_index(c))
        assert (cal["hour"].iloc[0], cal["dow"].iloc[0]) == (0, 0)
        assert cal["dow"].iloc[-1] == 6  # the last hour belongs to Sunday


@pytest.mark.parametrize("regime", ["oracle", "forecast"])
def test_inputs_stop_at_cutoff_and_horizon(data, regime):
    for zone in PROTO["zones"]:
        for c in GATE:
            assert data.history(zone, c).index.max() <= c
            temp = data.temperature(zone, c, regime)
            assert temp.index.max() == c + 168 * H
            assert temp.index.is_unique and temp.index.is_monotonic_increasing
            assert temp.loc[:c].equals(data.oracle[zone].loc[:c])
            assert temp.loc[c + H :].notna().all()


def test_forecast_regime_uses_lead_matched_values(data):
    zone, c = "JC", GATE[0]
    hz = horizon_index(c)
    temp = data.temperature(zone, c, "forecast").reindex(hz)
    for k in range(1, 8):
        hours = hz[24 * (k - 1) : 24 * k]
        expected = data.forecast[zone].loc[hours, k]
        assert np.allclose(temp.loc[hours].to_numpy(), expected.to_numpy())
    # Forecast weather must differ from the reanalysis actuals somewhere.
    assert not np.allclose(temp.to_numpy(), data.oracle[zone].reindex(hz).to_numpy())


@pytest.mark.parametrize("regime", ["oracle", "forecast"])
def test_forecasts_ignore_everything_after_the_cutoff(data, regime):
    """Corrupt all load after the cutoff, and all weather the regime does not allow.
    Forecasts must not change."""
    zone, c = "DOM", GATE[1]
    hz = horizon_index(c)
    before = {
        m: fn(data.history(zone, c), data.temperature(zone, c, regime) if w else None, c)
        for m, (fn, w) in MODELS.items()
    }
    y0, o0, f0 = data.y[zone].copy(), data.oracle[zone].copy(), data.forecast[zone].copy()
    try:
        data.y[zone].loc[c + H :] = -9999.0
        data.oracle[zone].loc[hz[-1] + H :] = 99.0
        if regime == "forecast":
            data.oracle[zone].loc[c + H :] = 99.0  # reanalysis after the cutoff is not allowed
            for k in range(1, 8):  # every lead except the matched one
                other = hz.delete(slice(24 * (k - 1), 24 * k))
                data.forecast[zone].loc[other, k] = 99.0
        for m, (fn, w) in MODELS.items():
            after = fn(data.history(zone, c), data.temperature(zone, c, regime) if w else None, c)
            pd.testing.assert_series_equal(before[m], after)
    finally:
        data.y[zone], data.oracle[zone], data.forecast[zone] = y0, o0, f0


def test_second_implementation_of_the_regression_agrees(data):
    """An independent statsmodels fit must match ours to 0.1 MW on three gate origins."""
    for zone, c in [("JC", GATE[0]), ("DOM", GATE[1]), ("JC", GATE[3])]:
        hist, temp = data.history(zone, c), data.temperature(zone, c, "oracle")
        ours = lag_regression_temperature(hist, temp, c)
        df = lag_frame(hist, temp, c)
        other = pd.Series(np.nan, index=horizon_index(c))
        for hour in range(24):
            rows = df[df["hour"] == hour]
            train = rows[rows["is_train"]].dropna(subset=["y", "y_lag168", "T"]).copy()
            test = rows[~rows["is_train"]].copy()
            tbar = train["T"].mean()
            for part in (train, test):
                part["Tc"] = part["T"] - tbar
                part["dow"] = pd.Categorical(part["dow"], categories=range(7))
            fit = smf.ols("y ~ y_lag168 + C(dow) + hol + yearend + Tc + I(Tc**2)", train).fit()
            other.loc[test.index] = fit.predict(test).to_numpy()
        assert np.abs(ours - other).max() < 0.1


def test_row_ordering_over_the_ordering_gate_year():
    """Sanity of the baselines over the 52 Mondays before the gate set (never scored)."""
    path = ROOT / "results" / "ordering_gate" / "leaderboard.parquet"
    if not path.exists():
        pytest.skip("run harness.run and harness.score with `ordering_gate` first")
    lb = pd.read_parquet(path)
    assert (lb["n_windows"] >= 45).all()
    mae = lb.set_index(["model", "unique_id", "regime"])["mae"]
    for zone in PROTO["zones"]:
        for regime in ["oracle", "forecast"]:
            assert mae["lag_regression", zone, regime] < mae["seasonal_naive", zone, regime]
        assert (
            mae["lag_regression_temperature", zone, "oracle"]
            < mae["lag_regression", zone, "oracle"]
        )


def test_origin_sets_do_not_overlap():
    o, g, s = (origins(PROTO, k) for k in ("ordering_gate", "gate", "scored"))
    assert (len(o), len(g), len(s)) == (52, 6, 52)
    assert max(o) < min(g) and max(g) < min(s)
