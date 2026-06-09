"""Pure-NumPy computational kernels for ETCCDI-style climate extremes indices.

These kernels are the *algorithmic core* of the workflow. They depend only on
NumPy so that the index definitions can be unit-tested anywhere, with no heavy
geoscience stack required. The xarray-aware layer in :mod:`sai_extremes.indices`
wraps these kernels with :func:`xarray.apply_ufunc` (``vectorize=True``) so the
same, tested logic runs gridpoint-by-gridpoint over CMIP/GeoMIP data cubes.

Conventions
-----------
* Every kernel operates on a 1-D time series for a single grid cell / single
  block (typically one calendar year, or the whole base period for percentile
  estimation). Higher-dimensional application is the wrapper's job.
* Temperatures are in degrees Celsius unless a threshold is given in Kelvin.
  The xarray layer converts units before calling these kernels.
* Precipitation is a daily flux already converted to mm day-1.
* ``> `` / ``< `` vs ``>=`` / ``<=`` follow the ETCCDI definitions
  (Zhang et al., 2011, WIREs Clim. Change; Klein Tank et al., 2009, WMO-TD/1500).

Author: Track A internship workflow (Reflective SAI Uncertainty Database).
License: MIT.
"""
from __future__ import annotations

import numpy as np

WET_DAY_MM = 1.0  # ETCCDI wet-day threshold (mm day-1)

# ---------------------------------------------------------------------------
# Threshold-count kernels (used by SU, ID, FD, TR, R10mm, R20mm, ...)
# ---------------------------------------------------------------------------

def count_gt(arr: np.ndarray, thresh: float) -> float:
    """Number of days strictly greater than ``thresh`` (ignoring NaN)."""
    arr = np.asarray(arr, dtype=float)
    return float(np.nansum(arr > thresh))


def count_lt(arr: np.ndarray, thresh: float) -> float:
    """Number of days strictly less than ``thresh`` (ignoring NaN)."""
    arr = np.asarray(arr, dtype=float)
    return float(np.nansum(arr < thresh))


def count_ge(arr: np.ndarray, thresh: float) -> float:
    """Number of days >= ``thresh`` (ignoring NaN). Used for R10mm/R20mm."""
    arr = np.asarray(arr, dtype=float)
    return float(np.nansum(arr >= thresh))


# ---------------------------------------------------------------------------
# Spell / run-length kernels (CDD, CWD, WSDI, CSDI)
# ---------------------------------------------------------------------------

def max_consecutive_run(mask: np.ndarray) -> float:
    """Length of the longest run of True values in a boolean 1-D mask.

    NaNs in the source field should be resolved to False by the caller.
    """
    mask = np.asarray(mask, dtype=bool)
    if mask.size == 0:
        return 0.0
    best = run = 0
    for v in mask:
        run = run + 1 if v else 0
        if run > best:
            best = run
    return float(best)


def count_days_in_spells(mask: np.ndarray, min_len: int = 6) -> float:
    """Total number of days that belong to runs of length >= ``min_len``.

    This is the kernel behind the Warm/Cold Spell Duration Indices (WSDI/CSDI),
    which count the *number of days* in spells of at least six consecutive days
    over (TX90p) / under (TN10p) the calendar-day percentile threshold.
    """
    mask = np.asarray(mask, dtype=bool)
    n = mask.size
    if n == 0:
        return 0.0
    total = 0
    i = 0
    while i < n:
        if mask[i]:
            j = i
            while j < n and mask[j]:
                j += 1
            run = j - i
            if run >= min_len:
                total += run
            i = j
        else:
            i += 1
    return float(total)


# ---------------------------------------------------------------------------
# Block-extreme kernels (TXx, TXn, TNx, TNn, Rx1day, Rx5day)
# ---------------------------------------------------------------------------

def block_max(arr: np.ndarray) -> float:
    arr = np.asarray(arr, dtype=float)
    return float(np.nanmax(arr)) if np.any(~np.isnan(arr)) else np.nan


def block_min(arr: np.ndarray) -> float:
    arr = np.asarray(arr, dtype=float)
    return float(np.nanmin(arr)) if np.any(~np.isnan(arr)) else np.nan


def running_sum_max(arr: np.ndarray, window: int = 5) -> float:
    """Maximum of the moving ``window``-day running sum. Kernel behind Rx5day.

    A NaN-aware rolling sum is used: a window is only valid if it contains no
    missing values, matching the ETCCDI rule that Rx5day requires a complete
    5-day window.
    """
    a = np.asarray(arr, dtype=float)
    if a.size < window:
        return np.nan
    valid = ~np.isnan(a)
    filled = np.where(valid, a, 0.0)
    csum = np.concatenate(([0.0], np.cumsum(filled)))
    win_sum = csum[window:] - csum[:-window]
    cvalid = np.concatenate(([0], np.cumsum(valid.astype(int))))
    win_valid = (cvalid[window:] - cvalid[:-window]) == window
    if not np.any(win_valid):
        return np.nan
    return float(np.nanmax(np.where(win_valid, win_sum, np.nan)))


