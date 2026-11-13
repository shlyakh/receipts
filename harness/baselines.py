"""Non-foundation baselines. Every model has the same signature:

    forecast(hist, temp, cutoff) -> pd.Series of 168 values indexed by horizon ds

`hist` is load up to the cutoff. `temp` is the regime's temperature series (through
cutoff+168h), or None for a model that uses no weather.
"""

from __future__ import annotations

import holidays
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


LGBM_FEATURES = ["y_lag168", "hour", "dow", "hol", "yearend", "T"]
LGBM_PARAMS = {
    "n_estimators": 300,
    "learning_rate": 0.05,
    "num_leaves": 31,
    "min_child_samples": 20,
    "random_state": 20261112,
    "deterministic": True,
    "force_row_wise": True,
    "n_jobs": 1,
    "verbose": -1,
}


def lightgbm_temperature(
    hist: pd.Series, temp: pd.Series | None, cutoff: pd.Timestamp
) -> pd.Series:
    """One gradient-boosted model per origin on exactly the regression's inputs."""
    import lightgbm as lgb

    if temp is None:
        raise ValueError("lightgbm_temperature needs a temperature series")
    df = lag_frame(hist, temp, cutoff)
    train = df[df["is_train"]].dropna(subset=["y", "y_lag168", "T"])
    test = df[~df["is_train"]]
    model = lgb.LGBMRegressor(**LGBM_PARAMS).fit(train[LGBM_FEATURES], train["y"])
    pred = pd.Series(model.predict(test[LGBM_FEATURES]), index=test.index)
    # Same availability rule as the regression: no forecast without the 168-hour lag.
    return pred.where(test["y_lag168"].notna())


VANILLA_DAYS = 730  # "the most recent 24 months"


def _vanilla_design(
    idx: pd.DatetimeIndex, t: np.ndarray, tz: str = "America/New_York"
) -> np.ndarray:
    """Design matrix of Tao's Vanilla Benchmark as written in Ziel and Liu (2016), eq. 10 and 11:
    month, day of week, hour and day-of-week x hour as classes, and a cubic in temperature
    on its own, by month and by hour. No lagged load, no trend, no holiday term."""
    local = (idx - H).tz_convert(tz)  # calendar from the local time at the start of the hour
    month, dow, hour = local.month.to_numpy(), local.day_of_week.to_numpy(), local.hour.to_numpy()
    m = (month[:, None] == np.arange(1, 13)).astype(float)  # 12 month classes
    h = (hour[:, None] == np.arange(24)).astype(float)  # 24 hour classes
    dh = ((dow * 24 + hour)[:, None] == np.arange(168)).astype(float)  # day of week x hour
    x = t / 10.0  # degrees C / 10, for conditioning only; the fit is unchanged
    powers = [x, x**2, x**3]
    cols = [m, dh]  # dh spans the intercept, day of week and hour; lstsq handles the overlap with m
    cols += [m * p[:, None] for p in powers]  # T, T^2, T^3 by month (spans the plain cubic)
    cols += [h * p[:, None] for p in powers]  # T, T^2, T^3 by hour
    return np.column_stack(cols)


def _vanilla(
    hist: pd.Series, temp: pd.Series | None, cutoff: pd.Timestamp, trend: bool
) -> pd.Series:
    if temp is None:
        raise ValueError("the Vanilla benchmark needs a temperature series")
    hz = horizon_index(cutoff)
    train_idx = pd.date_range(cutoff - pd.Timedelta(days=VANILLA_DAYS) + H, cutoff, freq="h")
    y = hist.reindex(train_idx).to_numpy()
    t_train = temp.reindex(train_idx).to_numpy()
    ok = np.isfinite(y) & np.isfinite(t_train)

    def design(idx: pd.DatetimeIndex, t: np.ndarray) -> np.ndarray:
        x = _vanilla_design(idx, t)
        if trend:  # years since the start of the training window, continuing over the horizon
            years = np.asarray((idx - train_idx[0]) / pd.Timedelta(days=365))
            x = np.column_stack([x, years])
        return x

    beta, *_ = np.linalg.lstsq(design(train_idx[ok], t_train[ok]), y[ok], rcond=None)
    return pd.Series(design(hz, temp.reindex(hz).to_numpy()) @ beta, index=hz)


