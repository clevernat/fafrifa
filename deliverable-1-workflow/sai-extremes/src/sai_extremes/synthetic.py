"""Synthetic GeoMIP-shaped daily data for tests, demos and CI.

Generates physically plausible daily ``tasmax``/``tasmin``/``pr`` on a small
lat/lon grid with a seasonal cycle, latitudinal gradient, weather noise and a
prescribed inter-model / inter-scenario signal. This lets the whole workflow be
exercised end-to-end with zero external data, and lets the demo reproduce the
*structure* of the real indices dataset (Deliverable 2).

Two entry points:

* :func:`generate_daily` -> plain NumPy dict (no heavy deps; used by the
  portable demo and by kernel-level integration checks).
* :func:`to_xarray` -> wraps the dict as an ``xarray.Dataset`` matching the
  standardized schema from :mod:`sai_extremes.io` (used by the notebook and the
  xarray integration tests).

The injected signal is a caricature, not a model emulator: it encodes the
*sign* of the documented mid-latitude responses (e.g. tropical-injection SAI
warms the Eurasian winter and dries the Mediterranean relative to HiLLA) so the
demo figures are interpretable, while inter-model spread is randomized.
"""
from __future__ import annotations

from typing import Dict

import numpy as np

# Caricatured winter mid-latitude signal (degC for temperature, fraction for pr)
# relative to a neutral baseline, by scenario. Encodes the Jones et al. (2021) /
# project-plan narrative: tropical-injection SAI -> +NAO-like Eurasian warming &
# Mediterranean drying; HiLLA -> weaker/полward-shifted, less tropical heating.
SCENARIO_SIGNAL = {
    "G6-1.5K-SAI":   {"warm_eurasia": 1.2, "med_dry": -0.15, "neur_wet": 0.12},
    "G6-1.5K-HiLLA": {"warm_eurasia": 0.4, "med_dry": -0.04, "neur_wet": 0.05},
    "baseline":      {"warm_eurasia": 0.0, "med_dry": 0.0,   "neur_wet": 0.0},
}

MODEL_SEED = {"CESM": 10, "MIROC": 20, "UKESM": 30, "E3SMv3": 40, "REF": 99}


def generate_daily(
    model: str = "CESM",
    scenario: str = "G6-1.5K-SAI",
    years=(2050, 2069),
    nlat: int = 12,
    nlon: int = 24,
    lat_range=(20.0, 80.0),
    lon_range=(-100.0, 60.0),
    calendar_days: int = 365,
    seed: int = None,
) -> Dict[str, np.ndarray]:
    """Generate one synthetic daily dataset as a dict of NumPy arrays."""
    y0, y1 = years
    nyear = y1 - y0 + 1
    base_seed = (MODEL_SEED.get(model, 0) * 1000
                 + (hash(scenario) % 97) * 7
                 + (seed or 0))
    rng = np.random.default_rng(base_seed)

    lat = np.linspace(lat_range[0], lat_range[1], nlat)
    lon = np.linspace(lon_range[0], lon_range[1], nlon)
    doy = np.tile(np.arange(1, calendar_days + 1), nyear)
    year = np.repeat(np.arange(y0, y1 + 1), calendar_days)
    ntime = doy.size

    # Seasonal cycle (NH): coldest near DOY 15, warmest near DOY 200.
    seas = -np.cos(2 * np.pi * (doy - 15) / calendar_days)        # -1..1
    lat_grad = (lat[:, None] - 50.0) * -0.6                       # colder poleward

    sig = SCENARIO_SIGNAL.get(scenario, SCENARIO_SIGNAL["baseline"])
    # Spatial signal patterns
    eurasia = ((lat[:, None] >= 50) & (lon[None, :] >= 40)).astype(float)
    med = ((lat[:, None] <= 45) & (lat[:, None] >= 30) &
           (lon[None, :] >= -10) & (lon[None, :] <= 40)).astype(float)
    neur = ((lat[:, None] >= 50) & (lon[None, :] >= -10) & (lon[None, :] <= 40)).astype(float)
    winter = (np.cos(2 * np.pi * (doy - 15) / calendar_days) + 1) / 2  # 1 in DJF

    tasmax = np.empty((ntime, nlat, nlon), dtype="float32")
    tasmin = np.empty_like(tasmax)
    pr = np.empty_like(tasmax)

    mean_field = (12.0 + 15.0 * seas[:, None, None]
                  + lat_grad[None, :, :])
    warm_signal = sig["warm_eurasia"] * eurasia[None, :, :] * winter[:, None, None]
    weather = rng.normal(0, 4.0, size=tasmax.shape)
    tmean = mean_field + warm_signal + weather
    dtr = 6.0 + 2.0 * rng.random(size=tasmax.shape)  # diurnal temp range
    tasmax[:] = tmean + dtr / 2
    tasmin[:] = tmean - dtr / 2

    # Precip: gamma-like wet days, modulated by scenario drying/wetting.
    base_rate = 3.0 + 2.0 * (1 - np.abs(seas))[:, None, None]
    rate = base_rate * (1 + sig["med_dry"] * med[None, :, :] * winter[:, None, None]
                        + sig["neur_wet"] * neur[None, :, :] * winter[:, None, None])
    rate = np.clip(rate, 0.2, None)
    wet = rng.random(size=pr.shape) < 0.35
    amounts = rng.gamma(shape=1.3, scale=rate, size=pr.shape)
    pr[:] = np.where(wet, amounts, 0.0).astype("float32")

    return {
        "model": model, "scenario": scenario,
        "lat": lat.astype("float64"), "lon": lon.astype("float64"),
        "doy": doy.astype("int32"), "year": year.astype("int32"),
        "tasmax": tasmax, "tasmin": tasmin, "pr": pr,
        "units": {"tasmax": "degC", "tasmin": "degC", "pr": "mm day-1"},
    }


