"""sai_extremes: an open, reproducible workflow for SAI mid-latitude extremes.

A prototype Deliverable for the Reflective SAI Uncertainty Database (Track A:
mid-latitude extreme winter weather response to SAI). Computes ETCCDI-style
climate extremes indices for the GeoMIP G6-1.5K-SAI and G6-1.5K-HiLLA scenarios
across four Earth system models, from a single, tested entry point.

Layers
------
* :mod:`sai_extremes.kernels`      - pure-NumPy index algorithms (unit-tested).
* :mod:`sai_extremes.indices`      - xarray operators for fixed/block indices.
* :mod:`sai_extremes.percentiles`  - percentile indices + Zhang (2005) bootstrap.
* :mod:`sai_extremes.io`           - pluggable backends (local/S3-NetCDF/Zarr).
* :mod:`sai_extremes.catalog`      - model/scenario/variable registry (YAML).
* :mod:`sai_extremes.regions`      - NH mid-latitude masks + DJF selection.
* :mod:`sai_extremes.pipeline`     - driver to produce the indices dataset.
* :mod:`sai_extremes.synthetic`    - synthetic data for tests/demo/CI.
"""
from __future__ import annotations

__version__ = "0.1.0"

# Lightweight imports only (no xarray) so `import sai_extremes` works anywhere.
from . import kernels  # noqa: F401
from .indices import (  # noqa: F401
    INDEX_REGISTRY,
    FIXED_INDICES,
    PERCENTILE_INDICES,
    list_indices,
)

__all__ = [
    "__version__",
    "kernels",
    "INDEX_REGISTRY",
    "FIXED_INDICES",
    "PERCENTILE_INDICES",
    "list_indices",
]
