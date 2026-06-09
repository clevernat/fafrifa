"""xarray integration tests (run in CI where the climate stack is installed).

These are skipped automatically if xarray/cftime are unavailable, so the
numpy-only kernel tests still run in a minimal environment. They check that:

* the xarray index operators agree with the pure-NumPy kernels on identical
  synthetic input (guards against divergence between the two layers), and
* the produced index Datasets have the expected dims, coords and CF metadata.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

xr = pytest.importorskip("xarray")
pytest.importorskip("cftime")

from sai_extremes import synthetic, kernels as K  # noqa: E402
from sai_extremes.indices import compute_fixed_index, FIXED_INDICES  # noqa: E402
from sai_extremes.percentiles import compute_percentile_index  # noqa: E402


@pytest.fixture(scope="module")
def daily_ds():
    d = synthetic.generate_daily("CESM", "G6-1.5K-SAI", years=(2060, 2062),
                                 nlat=3, nlon=4)
    return synthetic.to_xarray(d), d


@pytest.mark.parametrize("name", ["SU", "FD", "CDD", "TXx", "Rx5day", "PRCPTOT", "SDII"])
def test_fixed_index_matches_kernel(daily_ds, name):
    ds, d = daily_ds
    out = compute_fixed_index(ds, name).compute()
    assert set(out.dims) == {"year", "lat", "lon"}
    assert out.attrs["units"]  # metadata present
    # Compare one cell/year against a direct kernel call.
    yr = int(out["year"].values[0])
    from sai_extremes.indices import INDEX_REGISTRY
    var = INDEX_REGISTRY[name].var
    sel = d["year"] == yr
    series = d[var][sel, 0, 0]
    if name == "CDD":
        expected = K.max_consecutive_run(series < K.WET_DAY_MM)
    else:
        expected = INDEX_REGISTRY[name].kernel(series, **INDEX_REGISTRY[name].kwargs)
    got = float(out.sel(year=yr).isel(lat=0, lon=0).values)
    assert np.isclose(got, expected, equal_nan=True)


def test_all_fixed_indices_run(daily_ds):
    ds, _ = daily_ds
    for name in FIXED_INDICES:
        out = compute_fixed_index(ds, name).compute()
        assert out.name == name


def test_percentile_index_runs(daily_ds):
    ds, _ = daily_ds
    base = synthetic.to_xarray(
        synthetic.generate_daily("CESM", "baseline", years=(2050, 2053), nlat=3, nlon=4))
    for name in ["TX90p", "TN10p", "WSDI", "R95p"]:
        out = compute_percentile_index(ds, base, name).compute()
        assert set(out.dims) == {"year", "lat", "lon"}
        assert out.attrs["index_id"] == name
