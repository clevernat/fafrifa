"""Circulation diagnostics for the Weeks 7-8 "why" analysis.

Where the extremes indices (Deliverable 2) say *what* happens to mid-latitude
winter weather under SAI vs HiLLA, these diagnostics explain *why*: they probe
the large-scale circulation that drives the extremes — the eddy-driven jet, the
storm track, atmospheric blocking, and the North Atlantic Oscillation.

As elsewhere in the package, the numerically important logic is in pure-NumPy
kernels (unit-tested here) and the xarray wrappers are thin orchestration so the
same diagnostics run over CMIP cubes on the Cloud Hub.

Diagnostics
-----------
* :func:`jet_lat_speed`        - eddy-driven jet latitude & speed (Woollings
                                 et al., 2010): max of the sector-mean low-level
                                 zonal wind profile.
* :func:`storm_track_intensity`- transient eddy activity as the temporal std of
                                 high-pass-filtered Z500 (a band-pass storm-track
                                 proxy).
* :func:`tm_blocking_frequency`- Tibaldi & Molteni (1990) instantaneous blocking
                                 frequency vs longitude from Z500 meridional
                                 gradients.
* :func:`nao_station_index`    - Hurrell-style station NAO from normalized SLP at
                                 the Azores and Iceland boxes.

Inputs are daily fields, CF names: ``ua`` (zonal wind, m s-1), ``zg`` (geopotential
height, m), ``psl`` (sea-level pressure, Pa). The Track A focus is DJF.
"""
from __future__ import annotations

from typing import Tuple

import numpy as np

# ---------------------------------------------------------------------------
# Jet latitude and speed (Woollings et al., 2010, QJRMS)
# ---------------------------------------------------------------------------

def jet_lat_speed(u_profile: np.ndarray, lat: np.ndarray,
                  parabolic: bool = True) -> Tuple[float, float]:
    """Jet latitude and speed from a 1-D zonal-wind latitude profile.

    ``u_profile`` is the (time-mean, sector-mean) low-level zonal wind as a
    function of ``lat``. The jet latitude is the latitude of the maximum; with
    ``parabolic=True`` a 3-point parabolic fit refines it to sub-grid precision
    (the standard Woollings approach), which matters because jet shifts of a
    degree or two are the signal of interest.
    """
    u = np.asarray(u_profile, dtype=float)
    lat = np.asarray(lat, dtype=float)
    if u.size == 0 or np.all(np.isnan(u)):
        return np.nan, np.nan
    k = int(np.nanargmax(u))
    jlat, jspeed = float(lat[k]), float(u[k])
    if parabolic and 0 < k < u.size - 1:
        y0, y1, y2 = u[k - 1], u[k], u[k + 1]
        denom = (y0 - 2 * y1 + y2)
        if denom != 0:
            delta = 0.5 * (y0 - y2) / denom        # in grid-index units
            # assume locally uniform lat spacing
            dlat = lat[k + 1] - lat[k - 1]
            jlat = float(lat[k] + delta * dlat / 2.0)
            jspeed = float(y1 - 0.25 * (y0 - y2) * delta)
    return jlat, jspeed


# ---------------------------------------------------------------------------
# Storm-track intensity (transient eddy activity)
# ---------------------------------------------------------------------------

def highpass_anomaly(series: np.ndarray, window: int = 10) -> np.ndarray:
    """Remove a centred running-mean (low-pass) to retain synoptic variability."""
    a = np.asarray(series, dtype=float)
    n = a.size
    if n < window:
        return a - np.nanmean(a)
    kernel = np.ones(window) / window
    low = np.convolve(a, kernel, mode="same")
    return a - low


def storm_track_intensity(z500_series: np.ndarray, window: int = 10) -> float:
    """Storm-track proxy: std of high-pass-filtered Z500 over time (one cell)."""
    hp = highpass_anomaly(z500_series, window=window)
    return float(np.nanstd(hp))


# ---------------------------------------------------------------------------
# Tibaldi & Molteni (1990) instantaneous blocking
# ---------------------------------------------------------------------------

