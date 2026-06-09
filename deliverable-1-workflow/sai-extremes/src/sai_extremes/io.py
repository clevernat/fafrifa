"""Pluggable I/O layer for GeoMIP daily fields on the Reflective Cloud Hub.

Goal: give the indices code a single, stable entry point ::

    ds = open_daily(model="CESM", scenario="G6-1.5K-SAI", variables=["tasmax", "pr"])

regardless of whether the bytes live in local NetCDF, NetCDF on S3, or
cloud-optimized Zarr on Cloudflare R2. The function always returns a
*standardized* daily ``xarray.Dataset``:

* CF variable names ``tasmax`` / ``tasmin`` / ``pr``;
* temperatures in ``degC``, precipitation in ``mm day-1``;
* longitudes in ``[-180, 180)`` and sorted, latitudes ascending;
* a ``time`` coordinate with the model's native calendar preserved
  (no silent calendar conversion).

Backends are looked up from the catalog (:mod:`sai_extremes.catalog`). New
storage just means a new ``DataBackend`` subclass; the indices code is untouched.

The heavy I/O dependencies (xarray, s3fs, zarr, fsspec) are imported lazily so
that the catalog and unit conversions can be used / tested without them.
"""
from __future__ import annotations

import abc
from typing import Dict, Iterable, List, Optional

# Unit-conversion helpers are dependency-free and unit-tested.
K_TO_C = 273.15
# kg m-2 s-1 (CMIP flux) -> mm day-1
PR_FLUX_TO_MM_DAY = 86400.0


def kelvin_to_celsius(da):
    return da - K_TO_C


def flux_to_mm_per_day(da):
    return da * PR_FLUX_TO_MM_DAY


# Mapping from CF variable -> the per-model native name and native units.
# (Most CMIP6/GeoMIP archives use CMOR names already; kept explicit so a model
#  that deviates can be corrected in one place.)
CANONICAL_UNITS = {"tasmax": "degC", "tasmin": "degC", "pr": "mm day-1"}


def standardize(ds, drop_bnds: bool = True):
    """Apply name/unit/coordinate standardization to a raw daily dataset."""
    import numpy as np

    rename = {}
    for cand, target in {"tmax": "tasmax", "tmin": "tasmin", "precip": "pr",
                         "TREFHTMX": "tasmax", "TREFHTMN": "tasmin", "PRECT": "pr"}.items():
        if cand in ds.variables and target not in ds.variables:
            rename[cand] = target
    if rename:
        ds = ds.rename(rename)

    # Units
    for v in ("tasmax", "tasmin"):
        if v in ds and str(ds[v].attrs.get("units", "")).lower() in ("k", "kelvin"):
            ds[v] = kelvin_to_celsius(ds[v])
            ds[v].attrs["units"] = "degC"
    if "pr" in ds:
        u = str(ds["pr"].attrs.get("units", "")).lower()
        if u in ("kg m-2 s-1", "kg/m2/s", "kg m**-2 s**-1"):
            ds["pr"] = flux_to_mm_per_day(ds["pr"])
            ds["pr"].attrs["units"] = "mm day-1"

    # Longitudes to [-180, 180) and sorted; latitudes ascending.
    if "lon" in ds.coords:
        lon = ((ds["lon"] + 180) % 360) - 180
        ds = ds.assign_coords(lon=lon).sortby("lon")
    if "lat" in ds.coords:
        ds = ds.sortby("lat")

    if drop_bnds:
        ds = ds.drop_vars([v for v in ds.variables if v.endswith("_bnds") or v.endswith("_bounds")],
                          errors="ignore")
    ds.attrs.setdefault("standardized_by", "sai_extremes.io.standardize")
    return ds


# ---------------------------------------------------------------------------
# Backends
# ---------------------------------------------------------------------------

class DataBackend(abc.ABC):
    """Abstract storage backend. Returns a raw (un-standardized) dataset."""

    @abc.abstractmethod
    def open(self, uri: str, variables: Optional[Iterable[str]] = None, **kw):
        ...


