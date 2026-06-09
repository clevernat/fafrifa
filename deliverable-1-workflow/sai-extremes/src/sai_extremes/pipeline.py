"""Driver: compute the full index set per model x scenario and write the dataset.

Two code paths share the same kernels:

* :func:`run_model_scenario` / :func:`run_all` -- the **production** path. Reads
  daily data via :mod:`sai_extremes.io`, computes fixed + percentile indices via
  the xarray operators, and writes a CF-compliant NetCDF per model x scenario.
  Requires the climate-Python stack (xarray, cftime, netCDF4/dask); runs on the
  Reflective Cloud Hub.

* :func:`compute_all_indices_numpy` -- a **portable** path that computes the
  index fields directly from NumPy arrays (a :func:`sai_extremes.synthetic`
  dict) using the same kernels, with no xarray dependency. Used by the demo to
  generate a Deliverable-2 dataset anywhere.

Both produce the identical index definitions; only the array engine differs.
"""
from __future__ import annotations

from typing import Dict, List, Optional

import numpy as np

from . import kernels as K
from .indices import FIXED_INDICES, PERCENTILE_INDICES, INDEX_REGISTRY

ALL_INDICES = FIXED_INDICES + PERCENTILE_INDICES


# ---------------------------------------------------------------------------
# Portable NumPy path (used by the demo / Deliverable 2 generation here)
# ---------------------------------------------------------------------------

def _fixed_index_field(daily: Dict, name: str) -> np.ndarray:
    """Compute one fixed index -> (nyear, nlat, nlon) array via kernels."""
    idx = INDEX_REGISTRY[name]
    var = daily[idx.var]                      # (ntime, nlat, nlon)
    years = daily["year"]
    uniq = np.unique(years)
    nlat, nlon = var.shape[1], var.shape[2]
    out = np.full((uniq.size, nlat, nlon), np.nan, dtype="float32")
    for yi, y in enumerate(uniq):
        sel = years == y
        block = var[sel]                       # (days, nlat, nlon)
        for i in range(nlat):
            for j in range(nlon):
                series = block[:, i, j]
                if name == "CDD":
                    out[yi, i, j] = K.max_consecutive_run(series < K.WET_DAY_MM)
                elif name == "CWD":
                    out[yi, i, j] = K.max_consecutive_run(series >= K.WET_DAY_MM)
                else:
                    out[yi, i, j] = idx.kernel(series, **idx.kwargs)
    return out


def _percentile_index_field(daily: Dict, base: Dict, name: str) -> np.ndarray:
    """Compute one percentile index -> (nyear, nlat, nlon) via kernels."""
    idx = INDEX_REGISTRY[name]
    years = daily["year"]
    uniq = np.unique(years)
    var = idx.var
    nlat = daily["lat"].size
    nlon = daily["lon"].size
    out = np.full((uniq.size, nlat, nlon), np.nan, dtype="float32")

    if name in ("R95p", "R99p"):
        p = 95.0 if name == "R95p" else 99.0
        for i in range(nlat):
            for j in range(nlon):
                bp = base["pr"][:, i, j]
                wet = bp[bp >= K.WET_DAY_MM]
                thr = np.percentile(wet, p) if wet.size else np.inf
                for yi, y in enumerate(uniq):
                    series = daily["pr"][years == y, i, j]
                    out[yi, i, j] = K.total_above_threshold(series, float(thr))
        return out

    # Temperature percentile indices
    p = 90.0 if name in ("TX90p", "TN90p", "WSDI") else 10.0
    mode = "gt" if p == 90.0 else "lt"
    b_doy = base["doy"]
    for i in range(nlat):
        for j in range(nlon):
            thr_doy = K.calendar_day_percentiles(base[var][:, i, j], b_doy, p, half_window=2)
            for yi, y in enumerate(uniq):
                sel = years == y
                series = daily[var][sel, i, j]
                d = daily["doy"][sel]
                if name in ("WSDI", "CSDI"):
                    out[yi, i, j] = K.spell_days_vs_threshold(series, d, thr_doy, mode=mode, min_len=6)
                else:
                    out[yi, i, j] = K.exceedance_fraction(series, d, thr_doy, mode=mode)
    return out


