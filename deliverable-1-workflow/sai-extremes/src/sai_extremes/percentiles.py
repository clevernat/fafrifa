"""Percentile-based extremes indices with the Zhang et al. (2005) bootstrap.

Percentile temperature indices (TX90p, TX10p, TN90p, TN10p, WSDI, CSDI) compare
each day against a calendar-day percentile estimated over a fixed *base period*.
Naively counting exceedances introduces an inhomogeneity between years inside
and outside the base period, because each base-period day helped define its own
threshold. Zhang et al. (2005, J. Climate, doi:10.1175/JCLI3366.1) remove this
with an out-of-base bootstrap: for each base-period year ``y``, the threshold is
recomputed from the *other* ``n_base - 1`` years, with one of those years
duplicated to keep the sample size constant; the exceedance rate for ``y`` is
averaged over the ``n_base - 1`` resamples.

Precipitation percentile indices (R95p, R99p) use a single base-period
percentile of *wet-day* amounts (no calendar-day window, no bootstrap), per the
ETCCDI convention.

The numerically critical pieces (calendar-day percentile, exceedance fraction,
spell counting, wet-day totals) live in :mod:`sai_extremes.kernels` and are
unit-tested there. This module provides the base-period bookkeeping and the
xarray orchestration.
"""
from __future__ import annotations

from typing import Dict

import numpy as np

from . import kernels as K
from .indices import INDEX_REGISTRY


# ---------------------------------------------------------------------------
# NumPy-testable bootstrap core (operates on one grid cell)
# ---------------------------------------------------------------------------

def out_of_base_exceedance(
    values: np.ndarray,
    doy: np.ndarray,
    year: np.ndarray,
    target_year: int,
    p: float,
    mode: str = "gt",
    half_window: int = 2,
) -> float:
    """Zhang (2005) out-of-base exceedance rate (%) for one base-period year.

    For ``target_year`` inside the base period, recompute the calendar-day
    percentile from the remaining base years; for each remaining year ``r``,
    duplicate ``r`` to restore the original year count, estimate thresholds,
    and score the days of ``target_year`` against them. Return the mean
    exceedance fraction over the ``n_base - 1`` resamples.
    """
    years = np.unique(year)
    others = years[years != target_year]
    if others.size == 0:
        # Single-year base period: fall back to in-base estimate.
        thr = K.calendar_day_percentiles(values, doy, p, half_window)
        sel = year == target_year
        return K.exceedance_fraction(values[sel], doy[sel], thr, mode)

    sel_t = year == target_year
    v_t, d_t = values[sel_t], doy[sel_t]
    rates = []
    for r in others:
        # base = all "other" years, with year r duplicated
        sel_base = np.isin(year, others)
        v_base = np.concatenate([values[sel_base], values[year == r]])
        d_base = np.concatenate([doy[sel_base], doy[year == r]])
        thr = K.calendar_day_percentiles(v_base, d_base, p, half_window)
        rates.append(K.exceedance_fraction(v_t, d_t, thr, mode))
    return float(np.nanmean(rates))


def in_base_exceedance_series(
    values: np.ndarray,
    doy: np.ndarray,
    year: np.ndarray,
    p: float,
    mode: str = "gt",
    half_window: int = 2,
) -> Dict[int, float]:
    """Per-year exceedance (%) over the base period using the bootstrap."""
    out = {}
    for y in np.unique(year):
        out[int(y)] = out_of_base_exceedance(values, doy, year, int(y), p, mode, half_window)
    return out


# ---------------------------------------------------------------------------
# xarray orchestration (deferred xarray import)
# ---------------------------------------------------------------------------

def _doy_array(time):
    """Day-of-year (1..366) for an xarray time coordinate, calendar-aware."""
    return time.dt.dayofyear


