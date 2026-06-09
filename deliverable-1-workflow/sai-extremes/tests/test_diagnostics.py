"""Tests for circulation-diagnostic kernels (NumPy-only, run anywhere)."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from sai_extremes import diagnostics as D  # noqa: E402


def test_jet_lat_speed_peak():
    lat = np.arange(20, 81, 2.0)
    # Gaussian jet centred at 50 N, peak 15 m/s
    u = 15.0 * np.exp(-((lat - 50.0) / 7.0) ** 2)
    jl, js = D.jet_lat_speed(u, lat, parabolic=True)
    assert abs(jl - 50.0) < 1.0
    assert abs(js - 15.0) < 0.5


def test_jet_parabolic_subgrid():
    # peak between grid points -> parabolic fit should land between them
    lat = np.array([40.0, 45.0, 50.0, 55.0, 60.0])
    u = np.array([1.0, 4.0, 5.0, 4.5, 2.0])  # true peak slightly above 50
    jl, js = D.jet_lat_speed(u, lat, parabolic=True)
    assert 50.0 <= jl <= 55.0
    assert js >= 5.0


def test_highpass_removes_lowfreq():
    t = np.arange(200)
    slow = 10 * np.sin(2 * np.pi * t / 180)        # seasonal-like, period 180
    fast = np.sin(2 * np.pi * t / 4)               # synoptic, period 4 d
    hp = D.highpass_anomaly(slow + fast, window=10)
    # high-pass should retain most of the fast signal, remove most of the slow
    assert np.std(hp) < np.std(slow + fast)
    assert np.corrcoef(hp[20:-20], fast[20:-20])[0, 1] > 0.8


def test_storm_track_intensity_increases_with_eddies():
    rng = np.random.default_rng(0)
    calm = rng.normal(0, 5, 500)
    stormy = rng.normal(0, 50, 500)
    assert D.storm_track_intensity(stormy) > D.storm_track_intensity(calm)


def test_tibaldi_molteni_detects_reversal():
    lat = np.arange(30.0, 81.0, 5.0)
    # Normal westerly profile: Z decreases northward -> NOT blocked
    z_normal = 5700 - 6.5 * (lat - 30)
    assert not D.tm_blocked_at_lon(z_normal, lat)
    # Blocked: high Z at 60N (ridge), low to north -> reversal
    z_block = z_normal.copy()
    idx60 = np.argmin(np.abs(lat - 60))
    z_block[idx60] += 400  # strong ridge at 60N
    assert D.tm_blocked_at_lon(z_block, lat)


def test_tm_blocking_frequency_bounds():
    lat = np.arange(30.0, 81.0, 5.0)
    rng = np.random.default_rng(1)
    z = 5700 - 6.5 * (lat - 30)[None, :] + rng.normal(0, 20, (50, lat.size))
    f = D.tm_blocking_frequency(z, lat)
    assert 0.0 <= f <= 1.0


def test_nao_station_index_sign():
    # Azores high anomaly + Iceland low anomaly -> positive NAO
    az = np.array([1.0, 2.0, 3.0, 4.0])
    ic = np.array([4.0, 3.0, 2.0, 1.0])  # anti-correlated
    nao = D.nao_station_index(az, ic)
    assert nao[-1] > nao[0]  # last day more positive NAO than first


def _run_all():
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn(); print(f"  PASS  {fn.__name__}")
    print(f"\n{len(fns)}/{len(fns)} diagnostics tests passed.")


if __name__ == "__main__":
    _run_all()