def vanilla_benchmark(hist: pd.Series, temp: pd.Series | None, cutoff: pd.Timestamp) -> pd.Series:
    """Tao's Vanilla Benchmark: the load-forecasting field's standard regression benchmark
    (GEFCom2012, 2014 and 2017), as written in Ziel and Liu (2016). One least-squares fit
    on the trailing 24 months, refitted at every origin. Protocol-v1.1, secondary."""
    return _vanilla(hist, temp, cutoff, trend=False)


def vanilla_benchmark_trend(
    hist: pd.Series, temp: pd.Series | None, cutoff: pd.Timestamp
) -> pd.Series:
    """The same benchmark plus a linear trend, the form reported for GEFCom2012."""
    return _vanilla(hist, temp, cutoff, trend=True)


# ---------------------------------------------------------------- competition-grade LightGBM
# Feature design after the BigDEAL Challenge 2022 entry (https://arxiv.org/abs/2305.05575,
# read on 2026-11-13): temperature and calendar only, no lagged load; hourly temperature
# lags of 1 to 48 h; rolling mean, max, min, median and std over 3 h, 1 day, 1 week and
# 1 month; daily ("Year-Month-Day") and month-hour aggregates; calendar with holiday name and
# days since and until a holiday; log target with a linear trend removed and added back.
# Our own code. Fixed before any run (drafts/protocol-v1.3_models.yaml); not tuned. The paper
# reports no hyperparameter values (it tuned with Optuna), so the values below are LightGBM's
# defaults except a fixed budget of 1,000 trees at learning rate 0.05.
COMP_DAYS = 730  # training window, the same as Vanilla
COMP_TEMP_LAGS = range(1, 49)
COMP_ROLL_HOURS = {"3h": 3, "1d": 24, "1w": 168, "1m": 720}
COMP_ROLL_STATS = ["mean", "max", "min", "median", "std"]
COMP_PARAMS = {
    "objective": "regression",  # L2, as in the entry's qualifying match
    "n_estimators": 1000,
    "learning_rate": 0.05,
    "num_leaves": 31,
    "min_child_samples": 20,
    "random_state": 20261112,
    "deterministic": True,
    "force_row_wise": True,
    "n_jobs": 1,
    "verbose": -1,
}


def _hol_name(name: str) -> str:
    """One base name per day: drop "(observed)" and keep the first of joined names."""
    return name.split("; ")[0].replace(" (observed)", "")


# Holiday names as a fixed integer code (0 = no holiday), the same at every origin.
_US_HOLIDAY_NAMES = sorted(
    {_hol_name(n) for n in holidays.country_holidays("US", years=range(2017, 2029)).values()}
)


def _comp_calendar(idx: pd.DatetimeIndex, tz: str = "America/New_York") -> pd.DataFrame:
    """Calendar from the local time at the start of each hour. No year term: the level is
    carried by the removed trend, and a year code cannot extrapolate."""
    local = (idx - H).tz_convert(tz)
    years = range(local.year.min() - 1, local.year.max() + 2)
    us = holidays.country_holidays("US", years=years)
    hol_dates = np.array(sorted(us), dtype="datetime64[D]")
    day = local.tz_localize(None).normalize().to_numpy().astype("datetime64[D]")
    nxt = hol_dates[np.searchsorted(hol_dates, day, side="left")]
    prv = hol_dates[np.searchsorted(hol_dates, day, side="right") - 1]
    names = [us.get(d) for d in local.date]
    code = {n: i + 1 for i, n in enumerate(_US_HOLIDAY_NAMES)}
    month = local.month.to_numpy()
    return pd.DataFrame(
        {
            "hour": local.hour,
            "dow": local.day_of_week,
            "month": month,
            "week": local.isocalendar().week.to_numpy().astype(int),
            "dom": local.day,
            "doy": local.day_of_year,
            "weekend": (local.day_of_week >= 5).astype(int),
            "week_of_month": (local.day.to_numpy() - 1) // 7 + 1,
            "season": (month % 12) // 3,  # 0 DJF, 1 MAM, 2 JJA, 3 SON
            "hol": np.array([n is not None for n in names], dtype=int),
            "hol_name": [code[_hol_name(n)] if n else 0 for n in names],
            "days_to_hol": (nxt - day).astype(int),
            "days_from_hol": (day - prv).astype(int),
        },
        index=idx,
    )


