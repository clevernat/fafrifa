"""ETCCDI extremes indices as xarray-aware operators.

This module is the production layer: it wraps the pure-NumPy kernels in
:mod:`sai_extremes.kernels` with :func:`xarray.apply_ufunc` so each index is
computed gridpoint-by-gridpoint, year-by-year, over a standardized daily
``xarray.Dataset`` returned by :mod:`sai_extremes.io`.

Design
------
* Each index is registered in :data:`INDEX_REGISTRY` with the input variable it
  needs (``tasmax``/``tasmin``/``pr``), the kernel it calls, the output units,
  and CF-style metadata. Adding an index = adding one registry entry.
* Fixed-threshold and block-extreme indices need only a single dataset.
* Percentile-based indices (TX90p, TN10p, WSDI, CSDI, R95p, R99p) additionally
  need a base-period climatology; see :mod:`sai_extremes.percentiles`.

The numerically important code lives in the kernels and is unit-tested there;
this layer is orchestration. ``import xarray`` is deferred so that the kernels
and registry metadata can be imported in environments without xarray.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

import numpy as np

from . import kernels as K


@dataclass(frozen=True)
class IndexDef:
    """Declarative definition of one extremes index."""

    name: str
    long_name: str
    var: str                       # required input variable (CF name)
    units: str
    kind: str                      # 'count' | 'block' | 'accumulation' | 'percentile'
    description: str
    kernel: Optional[Callable] = None
    kwargs: Dict = field(default_factory=dict)
    requires_baseline: bool = False
    cell_methods: str = "time: "   # completed per-index below


# ---------------------------------------------------------------------------
# Registry of fixed-threshold and fixed-block indices (no baseline needed)
# ---------------------------------------------------------------------------
_DEG = "degC"

INDEX_REGISTRY: Dict[str, IndexDef] = {
    # --- Fixed-threshold temperature counts (annual day-counts) ---
    "SU": IndexDef("SU", "Summer days (TX > 25 degC)", "tasmax", "days", "count",
                   "Annual count of days with daily maximum temperature above 25 degC.",
                   kernel=K.count_gt, kwargs={"thresh": 25.0}, cell_methods="time: sum within years"),
    "ID": IndexDef("ID", "Icing days (TX < 0 degC)", "tasmax", "days", "count",
                   "Annual count of days with daily maximum temperature below 0 degC.",
                   kernel=K.count_lt, kwargs={"thresh": 0.0}, cell_methods="time: sum within years"),
    "FD": IndexDef("FD", "Frost days (TN < 0 degC)", "tasmin", "days", "count",
                   "Annual count of days with daily minimum temperature below 0 degC.",
                   kernel=K.count_lt, kwargs={"thresh": 0.0}, cell_methods="time: sum within years"),
    "TR": IndexDef("TR", "Tropical nights (TN > 20 degC)", "tasmin", "days", "count",
                   "Annual count of days with daily minimum temperature above 20 degC.",
                   kernel=K.count_gt, kwargs={"thresh": 20.0}, cell_methods="time: sum within years"),
    # --- Fixed-threshold precipitation counts ---
    "R10mm": IndexDef("R10mm", "Heavy precipitation days (PR >= 10 mm)", "pr", "days", "count",
                      "Annual count of days with precipitation >= 10 mm.",
                      kernel=K.count_ge, kwargs={"thresh": 10.0}, cell_methods="time: sum within years"),
    "R20mm": IndexDef("R20mm", "Very heavy precipitation days (PR >= 20 mm)", "pr", "days", "count",
                      "Annual count of days with precipitation >= 20 mm.",
                      kernel=K.count_ge, kwargs={"thresh": 20.0}, cell_methods="time: sum within years"),
    # --- Spell-length precipitation indices ---
    "CDD": IndexDef("CDD", "Consecutive dry days", "pr", "days", "count",
                    "Maximum number of consecutive days with precipitation < 1 mm.",
                    kernel=None, cell_methods="time: maximum within years"),
    "CWD": IndexDef("CWD", "Consecutive wet days", "pr", "days", "count",
                    "Maximum number of consecutive days with precipitation >= 1 mm.",
                    kernel=None, cell_methods="time: maximum within years"),
    # --- Fixed annual block extremes ---
    "TXx": IndexDef("TXx", "Annual maximum of daily maximum temperature", "tasmax", _DEG, "block",
                    "Warmest daily maximum temperature each year.",
                    kernel=K.block_max, cell_methods="time: maximum within years"),
    "TXn": IndexDef("TXn", "Annual minimum of daily maximum temperature", "tasmax", _DEG, "block",
                    "Coldest daily maximum temperature each year.",
                    kernel=K.block_min, cell_methods="time: minimum within years"),
    "TNx": IndexDef("TNx", "Annual maximum of daily minimum temperature", "tasmin", _DEG, "block",
                    "Warmest daily minimum temperature each year.",
                    kernel=K.block_max, cell_methods="time: maximum within years"),
    "TNn": IndexDef("TNn", "Annual minimum of daily minimum temperature", "tasmin", _DEG, "block",
                    "Coldest daily minimum temperature each year.",
                    kernel=K.block_min, cell_methods="time: minimum within years"),
    "Rx1day": IndexDef("Rx1day", "Annual maximum 1-day precipitation", "pr", "mm", "block",
                       "Maximum 1-day precipitation total each year.",
                       kernel=K.block_max, cell_methods="time: maximum within years"),
    "Rx5day": IndexDef("Rx5day", "Annual maximum consecutive 5-day precipitation", "pr", "mm", "block",
                       "Maximum 5-day running precipitation total each year.",
                       kernel=K.running_sum_max, kwargs={"window": 5}, cell_methods="time: maximum within years"),
    "PRCPTOT": IndexDef("PRCPTOT", "Annual total wet-day precipitation", "pr", "mm", "accumulation",
                        "Sum of precipitation on wet days (PR >= 1 mm) each year.",
                        kernel=K.wet_day_total, cell_methods="time: sum within years"),
    "SDII": IndexDef("SDII", "Simple daily intensity index", "pr", "mm/day", "accumulation",
                     "Mean wet-day (PR >= 1 mm) precipitation amount each year.",
                     kernel=K.simple_daily_intensity, cell_methods="time: mean within years"),
    # --- Percentile-based indices (need base-period climatology) ---
    "TX90p": IndexDef("TX90p", "Warm days (TX > 90th pct)", "tasmax", "%", "percentile",
                      "Percentage of days with TX above the calendar-day 90th percentile.",
                      requires_baseline=True, cell_methods="time: mean within years"),
    "TX10p": IndexDef("TX10p", "Cool days (TX < 10th pct)", "tasmax", "%", "percentile",
                      "Percentage of days with TX below the calendar-day 10th percentile.",
                      requires_baseline=True, cell_methods="time: mean within years"),
    "TN90p": IndexDef("TN90p", "Warm nights (TN > 90th pct)", "tasmin", "%", "percentile",
                      "Percentage of days with TN above the calendar-day 90th percentile.",
                      requires_baseline=True, cell_methods="time: mean within years"),
    "TN10p": IndexDef("TN10p", "Cold nights (TN < 10th pct)", "tasmin", "%", "percentile",
                      "Percentage of days with TN below the calendar-day 10th percentile.",
                      requires_baseline=True, cell_methods="time: mean within years"),
    "WSDI": IndexDef("WSDI", "Warm spell duration index", "tasmax", "days", "percentile",
                     "Annual count of days in spells of >= 6 consecutive days with TX > 90th pct.",
                     requires_baseline=True, cell_methods="time: sum within years"),
    "CSDI": IndexDef("CSDI", "Cold spell duration index", "tasmin", "days", "percentile",
                     "Annual count of days in spells of >= 6 consecutive days with TN < 10th pct.",
                     requires_baseline=True, cell_methods="time: sum within years"),
    "R95p": IndexDef("R95p", "Very wet day precipitation (> 95th pct)", "pr", "mm", "percentile",
                     "Annual total precipitation from days above the base-period 95th wet-day pct.",
                     requires_baseline=True, cell_methods="time: sum within years"),
    "R99p": IndexDef("R99p", "Extremely wet day precipitation (> 99th pct)", "pr", "mm", "percentile",
                     "Annual total precipitation from days above the base-period 99th wet-day pct.",
                     requires_baseline=True, cell_methods="time: sum within years"),
}

FIXED_INDICES: List[str] = [k for k, v in INDEX_REGISTRY.items() if not v.requires_baseline]
PERCENTILE_INDICES: List[str] = [k for k, v in INDEX_REGISTRY.items() if v.requires_baseline]


# ---------------------------------------------------------------------------
# xarray application helpers (deferred xarray import)
# ---------------------------------------------------------------------------

def _apply_per_year(da, func, **kwargs):
    """Apply a 1-D-time kernel to each calendar year of a DataArray.

    Returns a DataArray indexed by ``year``. ``da`` must have a ``time`` dim.
    """
    import xarray as xr

    def _wrap(arr1d):
        return func(arr1d, **kwargs)

    def _reduce(block):  # block: DataArray for one year
        return xr.apply_ufunc(
            _wrap, block,
            input_core_dims=[["time"]],
            output_core_dims=[[]],
            vectorize=True,
            dask="parallelized",
            output_dtypes=[float],
        )

    return da.groupby("time.year").map(_reduce)


def compute_fixed_index(ds, name: str):
    """Compute one fixed (non-percentile) index from a standardized dataset.

    ``ds`` is the daily dataset from :mod:`sai_extremes.io` (variables
    ``tasmax``/``tasmin`` in degC, ``pr`` in mm day-1). Returns a DataArray
    with dims ``(year, lat, lon)`` and CF metadata.
    """
    import xarray as xr  # noqa: F401

    if name not in INDEX_REGISTRY:
        raise KeyError(f"Unknown index '{name}'.")
    idx = INDEX_REGISTRY[name]
    if idx.requires_baseline:
        raise ValueError(f"{name} is percentile-based; use sai_extremes.percentiles.")

    da = ds[idx.var]

    if name == "CDD":
        mask = da < K.WET_DAY_MM
        out = _apply_per_year(mask, K.max_consecutive_run)
    elif name == "CWD":
        mask = da >= K.WET_DAY_MM
        out = _apply_per_year(mask, K.max_consecutive_run)
    else:
        out = _apply_per_year(da, idx.kernel, **idx.kwargs)

    out.name = name
    out.attrs.update(
        long_name=idx.long_name,
        units=idx.units,
        description=idx.description,
        cell_methods=idx.cell_methods,
        index_id=name,
        etccdi=str(name in _ETCCDI_27),
    )
    return out


# The 27 core ETCCDI indices (subset implemented here flagged for provenance).
_ETCCDI_27 = {
    "SU", "ID", "FD", "TR", "R10mm", "R20mm", "CDD", "CWD", "TXx", "TXn", "TNx",
    "TNn", "Rx1day", "Rx5day", "PRCPTOT", "SDII", "TX90p", "TX10p", "TN90p",
    "TN10p", "WSDI", "CSDI", "R95p", "R99p",
}


def list_indices(kind: Optional[str] = None) -> List[str]:
    """Return registered index names, optionally filtered by ``kind``."""
    if kind is None:
        return list(INDEX_REGISTRY)
    return [k for k, v in INDEX_REGISTRY.items() if v.kind == kind]