# ---------------------------------------------------------------------------
# Precipitation accumulation kernels (PRCPTOT, SDII, R95p, R99p)
# ---------------------------------------------------------------------------

def wet_day_total(arr: np.ndarray, wet_mm: float = WET_DAY_MM) -> float:
    """PRCPTOT: total precipitation on wet days (PR >= ``wet_mm``)."""
    arr = np.asarray(arr, dtype=float)
    wet = arr >= wet_mm
    return float(np.nansum(np.where(wet, arr, 0.0)))


def simple_daily_intensity(arr: np.ndarray, wet_mm: float = WET_DAY_MM) -> float:
    """SDII: mean precipitation amount on wet days."""
    arr = np.asarray(arr, dtype=float)
    wet = arr >= wet_mm
    n_wet = int(np.nansum(wet))
    if n_wet == 0:
        return 0.0
    return float(np.nansum(np.where(wet, arr, 0.0)) / n_wet)


def total_above_threshold(arr: np.ndarray, thresh: float, wet_mm: float = WET_DAY_MM) -> float:
    """Total precipitation from wet days whose amount exceeds ``thresh``.

    Kernel behind R95p / R99p: ``thresh`` is the 95th/99th percentile of
    wet-day precipitation over the base period.
    """
    arr = np.asarray(arr, dtype=float)
    sel = (arr >= wet_mm) & (arr > thresh)
    return float(np.nansum(np.where(sel, arr, 0.0)))


# ---------------------------------------------------------------------------
# Percentile-threshold estimation (base period, calendar-day window)
# ---------------------------------------------------------------------------

def calendar_day_percentiles(
    values: np.ndarray,
    doy: np.ndarray,
    p: float,
    half_window: int = 2,
) -> np.ndarray:
    """Percentile threshold for each day-of-year, pooled over a moving window.

    For each target day-of-year ``d`` (1..366) the ``p``-th percentile is taken
    over all base-period values whose day-of-year falls within
    ``[d - half_window, d + half_window]`` (a 5-day window for the default),
    pooled across all base-period years. This is the standard ETCCDI procedure
    for percentile-based temperature indices (Zhang et al., 2005, J. Climate).

    Parameters
    ----------
    values : 1-D array of the base-period daily values for one grid cell.
    doy : 1-D array of day-of-year (1..366) aligned with ``values``.
    p : percentile in [0, 100].
    half_window : half-width of the centred day-of-year window (days).

    Returns
    -------
    thresholds : array of length 366 (index 0 -> DOY 1, ... index 365 -> DOY 366).
    """
    values = np.asarray(values, dtype=float)
    doy = np.asarray(doy, dtype=int)
    out = np.full(366, np.nan)
    # Pre-bin values by day-of-year for speed and wrap-around handling.
    by_doy = {d: values[doy == d] for d in range(1, 367)}
    for d in range(1, 367):
        pool = []
        for off in range(-half_window, half_window + 1):
            dd = ((d - 1 + off) % 366) + 1  # wrap 1..366
            pool.append(by_doy.get(dd, np.empty(0)))
        pooled = np.concatenate(pool) if pool else np.empty(0)
        pooled = pooled[~np.isnan(pooled)]
        if pooled.size:
            out[d - 1] = np.percentile(pooled, p)
    return out


def exceedance_fraction(
    values: np.ndarray,
    doy: np.ndarray,
    thresholds_by_doy: np.ndarray,
    mode: str = "gt",
) -> float:
    """Fraction (in %) of days that exceed the per-day-of-year threshold.

    Kernel behind TX90p / TX10p / TN90p / TN10p. ``mode`` is ``"gt"`` for warm
    indices (value > threshold) or ``"lt"`` for cold indices (value < threshold).
    """
    values = np.asarray(values, dtype=float)
    doy = np.asarray(doy, dtype=int)
    thr = thresholds_by_doy[doy - 1]
    valid = ~np.isnan(values) & ~np.isnan(thr)
    n = int(np.sum(valid))
    if n == 0:
        return np.nan
    if mode == "gt":
        hits = np.sum((values > thr) & valid)
    elif mode == "lt":
        hits = np.sum((values < thr) & valid)
    else:
        raise ValueError("mode must be 'gt' or 'lt'")
    return float(100.0 * hits / n)


def spell_days_vs_threshold(
    values: np.ndarray,
    doy: np.ndarray,
    thresholds_by_doy: np.ndarray,
    mode: str = "gt",
    min_len: int = 6,
) -> float:
    """Days in spells of >= ``min_len`` consecutive days beyond the threshold.

    Kernel behind WSDI (``mode='gt'`` against the 90th pct of TX) and
    CSDI (``mode='lt'`` against the 10th pct of TN).
    """
    values = np.asarray(values, dtype=float)
    doy = np.asarray(doy, dtype=int)
    thr = thresholds_by_doy[doy - 1]
    if mode == "gt":
        mask = values > thr
    elif mode == "lt":
        mask = values < thr
    else:
        raise ValueError("mode must be 'gt' or 'lt'")
    mask = np.where(np.isnan(values) | np.isnan(thr), False, mask)
    return count_days_in_spells(mask, min_len=min_len)