def _comp_features(
    temp: pd.Series, idx: pd.DatetimeIndex, mh_ref: pd.DatetimeIndex, tz: str = "America/New_York"
) -> pd.DataFrame:
    """Features for the rows `idx` from one temperature series. Lags and rolling statistics
    look back only; daily aggregates use the hours of the same local day; the month-hour
    mean is taken over the hours `mh_ref` (the training rows, all at or before the cutoff)."""
    back = pd.Timedelta(hours=max(*COMP_ROLL_HOURS.values(), *COMP_TEMP_LAGS))
    grid = pd.date_range(idx[0] - back, idx[-1], freq="h")
    t = temp.reindex(grid)
    cols = {"T": t}
    for k in COMP_TEMP_LAGS:
        cols[f"T_lag{k}"] = t.shift(k)
    for name, w in COMP_ROLL_HOURS.items():
        roll = t.rolling(w, min_periods=1)
        for stat in COMP_ROLL_STATS:
            cols[f"T_roll{name}_{stat}"] = getattr(roll, stat)()
    f = pd.DataFrame(cols).reindex(idx)
    day = (idx - H).tz_convert(tz).tz_localize(None).normalize()
    by_day = f["T"].groupby(day)
    for stat in ["mean", "max", "min", "median", "std"]:
        f[f"T_day_{stat}"] = by_day.transform(stat).to_numpy()
    f["T_day_ptp"] = f["T_day_max"] - f["T_day_min"]
    f["T_minus_day_mean"] = f["T"] - f["T_day_mean"]
    ref_local = (mh_ref - H).tz_convert(tz)
    mh = temp.reindex(mh_ref).groupby([ref_local.month, ref_local.hour]).mean()
    local = (idx - H).tz_convert(tz)
    keys = pd.MultiIndex.from_arrays([local.month, local.hour])
    f["T_monthhour_mean"] = mh.reindex(keys).to_numpy()
    f["T_minus_monthhour_mean"] = f["T"] - f["T_monthhour_mean"]
    return pd.concat([_comp_calendar(idx, tz), f], axis=1)


def lightgbm_competition(
    hist: pd.Series, temp: pd.Series | None, cutoff: pd.Timestamp
) -> pd.Series:
    """Competition-grade LightGBM after the BigDEAL 2022 entry: temperature and calendar
    features only (no lagged load), log target with a linear trend removed, one model per
    origin on the trailing 730 days, all 168 horizon hours predicted directly from the
    regime's temperature. Protocol-v1.3 (draft), secondary."""
    import lightgbm as lgb

    if temp is None:
        raise ValueError("lightgbm_competition needs a temperature series")
    train_idx = pd.date_range(cutoff - pd.Timedelta(days=COMP_DAYS) + H, cutoff, freq="h")
    hz = horizon_index(cutoff)
    y = hist.reindex(train_idx)
    ok = y.notna() & (y > 0)
    train_idx = train_idx[ok.to_numpy()]
    z = np.log(y[ok].to_numpy())
    # Linear trend in log load, years since the start of the training window.
    origin = cutoff - pd.Timedelta(days=COMP_DAYS)

    def years(idx: pd.DatetimeIndex) -> np.ndarray:
        return np.asarray((idx - origin) / pd.Timedelta(days=365))

    a = np.column_stack([np.ones(len(train_idx)), years(train_idx)])
    beta, *_ = np.linalg.lstsq(a, z, rcond=None)
    resid = z - a @ beta
    x_train = _comp_features(temp, train_idx, train_idx)
    x_hz = _comp_features(temp, hz, train_idx)
    model = lgb.LGBMRegressor(**COMP_PARAMS).fit(x_train, resid)
    trend_hz = beta[0] + beta[1] * years(hz)
    return pd.Series(np.exp(trend_hz + model.predict(x_hz[x_train.columns])), index=hz)


# Rows added after protocol-v1 carry the version that defined them. protocol-v1.3 is a
# draft (drafts/protocol-v1.3_models.yaml) until it is written, committed and tagged.
MODEL_PROTOCOL = {
    "vanilla_benchmark": "protocol-v1.1",
    "vanilla_benchmark_trend": "protocol-v1.1",
    "lightgbm_competition": "protocol-v1.3",
    # Runs in models_ff/ (models_ff/tabpfn_ts_v2.py), which writes the same label.
    "tabpfn_ts_v2_temperature": "protocol-v1.3",
}

# name -> (function, uses_weather)
MODELS = {
    "seasonal_naive": (seasonal_naive, False),
    "lag_regression": (lag_regression, False),
    "lag_regression_temperature": (lag_regression_temperature, True),
    "lightgbm_temperature": (lightgbm_temperature, True),
    "vanilla_benchmark": (vanilla_benchmark, True),
    "vanilla_benchmark_trend": (vanilla_benchmark_trend, True),
    "lightgbm_competition": (lightgbm_competition, True),
}
