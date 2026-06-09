"""Region masks and seasonal selection for the mid-latitude winter analysis.

Track A focuses on Northern Hemisphere mid-latitude winter (DJF) extremes and
their link to the North Atlantic Oscillation and the sub-polar jet. These
helpers provide reproducible spatial masks and season selection so every figure
and index uses the same definitions.
"""
from __future__ import annotations

# Standard analysis boxes (lat_s, lat_n, lon_w, lon_e) in [-180,180) longitudes.
REGIONS = {
    "NH_midlat": (30.0, 60.0, -180.0, 180.0),       # zonal NH mid-latitudes
    "Euro_Atlantic": (30.0, 75.0, -90.0, 40.0),      # NAO / storm-track domain
    "North_Atlantic": (40.0, 65.0, -60.0, 0.0),
    "Mediterranean": (30.0, 45.0, -10.0, 40.0),      # southern-Europe drying
    "Northern_Europe": (50.0, 70.0, -10.0, 40.0),    # wetting signal
    "Eurasia_high": (50.0, 70.0, 40.0, 140.0),       # Jones et al. warming
}

# NAO station boxes (Hurrell-style PC/station NAO uses SLP gradients).
NAO_BOXES = {
    "Azores": (36.0, 40.0, -28.0, -20.0),
    "Iceland": (63.0, 70.0, -25.0, -10.0),
}

DJF = [12, 1, 2]


def select_season(ds, months=DJF):
    """Subset a dataset to the given months (default DJF)."""
    return ds.sel(time=ds["time.month"].isin(months))


def box_mask(ds, region: str):
    """Boolean mask for a named region box on the dataset's lat/lon grid."""
    lat_s, lat_n, lon_w, lon_e = REGIONS[region]
    m = (ds["lat"] >= lat_s) & (ds["lat"] <= lat_n) & \
        (ds["lon"] >= lon_w) & (ds["lon"] <= lon_e)
    return m


def subset_region(ds, region: str):
    """Slice a dataset to a named region box (assumes standardized coords)."""
    lat_s, lat_n, lon_w, lon_e = REGIONS[region]
    return ds.sel(lat=slice(lat_s, lat_n), lon=slice(lon_w, lon_e))


def area_weights(ds):
    """cos(latitude) area weights for spatial averaging."""
    import numpy as np
    w = np.cos(np.deg2rad(ds["lat"]))
    w.name = "area_weights"
    return w


def area_mean(da, ds=None):
    """cos-lat weighted spatial mean over (lat, lon)."""
    ref = ds if ds is not None else da
    w = area_weights(ref)
    return da.weighted(w).mean(dim=[d for d in ("lat", "lon") if d in da.dims])
