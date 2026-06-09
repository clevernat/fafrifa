# Contributing

This repo holds the Track A deliverables for the Reflective SAI Uncertainty
Database (open-science workflow, indices dataset, and uncertainty entry).
Contributions that extend the index set, add diagnostics, or wire the catalog to
new model output are welcome.

## Dev setup

```bash
cd deliverable-1-workflow/sai-extremes
pip install -e ".[all]"      # full stack (xarray, cloud I/O, plotting, pytest)
pytest -q                    # full suite
python tests/test_kernels.py # numpy-only fast path
```

## Ground rules for index / diagnostic code

* **Put the math in a NumPy kernel** (`sai_extremes/kernels.py` or
  `diagnostics.py`) and unit-test it against hand-computed values. The xarray
  layer should only orchestrate (`apply_ufunc`, `groupby`), never redefine the
  algorithm.
* **Add an index** by appending one entry to `INDEX_REGISTRY` in
  `sai_extremes/indices.py` (name, variable, units, kernel, CF metadata). The
  pipeline and data card pick it up automatically.
* **Follow the ETCCDI conventions** (Zhang et al., 2011; Klein Tank et al.,
  2009): 1 mm wet-day threshold, 5-day calendar-day percentile window, ≥6-day
  spells, and the Zhang (2005) out-of-base bootstrap for in-base years.
* **Never silently convert calendars.** Preserve the model's native calendar;
  day-of-year handling is calendar-agnostic (1–366 with wrap-around).
* **Keep the baseline honest.** Percentile base periods must use a
  quasi-equilibrium reference at the target global-mean temperature (Duffey &
  Irvine, 2024), not a transient SSP segment.

## Wiring new data

Edit `deliverable-1-workflow/sai-extremes/config/catalog.yaml`: add the model /
scenario / variable URIs and set `backend: s3-netcdf | zarr`. Set
`available: true` only when the data exists. No Python changes are required.

## Tests must pass before merge

CI runs the NumPy-only kernels on Python 3.9–3.12, the full xarray suite on
3.10–3.12, and a demo-dataset smoke test. Add tests for any new behaviour.
