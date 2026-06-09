"""Tests for the Zhang (2005) bootstrap bookkeeping (NumPy-only, runs anywhere)."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from sai_extremes import percentiles as P  # noqa: E402


def _toy_base(nyear=5, ndays=60, seed=0):
    rng = np.random.default_rng(seed)
    doy = np.tile(np.arange(1, ndays + 1), nyear)
    year = np.repeat(np.arange(2000, 2000 + nyear), ndays)
    values = 10 + 5 * np.sin(2 * np.pi * doy / ndays) + rng.normal(0, 1, doy.size)
    return values, doy, year


def test_out_of_base_runs_and_is_bounded():
    values, doy, year = _toy_base()
    rate = P.out_of_base_exceedance(values, doy, year, target_year=2002, p=90, mode="gt")
    assert 0.0 <= rate <= 100.0


def test_in_base_series_keys_and_average():
    values, doy, year = _toy_base()
    series = P.in_base_exceedance_series(values, doy, year, p=90, mode="gt")
    assert set(series) == set(range(2000, 2005))
    # Warm-tail (90th pct) exceedance averaged over base years is roughly 10%.
    mean_rate = float(np.mean(list(series.values())))
    assert 4.0 < mean_rate < 18.0


def test_bootstrap_excludes_target_year_spike():
    # If one year is anomalously hot, the out-of-base threshold (computed from the
    # OTHER years) should flag almost all of that year's days as exceedances.
    values, doy, year = _toy_base()
    values = values.copy()
    values[year == 2002] += 50.0  # huge warm anomaly in the target year only
    rate = P.out_of_base_exceedance(values, doy, year, target_year=2002, p=90, mode="gt")
    assert rate > 90.0


def _run_all():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"  PASS  {fn.__name__}")
    print(f"\n{len(fns)}/{len(fns)} percentile tests passed.")


if __name__ == "__main__":
    _run_all()