# Circulation signal by scenario (NH winter). Encodes the documented direction:
# tropical/subtropical-injection SAI -> more positive NAO, poleward & stronger
# eddy-driven jet, fewer blocks; HiLLA -> weaker (less tropical strat. heating).
CIRC_SIGNAL = {
    "G6-1.5K-SAI":   {"nao": 1.0, "jet_shift": 2.5, "jet_boost": 2.0, "block": -0.30},
    "G6-1.5K-HiLLA": {"nao": 0.3, "jet_shift": 0.7, "jet_boost": 0.6, "block": -0.08},
    "baseline":      {"nao": 0.0, "jet_shift": 0.0, "jet_boost": 0.0, "block": 0.0},
}


def generate_circulation_daily(
    model: str = "CESM",
    scenario: str = "G6-1.5K-SAI",
    years=(2060, 2069),
    nlat: int = 25,
    nlon: int = 33,
    lat_range=(20.0, 80.0),
    lon_range=(-80.0, 40.0),
    calendar_days: int = 365,
    seed: int = None,
) -> Dict[str, np.ndarray]:
    """Synthetic daily Euro-Atlantic circulation fields for the Weeks 7-8 demo.

    Returns ``ua`` (850 hPa zonal wind, m s-1), ``zg`` (500 hPa geopotential
    height, m) and ``psl`` (sea-level pressure, Pa) on a regular grid, with a
    seasonal cycle, transient synoptic eddies, occasional blocking (a reversed
    meridional Z500 gradient), and a scenario-dependent NAO/jet signal. As with
    the temperature/precip generator this is a caricature for demonstration, not
    a model emulator.
    """
    y0, y1 = years
    nyear = y1 - y0 + 1
    rng = np.random.default_rng(MODEL_SEED.get(model, 0) * 1000
                                + (hash(scenario) % 89) * 11 + (seed or 0) + 7)
    lat = np.linspace(lat_range[0], lat_range[1], nlat)
    lon = np.linspace(lon_range[0], lon_range[1], nlon)
    doy = np.tile(np.arange(1, calendar_days + 1), nyear)
    year = np.repeat(np.arange(y0, y1 + 1), calendar_days)
    ntime = doy.size
    sig = CIRC_SIGNAL.get(scenario, CIRC_SIGNAL["baseline"])
    winter = (np.cos(2 * np.pi * (doy - 15) / calendar_days) + 1) / 2  # 1 in DJF

    LAT = lat[None, :, None]
    # --- Z500: mean meridional gradient (high south, low north) + waves ---
    zmean = 5700.0 - 6.5 * (lat - 20.0)            # ~5700 m at 20N -> ~5310 m at 80N
    zg = np.empty((ntime, nlat, nlon), dtype="float32")
    ua = np.empty_like(zg)
    psl = np.empty_like(zg)

    jet_lat0 = 48.0 + sig["jet_shift"] * winter      # poleward shift in DJF under SAI
    for t in range(ntime):
        phase = 2 * np.pi * (rng.random() )          # random wave phase (weather)
        wave = 70.0 * np.sin(np.deg2rad(3 * (lon)) + phase)[None, :] * \
            np.exp(-((lat[:, None] - 55.0) / 18.0) ** 2)
        synoptic = rng.normal(0, 35.0, size=(nlat, nlon))
        # Occasional blocking ridge near 0-20E, 60N: locally lifts high-lat Z500
        block_prob = np.clip(0.06 + sig["block"] * winter[t], 0.0, 1.0)
        ridge = 0.0
        if rng.random() < block_prob:
            ridge = (260.0 * np.exp(-((lat[:, None] - 62.0) / 8.0) ** 2)
                     * np.exp(-((lon[None, :] - 10.0) / 18.0) ** 2))
        zg[t] = zmean[:, None] + wave + synoptic + ridge

        # --- u850 from thermal-wind-like meridional Z gradient + jet profile ---
        jl = jet_lat0[t]
        jet = (12.0 + sig["jet_boost"] * winter[t]) * \
            np.exp(-((lat[:, None] - jl) / 7.0) ** 2) * np.ones((1, nlon))
        ua[t] = jet + rng.normal(0, 2.5, size=(nlat, nlon))

        # --- SLP: climatology + NAO dipole (Azores high, Iceland low) ---
        # Positive NAO => higher pressure at the Azores AND lower pressure at
        # Iceland, so the two anomalies have opposite sign in the SLP field.
        nao_amp = sig["nao"] * winter[t] + rng.normal(0, 1.0)
        azores_anom = 700.0 * nao_amp * np.exp(-(((lat[:, None] - 38) / 9) ** 2 + ((lon[None, :] + 25) / 20) ** 2))
        iceland_anom = 900.0 * nao_amp * np.exp(-(((lat[:, None] - 65) / 8) ** 2 + ((lon[None, :] + 20) / 22) ** 2))
        psl[t] = 101300.0 - 1.5 * (lat[:, None] - 50) + azores_anom - iceland_anom \
            + rng.normal(0, 300.0, size=(nlat, nlon))

    return {
        "model": model, "scenario": scenario,
        "lat": lat.astype("float64"), "lon": lon.astype("float64"),
        "doy": doy.astype("int32"), "year": year.astype("int32"),
        "ua": ua, "zg": zg, "psl": psl,
        "units": {"ua": "m s-1", "zg": "m", "psl": "Pa"},
    }


def to_xarray(d: Dict[str, np.ndarray]):
    """Wrap a :func:`generate_daily` dict as a standardized xarray.Dataset."""
    import cftime
    import numpy as np
    import xarray as xr

    # Build a noleap time axis from (year, doy).
    times = [cftime.DatetimeNoLeap(int(y), 1, 1) + _days(int(dd) - 1)
             for y, dd in zip(d["year"], d["doy"])]
    ds = xr.Dataset(
        {
            "tasmax": (("time", "lat", "lon"), d["tasmax"], {"units": "degC"}),
            "tasmin": (("time", "lat", "lon"), d["tasmin"], {"units": "degC"}),
            "pr": (("time", "lat", "lon"), d["pr"], {"units": "mm day-1"}),
        },
        coords={"time": times, "lat": d["lat"], "lon": d["lon"]},
        attrs={"model": d["model"], "scenario": d["scenario"], "synthetic": "true"},
    )
    return ds


def _days(n):
    import datetime
    return datetime.timedelta(days=n)
