"""Produce the *real* indices dataset on the Reflective Cloud Hub.

This is the production entry point for Deliverable 2. It assumes the
climate-Python stack is installed (xarray, cftime, netCDF4, dask, s3fs/zarr)
and that ``config/catalog.yaml`` points at real Cloud Hub data.

Usage (on a Cloud Hub JupyterHub terminal)::

    python run_production.py --outdir indices_dataset \
        --scenarios G6-1.5K-SAI G6-1.5K-HiLLA

For each available model x scenario it writes ``etccdi_<MODEL>_<SCENARIO>.nc``
(CF-1.10). Percentile indices require a base-period dataset per model; supply
those by editing ``build_baselines`` for your Cloud Hub layout.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

PKG_SRC = Path(__file__).resolve().parents[2] / "deliverable-1-workflow" / "sai-extremes" / "src"
sys.path.insert(0, str(PKG_SRC))


def build_baselines(catalog):
    """Open the quasi-equilibrium reference run per model for percentile base periods.

    Returns {model: standardized_base_dataset}. Edit the scenario/URIs to match
    your Cloud Hub reference run (see DATA_CARD.md §4 on baseline choice).
    Returning an empty dict computes only the fixed (non-percentile) indices.
    """
    from sai_extremes.io import open_daily  # noqa: F401
    baselines = {}
    # Example (uncomment + point catalog at the reference run):
    # for model in catalog.models():
    #     baselines[model] = open_daily(model, "SSP2-4.5-ref", ["tasmax", "tasmin", "pr"])
    return baselines


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--outdir", default="indices_dataset")
    ap.add_argument("--scenarios", nargs="+", default=["G6-1.5K-SAI", "G6-1.5K-HiLLA"])
    ap.add_argument("--models", nargs="*", default=None)
    ap.add_argument("--indices", nargs="*", default=None)
    args = ap.parse_args()

    from sai_extremes.catalog import load_catalog
    from sai_extremes.pipeline import run_all

    cat = load_catalog()
    baselines = build_baselines(cat)
    run_all(scenarios=tuple(args.scenarios), models=args.models, outdir=args.outdir,
            base_by_model=baselines, catalog=cat, indices=args.indices, write=True)


if __name__ == "__main__":
    main()