def compute_all_indices_numpy(
    daily: Dict,
    base: Optional[Dict] = None,
    indices: Optional[List[str]] = None,
) -> Dict:
    """Compute index fields for one synthetic daily dict.

    Returns a dict with ``years``, ``lat``, ``lon`` and one (nyear,nlat,nlon)
    field per index. Percentile indices are skipped if ``base`` is None.
    """
    indices = indices or ALL_INDICES
    result = {
        "model": daily["model"], "scenario": daily["scenario"],
        "years": np.unique(daily["year"]),
        "lat": daily["lat"], "lon": daily["lon"], "fields": {}, "attrs": {},
    }
    for name in indices:
        if INDEX_REGISTRY[name].requires_baseline:
            if base is None:
                continue
            field = _percentile_index_field(daily, base, name)
        else:
            field = _fixed_index_field(daily, name)
        result["fields"][name] = field
        result["attrs"][name] = {
            "long_name": INDEX_REGISTRY[name].long_name,
            "units": INDEX_REGISTRY[name].units,
        }
    return result


# ---------------------------------------------------------------------------
# Production xarray path
# ---------------------------------------------------------------------------

def run_model_scenario(model: str, scenario: str, *, base_ds=None,
                       indices: Optional[List[str]] = None, catalog=None,
                       chunks: Optional[Dict] = None):
    """Compute the index set for one model x scenario as an xarray.Dataset.

    Requires xarray + the I/O stack. ``base_ds`` is the standardized base-period
    dataset for percentile indices (omit to compute only fixed indices).
    """
    import xarray as xr  # noqa: F401

    from .io import open_daily
    from .indices import compute_fixed_index
    from .percentiles import compute_percentile_index

    indices = indices or ALL_INDICES
    need_baseline = any(INDEX_REGISTRY[n].requires_baseline for n in indices)
    variables = sorted({INDEX_REGISTRY[n].var for n in indices})

    ds = open_daily(model, scenario, variables, catalog=catalog,
                    **({"chunks": chunks} if chunks else {}))

    out = {}
    for name in indices:
        if INDEX_REGISTRY[name].requires_baseline:
            if base_ds is None:
                continue
            out[name] = compute_percentile_index(ds, base_ds, name)
        else:
            out[name] = compute_fixed_index(ds, name)
    result = xr.Dataset(out)
    result.attrs.update(
        title=f"ETCCDI extremes indices: {model} {scenario}",
        model=model, scenario=scenario,
        Conventions="CF-1.10",
        institution="Reflective (SAI Uncertainty Database, Track A prototype)",
        source="sai_extremes workflow",
        references="Zhang et al. (2011); Klein Tank et al. (2009)",
    )
    return result


def run_all(scenarios=("G6-1.5K-SAI", "G6-1.5K-HiLLA"), models=None,
            outdir="indices_dataset", base_by_model=None, catalog=None,
            indices=None, write=True):
    """Run every available model x scenario and (optionally) write NetCDF.

    Skips combinations flagged unavailable in the catalog. Returns the list of
    (model, scenario, dataset) computed.
    """
    from pathlib import Path

    from .catalog import load_catalog

    cat = catalog if catalog is not None else load_catalog()
    models = models or cat.models()
    base_by_model = base_by_model or {}
    Path(outdir).mkdir(parents=True, exist_ok=True)

    done = []
    for model in models:
        for scenario in scenarios:
            if not cat.is_available(model, scenario):
                print(f"skip {model}/{scenario}: not available")
                continue
            print(f"computing {model}/{scenario} ...")
            res = run_model_scenario(model, scenario, base_ds=base_by_model.get(model),
                                     indices=indices, catalog=cat)
            if write:
                fn = Path(outdir) / f"etccdi_{model}_{scenario}.nc"
                res.to_netcdf(fn)
                print(f"  wrote {fn}")
            done.append((model, scenario, res))
    return done