class LocalNetCDFBackend(DataBackend):
    """Local NetCDF files (also used for the synthetic test fixtures)."""

    def open(self, uri, variables=None, **kw):
        import xarray as xr
        ds = xr.open_mfdataset(uri, combine="by_coords", **kw) if _is_glob(uri) \
            else xr.open_dataset(uri, **kw)
        return _maybe_subset(ds, variables)


class S3NetCDFBackend(DataBackend):
    """NetCDF on S3 (anonymous or credentialed) via fsspec/s3fs."""

    def __init__(self, anon: bool = True, client_kwargs: Optional[Dict] = None):
        self.anon = anon
        self.client_kwargs = client_kwargs or {}

    def open(self, uri, variables=None, **kw):
        import fsspec
        import xarray as xr
        mapper = fsspec.open_files(uri, anon=self.anon, **self.client_kwargs) \
            if _is_glob(uri) else [fsspec.open(uri, anon=self.anon, **self.client_kwargs)]
        files = [f.open() for f in mapper]
        ds = xr.open_mfdataset(files, combine="by_coords", **kw) if len(files) > 1 \
            else xr.open_dataset(files[0], **kw)
        return _maybe_subset(ds, variables)


class ZarrBackend(DataBackend):
    """Cloud-optimized Zarr (e.g. Cloudflare R2 / S3). The fast path.

    Per the June 4 check-in: John & Alistair maintain cloud-optimized Zarr
    versions of the CESM data; switch the catalog backend to ``zarr`` when S3
    NetCDF reads become the bottleneck. No change to the indices code required.
    """

    def __init__(self, storage_options: Optional[Dict] = None):
        self.storage_options = storage_options or {"anon": True}

    def open(self, uri, variables=None, **kw):
        import xarray as xr
        ds = xr.open_zarr(uri, storage_options=self.storage_options,
                          consolidated=kw.pop("consolidated", True), **kw)
        return _maybe_subset(ds, variables)


_BACKENDS = {
    "local": LocalNetCDFBackend,
    "s3-netcdf": S3NetCDFBackend,
    "zarr": ZarrBackend,
}


def get_backend(kind: str, **kwargs) -> DataBackend:
    if kind not in _BACKENDS:
        raise KeyError(f"Unknown backend '{kind}'. Options: {list(_BACKENDS)}")
    return _BACKENDS[kind](**kwargs)


def _is_glob(uri) -> bool:
    return isinstance(uri, str) and any(c in uri for c in "*?[")


def _maybe_subset(ds, variables):
    if variables is None:
        return ds
    keep = [v for v in variables if v in ds.variables]
    aux = [v for v in ds.variables if v.endswith(("_bnds", "_bounds")) or v in ("lat", "lon", "time")]
    return ds[list(dict.fromkeys(keep + aux))]


# ---------------------------------------------------------------------------
# High-level entry point
# ---------------------------------------------------------------------------

def open_daily(model: str, scenario: str, variables: List[str],
               catalog=None, standardize_ds: bool = True, **open_kw):
    """Open and standardize daily fields for one model x scenario.

    Looks up the backend + URIs in the catalog, opens each requested variable,
    merges, and standardizes names/units/coords. Raises a clear error if the
    requested model x scenario combination is not available (not every model
    ran every scenario; see the catalog ``available`` flags).
    """
    from .catalog import load_catalog

    cat = catalog if catalog is not None else load_catalog()
    entry = cat.entry(model, scenario)
    backend = get_backend(entry["backend"], **entry.get("backend_kwargs", {}))

    import xarray as xr
    datasets = []
    for var in variables:
        if var not in entry["uris"]:
            raise KeyError(
                f"Variable '{var}' not catalogued for {model}/{scenario}. "
                f"Have: {sorted(entry['uris'])}.")
        datasets.append(backend.open(entry["uris"][var], variables=[var], **open_kw))
    ds = xr.merge(datasets, compat="override", join="outer")
    ds.attrs.update(model=model, scenario=scenario, source_backend=entry["backend"])
    return standardize(ds) if standardize_ds else ds
