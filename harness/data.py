"""Data access for the backtest. This module is the only place that decides what a
model may see at a cutoff (CLAUDE.md rules 1 to 4).

Timestamps are UTC. A load timestamp `ds` labels the hour ENDING at `ds`, so the
168 forecast hours for a cutoff `c` are c+1h .. c+168h, and calendar features are
taken from the local time at the start of the hour (`ds - 1h`).
"""

from __future__ import annotations

from pathlib import Path

import holidays
import numpy as np
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parent.parent
PROCESSED = ROOT / "data" / "processed"
H = pd.Timedelta(hours=1)

# Draft protocol-v1.2 regimes (not part of the frozen protocol; secondary rows only).
V12_REGIMES = ("oracle_era5", "forecast_ifs", "forecast_aifs")
V12_PARQUET = {
    "oracle_era5": "weather_oracle_era5.parquet",
    "forecast_ifs": "weather_forecast_ifs.parquet",
    "forecast_aifs": "weather_forecast_aifs.parquet",
}


def load_protocol() -> dict:
    return yaml.safe_load((ROOT / "protocol.yaml").read_text())


def origin_utc(local_date: str, tz: str) -> pd.Timestamp:
    """Local midnight at the start of `local_date`, as a UTC timestamp."""
    return pd.Timestamp(f"{local_date} 00:00", tz=tz).tz_convert("UTC")


def origins(proto: dict, which: str) -> list[pd.Timestamp]:
    """Cutoffs from protocol.yaml. `which` is "gate", "ordering_gate" or "scored"."""
    return [origin_utc(str(d), proto["timezone"]) for d in proto["origins"][which]]


def horizon_index(cutoff: pd.Timestamp, hours: int = 168) -> pd.DatetimeIndex:
    return pd.date_range(cutoff + H, periods=hours, freq="h")


def calendar(index: pd.DatetimeIndex, tz: str = "America/New_York") -> pd.DataFrame:
    """Calendar features from the local time at the start of each hour."""
    local = (index - H).tz_convert(tz)
    us = holidays.country_holidays("US", years=sorted(set(local.year)))
    dates = pd.Series(local.date, index=index)
    month, day = local.month, local.day
    return pd.DataFrame(
        {
            "hour": local.hour,
            "dow": local.day_of_week,  # Monday = 0
            "hol": dates.map(lambda d: d in us).astype(float).to_numpy(),
            "yearend": (((month == 12) & (day >= 24)) | ((month == 1) & (day <= 2))).astype(float),
        },
        index=index,
    )


class Data:
    def __init__(self) -> None:
        load = pd.read_parquet(PROCESSED / "load.parquet")
        oracle = pd.read_parquet(PROCESSED / "weather_oracle.parquet")
        forecast = pd.read_parquet(PROCESSED / "weather_forecast.parquet")
        self.y = {z: g.set_index("ds")["y"].sort_index() for z, g in load.groupby("unique_id")}
        self.oracle = {
            z: g.set_index("ds")["temperature_2m"].sort_index()
            for z, g in oracle.groupby("unique_id")
        }
        self.forecast = {
            z: g.pivot(index="ds", columns="lead_day", values="temperature_2m").sort_index()
            for z, g in forecast.groupby("unique_id")
        }

    def history(self, zone: str, cutoff: pd.Timestamp) -> pd.Series:
        """Load up to and including the cutoff. Nothing later."""
        return self.y[zone].loc[:cutoff]

    def actuals(self, zone: str, cutoff: pd.Timestamp) -> pd.Series:
        return self.y[zone].reindex(horizon_index(cutoff))

    def temperature(self, zone: str, cutoff: pd.Timestamp, regime: str) -> pd.Series:
        """Temperature a model may use: reanalysis up to the cutoff, then the
        regime's series for the 168 horizon hours. The series ends at cutoff+168h."""
        past = self.oracle[zone].loc[:cutoff]
        hz = horizon_index(cutoff)
        if regime == "oracle":
            future = self.oracle[zone].reindex(hz)
        elif regime == "forecast":
            lead_day = np.arange(len(hz)) // 24 + 1  # horizon day k uses previous_day{k}
            table = self.forecast[zone].reindex(hz)
            future = pd.Series(
                table.to_numpy()[np.arange(len(hz)), lead_day - 1], index=hz, dtype=float
            )
        elif regime in V12_REGIMES:
            return self._temperature_v12(zone, cutoff, regime)
        else:
            raise ValueError(f"unknown regime {regime!r}")
        return pd.concat([past, future]).rename("T")

    # ---- draft protocol-v1.2 weather regimes (drafts/protocol-v1.2_weather.yaml).
    # Loaded on first use, so the v1 regimes and their tests never need these files.

    def _load_v12(self) -> None:
        if hasattr(self, "era5"):
            return
        era5 = pd.read_parquet(PROCESSED / V12_PARQUET["oracle_era5"])
        self.era5 = {
            z: g.set_index("ds")["temperature_2m"].sort_index()
            for z, g in era5.groupby("unique_id")
        }
        self.forecast_v12 = {}
        for regime in ("forecast_ifs", "forecast_aifs"):
            fc = pd.read_parquet(PROCESSED / V12_PARQUET[regime])
            self.forecast_v12[regime] = {
                z: g.pivot(index="ds", columns="lead_day", values="temperature_2m").sort_index()
                for z, g in fc.groupby("unique_id")
            }

    def _temperature_v12(self, zone: str, cutoff: pd.Timestamp, regime: str) -> pd.Series:
        """ERA5 (the declared truth) up to the cutoff in every v1.2 regime. After it:
        ERA5 for oracle_era5; for forecast_ifs / forecast_aifs, horizon day k uses that
        model's previous_day{k} value, the same lead matching as the v1 forecast regime.
        Missing values stay missing; the per-regime drop rule handles them."""
        self._load_v12()
        past = self.era5[zone].loc[:cutoff]
        hz = horizon_index(cutoff)
        if regime == "oracle_era5":
            future = self.era5[zone].reindex(hz)
        else:
            lead_day = np.arange(len(hz)) // 24 + 1
            table = self.forecast_v12[regime][zone].reindex(index=hz, columns=range(1, 8))
            future = pd.Series(
                table.to_numpy()[np.arange(len(hz)), lead_day - 1], index=hz, dtype=float
            )
        return pd.concat([past, future]).rename("T")
