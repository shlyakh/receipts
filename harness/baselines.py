"""Non-foundation baselines. Every model has the same signature:

    forecast(hist, temp, cutoff) -> pd.Series of 168 values indexed by horizon ds

`hist` is load up to the cutoff. `temp` is the regime's temperature series (through
cutoff+168h), or None for a model that uses no weather.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from harness.data import H, calendar, horizon_index

LAG = pd.Timedelta(hours=168)
TRAIN_DAYS = 365


def seasonal_naive(hist: pd.Series, temp: pd.Series | None, cutoff: pd.Timestamp) -> pd.Series:
    hz = horizon_index(cutoff)
    return pd.Series(hist.reindex(hz - LAG).to_numpy(), index=hz)


def lag_frame(hist: pd.Series, temp: pd.Series | None, cutoff: pd.Timestamp) -> pd.DataFrame:
    """Rows for the trailing 365 days plus the 168 horizon hours."""
    idx = pd.date_range(cutoff - pd.Timedelta(days=TRAIN_DAYS) + H, cutoff + LAG, freq="h")
    df = calendar(idx)
    df["y"] = hist.reindex(idx).to_numpy()  # missing over the horizon by construction
    df["y_lag168"] = hist.reindex(idx - LAG).to_numpy()
    if temp is not None:
        df["T"] = temp.reindex(idx).to_numpy()
    df["is_train"] = idx <= cutoff
    return df


def _design(df: pd.DataFrame, tbar: float | None) -> np.ndarray:
    cols = [np.ones(len(df)), df["y_lag168"].to_numpy()]
    cols += [(df["dow"] == k).to_numpy(float) for k in range(1, 7)]  # Monday is the base
    cols += [df["hol"].to_numpy(float), df["yearend"].to_numpy(float)]
    if tbar is not None:
        tc = df["T"].to_numpy() - tbar
        cols += [tc, tc**2]
    return np.column_stack(cols)


def _lag_regression(
    hist: pd.Series, temp: pd.Series | None, cutoff: pd.Timestamp, weather: bool
) -> pd.Series:
    df = lag_frame(hist, temp if weather else None, cutoff)
    needed = ["y", "y_lag168"] + (["T"] if weather else [])
    out = pd.Series(np.nan, index=horizon_index(cutoff))
    for hour in range(24):
        rows = df[df["hour"] == hour]
        train = rows[rows["is_train"]].dropna(subset=needed)
        test = rows[~rows["is_train"]]
        tbar = float(train["T"].mean()) if weather else None
        beta, *_ = np.linalg.lstsq(_design(train, tbar), train["y"].to_numpy(), rcond=None)
        out.loc[test.index] = _design(test, tbar) @ beta
    return out


def lag_regression(hist: pd.Series, temp: pd.Series | None, cutoff: pd.Timestamp) -> pd.Series:
    """24 per-hour OLS fits: 7-day lag, day of week, holiday, year-end. No weather."""
    return _lag_regression(hist, None, cutoff, weather=False)


def lag_regression_temperature(
    hist: pd.Series, temp: pd.Series | None, cutoff: pd.Timestamp
) -> pd.Series:
    """The headline comparator: the lag regression plus centred temperature and its square."""
    if temp is None:
        raise ValueError("lag_regression_temperature needs a temperature series")
    return _lag_regression(hist, temp, cutoff, weather=True)


# name -> (function, uses_weather)
MODELS = {
    "seasonal_naive": (seasonal_naive, False),
    "lag_regression": (lag_regression, False),
    "lag_regression_temperature": (lag_regression_temperature, True),
}
