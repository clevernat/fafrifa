"""Unit tests for the pure-NumPy index kernels.

These tests pin every ETCCDI kernel to hand-computed expected values on small
synthetic arrays, so the algorithmic core is verifiable with NumPy alone (no
xarray / xclim / scipy required). Run with ``pytest`` in CI, or directly with
``python tests/test_kernels.py`` in a minimal environment.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from sai_extremes import kernels as K  # noqa: E402


def test_count_thresholds():
    tx = np.array([26.0, 25.0, 24.9, 30.0, np.nan, 25.1])
    # SU: strictly > 25 -> {26, 30, 25.1} = 3
    assert K.count_gt(tx, 25.0) == 3
    tn = np.array([-1.0, 0.0, -0.001, 5.0])
    # FD: strictly < 0 -> {-1, -0.001} = 2
    assert K.count_lt(tn, 0.0) == 2
    pr = np.array([10.0, 9.99, 20.0, 0.0, 10.0])
    # R10mm: >= 10 -> {10, 20, 10} = 3
    assert K.count_ge(pr, 10.0) == 3
    # R20mm: >= 20 -> {20} = 1
    assert K.count_ge(pr, 20.0) == 1


def test_max_consecutive_run():
    # dry days mask for CDD: PR < 1mm
    pr = np.array([0.0, 0.0, 2.0, 0.0, 0.0, 0.0, 5.0])
    dry = pr < K.WET_DAY_MM
    assert K.max_consecutive_run(dry) == 3  # the trailing run of 3 zeros
    wet = pr >= K.WET_DAY_MM
    assert K.max_consecutive_run(wet) == 1
    assert K.max_consecutive_run(np.array([], dtype=bool)) == 0
    assert K.max_consecutive_run(np.zeros(4, dtype=bool)) == 0


def test_count_days_in_spells():
    # spells of >= 6 consecutive True
    m = np.array([1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1], dtype=bool)
    # first spell length 6 (counts), gap, second spell length 7 (counts) -> 13
    assert K.count_days_in_spells(m, min_len=6) == 13
    m2 = np.array([1, 1, 1, 1, 1, 0], dtype=bool)  # only 5 in a row -> 0
    assert K.count_days_in_spells(m2, min_len=6) == 0


def test_block_extremes():
    tx = np.array([3.0, 7.0, -2.0, np.nan, 5.0])
    assert K.block_max(tx) == 7.0   # TXx
    assert K.block_min(tx) == -2.0  # TXn
    assert np.isnan(K.block_max(np.array([np.nan, np.nan])))


def test_running_sum_max():
    pr = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 0.0, 0.0])
    # windows of 5: [1+2+3+4+5]=15, [2+3+4+5+0]=14, [3+4+5+0+0]=12 -> max 15
    assert K.running_sum_max(pr, window=5) == 15.0
    # too short
    assert np.isnan(K.running_sum_max(np.array([1.0, 2.0]), window=5))
    # a NaN inside invalidates only the windows that contain it
    pr2 = np.array([1.0, 2.0, np.nan, 4.0, 5.0, 6.0, 7.0])
    # only fully-valid 5-day window is the last one: 4+5+6+7? no -> [np.nan..],
    # valid window is indices 2..6 contains nan; 1..5 contains nan; 3..7? size7
    # windows start at 0,1,2 ; start2 = idx2..6 has nan; start1 idx1..5 has nan;
    # start0 idx0..4 has nan -> all contain nan -> NaN
    assert np.isnan(K.running_sum_max(pr2, window=5))


def test_precip_accumulation():
    pr = np.array([0.5, 1.0, 12.0, 0.0, 30.0, 0.9])
    # wet days (>=1): 1.0, 12.0, 30.0 -> PRCPTOT = 43
    assert K.wet_day_total(pr) == 43.0
    # SDII = 43 / 3 wet days
    assert abs(K.simple_daily_intensity(pr) - 43.0 / 3.0) < 1e-9
    # R95p-style total above threshold=11 on wet days: 12 + 30 = 42
    assert K.total_above_threshold(pr, thresh=11.0) == 42.0


def test_calendar_day_percentiles_and_exceedance():
    # Build a 3-year base period with a clean ramp so percentiles are predictable.
    rng = np.random.default_rng(0)
    years = 30
    doy = np.tile(np.arange(1, 366), years)            # 365-day calendar
    base = 10.0 + 5.0 * np.sin(2 * np.pi * doy / 365)  # seasonal cycle
    noise = rng.normal(0, 1.0, size=base.size)
    values = base + noise
    thr90 = K.calendar_day_percentiles(values, doy, p=90, half_window=2)
    # Threshold array covers all 366 day-of-year slots and is finite for 1..365.
    assert thr90.shape == (366,)
    assert np.all(np.isfinite(thr90[:365]))
    # By construction ~10% of base-period days exceed their own 90th pct.
    frac = K.exceedance_fraction(values, doy, thr90, mode="gt")
    assert 7.0 < frac < 13.0


def test_exceedance_fraction_exact():
    # Deterministic check of the exceedance kernel.
    doy = np.array([1, 1, 2, 2])
    values = np.array([5.0, 15.0, 0.0, 20.0])
    thr = np.full(366, np.nan)
    thr[0] = 10.0  # DOY 1 threshold
    thr[1] = 10.0  # DOY 2 threshold
    # gt: 15>10 (doy1), 20>10 (doy2) -> 2 of 4 -> 50%
    assert K.exceedance_fraction(values, doy, thr, mode="gt") == 50.0
    # lt: 5<10 (doy1), 0<10 (doy2) -> 2 of 4 -> 50%
    assert K.exceedance_fraction(values, doy, thr, mode="lt") == 50.0


def test_spell_days_vs_threshold():
    doy = np.arange(1, 11)
    values = np.array([20, 20, 20, 20, 20, 20, 20, 0, 0, 0], dtype=float)
    thr = np.full(366, 10.0)
    # first 7 days exceed -> spell length 7 >= 6 -> 7 days
    assert K.spell_days_vs_threshold(values, doy, thr, mode="gt", min_len=6) == 7


def _run_all():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    passed = 0
    for fn in fns:
        fn()
        print(f"  PASS  {fn.__name__}")
        passed += 1
    print(f"\n{passed}/{len(fns)} kernel tests passed.")


if __name__ == "__main__":
    _run_all()