def tm_blocked_at_lon(z_lat_profile: np.ndarray, lat: np.ndarray,
                      phi0: float = 60.0, dphi: float = 20.0,
                      deltas=(-5.0, 0.0, 5.0),
                      ghgn_thresh: float = -10.0) -> bool:
    """Tibaldi-Molteni blocking test at one longitude for one day.

    Given the Z500 profile vs latitude at a single longitude, the central
    latitude ``phi0`` is *blocked* if, for any of the latitude shifts ``deltas``:

        GHGS = (Z(phi0) - Z(phi0 - dphi)) / dphi          > 0
        GHGN = (Z(phi0 + dphi) - Z(phi0)) / dphi          < ghgn_thresh (m/deg)

    i.e. a reversal of the climatological westerly gradient to the south and a
    sufficiently strong easterly gradient to the north.
    """
    z = np.asarray(z_lat_profile, dtype=float)
    lat = np.asarray(lat, dtype=float)

    def zval(phi):
        return np.interp(phi, lat, z, left=np.nan, right=np.nan)

    for d in deltas:
        c = phi0 + d
        zn, z0, zs = zval(c + dphi), zval(c), zval(c - dphi)
        if np.any(np.isnan([zn, z0, zs])):
            continue
        ghgs = (z0 - zs) / dphi
        ghgn = (zn - z0) / dphi
        if ghgs > 0 and ghgn < ghgn_thresh:
            return True
    return False


def tm_blocking_frequency(z500_time_lat: np.ndarray, lat: np.ndarray,
                          **kw) -> float:
    """Blocking frequency (fraction of days blocked) at one longitude.

    ``z500_time_lat`` has shape (time, lat) — the Z500 profile through time at a
    single longitude. Returns the fraction of days flagged blocked.
    """
    z = np.asarray(z500_time_lat, dtype=float)
    if z.ndim != 2:
        raise ValueError("expected (time, lat) array")
    blocked = [tm_blocked_at_lon(z[t], lat, **kw) for t in range(z.shape[0])]
    return float(np.mean(blocked)) if blocked else np.nan


# ---------------------------------------------------------------------------
# Station NAO index (Hurrell-style)
# ---------------------------------------------------------------------------

def nao_station_index(psl_azores: np.ndarray, psl_iceland: np.ndarray) -> np.ndarray:
    """Normalized Azores-minus-Iceland SLP difference (per-time NAO index).

    Each station series is standardized (zero mean, unit std) over the input
    sample before differencing, following the station-based NAO definition.
    Positive = stronger Azores high / deeper Icelandic low (positive NAO).
    """
    a = np.asarray(psl_azores, dtype=float)
    i = np.asarray(psl_iceland, dtype=float)
    az = (a - np.nanmean(a)) / np.nanstd(a)
    ic = (i - np.nanmean(i)) / np.nanstd(i)
    return az - ic


# ---------------------------------------------------------------------------
# xarray wrappers (deferred import)
# ---------------------------------------------------------------------------

def jet_diagnostics(ds_ua, sector=(-60.0, 0.0), level=85000.0, var="ua"):
    """DJF eddy-driven jet latitude & speed from a daily zonal-wind dataset.

    ``ds_ua`` has ``ua`` on (time, lat, lon[, plev]); selects the Atlantic
    ``sector``, optional pressure ``level``, takes the DJF time-mean sector-mean
    profile and returns scalars ``jet_lat`` / ``jet_speed`` per year.
    """
    import xarray as xr  # noqa: F401
    from .regions import select_season

    da = ds_ua[var]
    if "plev" in da.dims:
        da = da.sel(plev=level, method="nearest")
    da = da.sel(lon=slice(*sector))
    da = select_season(da)
    prof = da.mean("lon")  # (time, lat)

    def _per_year(block):
        p = block.mean("time")  # (lat,)
        jl, js = jet_lat_speed(p.values, p["lat"].values)
        return xr.Dataset({"jet_lat": jl, "jet_speed": js})

    return prof.groupby("time.year").map(_per_year)


def blocking_frequency(ds_zg, level=50000.0, var="zg", lat_band=(30.0, 75.0)):
    """Tibaldi-Molteni blocking frequency vs longitude (DJF) from daily Z500."""
    import xarray as xr  # noqa: F401
    from .regions import select_season

    da = ds_zg[var]
    if "plev" in da.dims:
        da = da.sel(plev=level, method="nearest")
    da = select_season(da).sel(lat=slice(*lat_band))
    lat = da["lat"].values

    def _per_lon(col):  # col: (time, lat) at one lon
        return tm_blocking_frequency(col.transpose("time", "lat").values, lat)

    freq = xr.apply_ufunc(
        lambda a: np.array([tm_blocking_frequency(a[:, :, j], lat)
                            for j in range(a.shape[2])]),
        da, input_core_dims=[["time", "lat", "lon"]], output_core_dims=[["lon"]],
        dask="forbidden",
    )
    freq.name = "blocking_frequency"
    freq.attrs.update(long_name="TM90 instantaneous blocking frequency",
                      units="fraction", method="Tibaldi & Molteni (1990)")
    return freq
