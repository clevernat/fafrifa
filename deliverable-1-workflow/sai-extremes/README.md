# sai-extremes

**An open, reproducible workflow for SAI mid-latitude extremes indices.**
Deliverable 1 of the Reflective *SAI Uncertainty Database* internship — Track A:
*Mid-latitude extreme winter weather response to SAI*.

`sai-extremes` computes ETCCDI-style climate extremes indices for the GeoMIP
**G6-1.5K-SAI** (subtropical injection) and **G6-1.5K-HiLLA** (high-latitude,
low-altitude, seasonal injection) scenarios across up to four Earth system
models (CESM2-WACCM, MIROC-ES2H, UKESM1, E3SMv3), from a single, tested entry
point that runs on the Reflective Cloud Hub.

It extends the existing ETCCDI codebase with **percentile-based indices**
(TX90p/TX10p/TN90p/TN10p, WSDI/CSDI, R95p/R99p) including the Zhang et al. (2005)
out-of-base bootstrap, and adds a **pluggable I/O layer** so the same analysis
reads local NetCDF, NetCDF-on-S3, or cloud-optimized Zarr without code changes.

---

## Why the architecture looks like this

The numerically important logic lives in **pure-NumPy kernels**
(`sai_extremes.kernels`) that depend on nothing but NumPy and are unit-tested
against hand-computed values. The **xarray layer** (`indices`, `percentiles`)
wraps those kernels with `apply_ufunc` to run gridpoint-by-gridpoint over CMIP
data cubes. Benefits:

* the index definitions are verifiable **anywhere**, even without the heavy
  geoscience stack (useful for CI and for review);
* there is exactly **one** implementation of each index — the xarray tests
  assert the two layers agree on identical input, so they cannot drift;
* adding an index is a one-line registry entry in `sai_extremes.indices`.

```
src/sai_extremes/
  kernels.py      pure-NumPy index algorithms        (unit-tested, no deps)
  indices.py      xarray operators + index registry   (fixed/block indices)
  percentiles.py  percentile indices + Zhang bootstrap
  io.py           pluggable backends: local / s3-netcdf / zarr
  catalog.py      model/scenario/variable registry (YAML-backed)
  regions.py      NH mid-latitude masks + DJF selection
  pipeline.py     driver to produce the indices dataset (Deliverable 2)
  synthetic.py    synthetic GeoMIP-shaped data for tests/demo/CI
config/catalog.yaml
tests/            kernel + bootstrap + xarray integration tests
notebooks/01_extremes_workflow_demo.ipynb
```

## Indices (24)

Fixed-threshold / block: `SU ID FD TR R10mm R20mm CDD CWD TXx TXn TNx TNn Rx1day
Rx5day PRCPTOT SDII`. Percentile-based: `TX90p TX10p TN90p TN10p WSDI CSDI R95p
R99p`. See `sai_extremes.INDEX_REGISTRY` for definitions/units/metadata.

## Install

```bash
# Light core (numpy kernels + registry + tests):
pip install -e .

# Full workflow (xarray pipeline + cloud I/O + plotting):
pip install -e ".[all]"
# or:  conda env create -f environment.yml
```

## Quick start

```python
import sai_extremes as se
se.list_indices()                       # all 24
se.list_indices(kind="percentile")      # the 8 percentile indices

# --- Production (on the Cloud Hub) ---
from sai_extremes.io import open_daily
from sai_extremes.pipeline import run_model_scenario

ds = open_daily("CESM", "G6-1.5K-SAI", ["tasmax", "tasmin", "pr"])  # standardized
indices = run_model_scenario("CESM", "G6-1.5K-SAI", base_ds=ref_ds)  # xarray.Dataset
indices.to_netcdf("etccdi_CESM_G6-1.5K-SAI.nc")

# --- Anywhere (no data needed) ---
from sai_extremes import synthetic, pipeline
daily = synthetic.generate_daily("CESM", "G6-1.5K-SAI")
base  = synthetic.generate_daily("CESM", "baseline")
res = pipeline.compute_all_indices_numpy(daily, base=base)   # dict of fields
```

Point the workflow at real data by editing `config/catalog.yaml` (URIs +
`backend: s3-netcdf | zarr`); no Python changes are needed. Switch a model to
`zarr` when S3 NetCDF reads become the bottleneck (per the June 4 check-in).

## Tests

```bash
pytest                       # full suite (needs xarray for integration tests)
python tests/test_kernels.py # kernels only — runs with just NumPy
```

The kernel and bootstrap tests pin every ETCCDI definition to hand-computed
expected values; the xarray tests assert the production operators reproduce the
kernels exactly.

## Scientific choices

* Wet-day threshold 1 mm day⁻¹; 5-day calendar-day percentile window; spells
  ≥ 6 days (WSDI/CSDI). Definitions follow Zhang et al. (2011) and Klein Tank et
  al. (2009).
* Temperature percentile indices use the Zhang et al. (2005) out-of-base
  bootstrap to avoid in-base/out-of-base inhomogeneity.
* **Baseline matters:** per Duffey & Irvine (2024), use a quasi-equilibrium
  reference at the SAI target global-mean temperature as the base period, not a
  transient SSP segment — see `DATA_CARD.md`.
* Model calendars (`noleap`, `360_day`, `gregorian`) are preserved; day-of-year
  handling is calendar-agnostic.

## License

MIT.
