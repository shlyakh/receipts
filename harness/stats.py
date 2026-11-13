"""Error ratios with whole-week bootstrap intervals, and the primary outcome sentence.

    uv run --project core python -m harness.stats scored

Everything here follows protocol.yaml: ratio of mean window errors, paired resampling
of whole weeks, fixed seed and number of draws, 90% percentile interval, and the verdict
rule and pre-written sentences for the primary comparison.
Outputs: stats.parquet, stats.csv and (when the primary model has been run) primary.md.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from harness.data import ROOT, load_protocol  # noqa: E402

PRIMARY_MODEL = "chronos2_temperature"
DAY_COLS = [f"mae_day{k}" for k in range(1, 8)]


def ratio_ci(a: np.ndarray, b: np.ndarray, draws: int, seed: int) -> tuple[float, float, float]:
    """Ratio of mean errors with a 90% interval. `a` and `b` are per-week errors in the
    same week order; each draw resamples whole weeks and uses the same weeks for both."""
    rng = np.random.default_rng(seed)  # same seed for every comparison: same resampled weeks
    idx = rng.integers(0, len(a), size=(draws, len(a)))
    boot = a[idx].sum(axis=1) / b[idx].sum(axis=1)
    lo, hi = np.percentile(boot, [5, 95])
    return float(a.sum() / b.sum()), float(lo), float(hi)


def verdict(lo: float, hi: float, bar: float) -> str:
    if hi < 1 - bar:
        return "worth_switching"
    if lo > 1 + bar:
        return "regression_clearly_better"
    if lo >= 1 - bar and hi <= 1 + bar:
        return "practical_tie"
    return "inconclusive"


def main() -> None:
    which = sys.argv[1] if len(sys.argv) > 1 else ""
    if which not in ("gate", "ordering_gate", "scored"):
        sys.exit(__doc__)
    proto = load_protocol()
    draws, seed = proto["bootstrap"]["draws"], proto["bootstrap"]["seed"]
    base_name, bar = proto["baseline_model"], proto["primary_comparison"]["bar"]
    out = ROOT / "results" if which == "scored" else ROOT / "results" / which
    win = pd.read_parquet(out / "windows.parquet")
    wide = win.set_index(["unique_id", "regime", "cutoff", "model"]).sort_index()

    rows = []

    def compare(
        kind: str,
        zone: str,
        regime: str,
        a_model: str,
        b_model: str,
        a_regime: str | None = None,
        b_regime: str | None = None,
    ) -> None:
        a = wide.xs((zone, a_regime or regime), level=("unique_id", "regime")).xs(
            a_model, level="model"
        )
        b = wide.xs((zone, b_regime or regime), level=("unique_id", "regime")).xs(
            b_model, level="model"
        )
        assert a.index.equals(b.index), "arms must cover the same weeks"
        for col in ["mae", *DAY_COLS]:
            r, lo, hi = ratio_ci(a[col].to_numpy(), b[col].to_numpy(), draws, seed)
            rows.append(
                {
                    "kind": kind,
                    "unique_id": zone,
                    "regime": regime,
                    "model_a": a_model,
                    "model_b": b_model,
                    "metric": col,
                    "n_windows": len(a),
                    "ratio": r,
                    "ci90_low": lo,
                    "ci90_high": hi,
                }
            )

    models = sorted(win["model"].unique())
    for zone in proto["zones"]:
        for regime in ["forecast", "oracle"]:
            for m in models:
                if m != base_name:
                    compare("vs_baseline", zone, regime, m, base_name)
            # Weather gain: error with temperature / error without, same forecaster.
            for with_t, without_t in [
                ("lag_regression_temperature", "lag_regression"),
                ("chronos2_temperature", "chronos2"),
            ]:
                if with_t in models and without_t in models:
                    compare("weather_gain", zone, regime, with_t, without_t)
        # Cost of forecast weather: forecast-regime error / oracle-regime error.
        for m in models:
            if (win.loc[win["model"] == m, "weather"] == "temperature").all():
                compare("forecast_vs_oracle", zone, "forecast", m, m, "forecast", "oracle")

    stats = pd.DataFrame(rows)
    stats.to_parquet(out / "stats.parquet", index=False)
    stats.round(4).to_csv(out / "stats.csv", index=False)
    head = stats[stats["metric"] == "mae"].drop(columns="metric")
    print(head.round(3).to_string(index=False))

    prim = head[
        (head["kind"] == "vs_baseline")
        & (head["model_a"] == PRIMARY_MODEL)
        & (head["regime"] == proto["primary_comparison"]["regime"])
    ]
    if prim.empty:
        return
    fc = pd.read_parquet(out / "forecasts" / f"{PRIMARY_MODEL}.parquet")
    weights_date = pd.Timestamp(fc["weights_date"].iloc[0])
    sentences = proto["primary_comparison"]["outcome_sentences"]
    lines = [f"# Primary comparison ({which} set)", ""]
    for r in prim.itertuples():
        v = verdict(r.ci90_low, r.ci90_high, bar)
        cutoffs = win.loc[
            (win["model"] == PRIMARY_MODEL)
            & (win["unique_id"] == r.unique_id)
            & (win["regime"] == r.regime),
            "cutoff",
        ]
        text = " ".join(sentences[v].split()).format(
            zone=r.unique_id,
            ratio=f"{r.ratio:.3f}",
            low=f"{r.ci90_low:.3f}",
            high=f"{r.ci90_high:.3f}",
            n=r.n_windows,
        )
        leak = " ".join(proto["primary_comparison"]["leakage_statement"].split()).format(
            n_after=int((cutoffs > weights_date).sum()), n=r.n_windows
        )
        lines += [f"**{r.unique_id}: {v}.** {text} {leak}", ""]
    (out / "primary.md").write_text("\n".join(lines))
    print("\n" + "\n".join(lines))


if __name__ == "__main__":
    main()