def base_period_temperature_thresholds(ds_base, var: str, p: float, half_window: int = 2):
    """Calendar-day percentile thresholds (lat, lon, dayofyear) over the base period.

    Used for *out-of-base* years (the analysis period); in-base years should use
    :func:`out_of_base_exceedance` via :func:`compute_percentile_index`.
    """
    import xarray as xr

    da = ds_base[var]
    doy = _doy_array(da["time"])

    def _per_cell(vals, dvals):
        return K.calendar_day_percentiles(vals, dvals.astype(int), p, half_window)

    thr = xr.apply_ufunc(
        _per_cell, da, doy,
        input_core_dims=[["time"], ["time"]],
        output_core_dims=[["dayofyear"]],
        vectorize=True,
        dask="parallelized",
        output_dtypes=[float],
        dask_gufunc_kwargs={"output_sizes": {"dayofyear": 366}},
    )
    thr = thr.assign_coords(dayofyear=np.arange(1, 367))
    return thr


def compute_percentile_index(ds_analysis, ds_base, name: str, half_window: int = 2):
    """Compute a percentile-based index over the analysis period.

    Parameters
    ----------
    ds_analysis : standardized daily dataset for the years being analysed.
    ds_base : standardized daily dataset for the base period (e.g. a reference
        baseline run at matched global-mean temperature; see the data card).
    name : one of TX90p/TX10p/TN90p/TN10p/WSDI/CSDI/R95p/R99p.

    Notes
    -----
    * Temperature indices use a 5-day calendar-day window and the Zhang (2005)
      bootstrap for any analysis years that overlap the base period.
    * R95p/R99p use a single base-period wet-day percentile.
    """
    import xarray as xr

    idx = INDEX_REGISTRY[name]
    if not idx.requires_baseline:
        raise ValueError(f"{name} is not percentile-based.")

    # ---- Precipitation percentile indices -------------------------------
    if name in ("R95p", "R99p"):
        p = 95.0 if name == "R95p" else 99.0
        pr_base = ds_base["pr"]
        wet = pr_base.where(pr_base >= K.WET_DAY_MM)
        thr = wet.quantile(p / 100.0, dim="time")  # (lat, lon)

        def _total_above(arr, t):
            return K.total_above_threshold(arr, float(t))

        out = ds_analysis["pr"].groupby("time.year").map(
            lambda blk: xr.apply_ufunc(
                _total_above, blk, thr,
                input_core_dims=[["time"], []],
                vectorize=True, dask="parallelized", output_dtypes=[float],
            )
        )
        out.name = name
        out.attrs.update(long_name=idx.long_name, units=idx.units,
                         description=idx.description, cell_methods=idx.cell_methods,
                         index_id=name, base_percentile=p)
        return out

    # ---- Temperature percentile indices ---------------------------------
    var = idx.var
    p = 90.0 if name in ("TX90p", "TN90p", "WSDI") else 10.0
    mode = "gt" if p == 90.0 else "lt"

    thr = base_period_temperature_thresholds(ds_base, var, p, half_window)  # (...,dayofyear)
    doy_a = _doy_array(ds_analysis[var]["time"]).astype(int)

    if name in ("WSDI", "CSDI"):
        def _spell(vals, dvals, thr_doy):
            return K.spell_days_vs_threshold(vals, dvals.astype(int), thr_doy, mode=mode, min_len=6)

        out = ds_analysis[var].groupby("time.year").map(
            lambda blk: xr.apply_ufunc(
                _spell, blk, _doy_array(blk["time"]).astype(int), thr,
                input_core_dims=[["time"], ["time"], ["dayofyear"]],
                vectorize=True, dask="parallelized", output_dtypes=[float],
            )
        )
    else:  # TX90p / TX10p / TN90p / TN10p
        def _frac(vals, dvals, thr_doy):
            return K.exceedance_fraction(vals, dvals.astype(int), thr_doy, mode=mode)

        out = ds_analysis[var].groupby("time.year").map(
            lambda blk: xr.apply_ufunc(
                _frac, blk, _doy_array(blk["time"]).astype(int), thr,
                input_core_dims=[["time"], ["time"], ["dayofyear"]],
                vectorize=True, dask="parallelized", output_dtypes=[float],
            )
        )

    out.name = name
    out.attrs.update(long_name=idx.long_name, units=idx.units,
                     description=idx.description, cell_methods=idx.cell_methods,
                     index_id=name, base_percentile=p,
                     bootstrap="Zhang et al. (2005) for in-base years")
    return out
