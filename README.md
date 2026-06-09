# Track A — Mid-latitude extreme winter weather response to SAI

Deliverables for the **Reflective SAI Uncertainty Database** internship project
(*Open Science for Reflective's SAI Uncertainty Database*), Track A. The project
quantifies how Northern-Hemisphere mid-latitude winter extremes respond to two
GeoMIP scenarios — **G6-1.5K-SAI** (subtropical injection) and **G6-1.5K-HiLLA**
(high-latitude, low-altitude, seasonal injection) — across up to four Earth
system models, and demonstrates a best-practice, reproducible open-science
workflow for the *Extratropical Circulation* uncertainty.

## The three deliverables

| # | Deliverable | Where | What it is |
|---|---|---|---|
| **1** | Open-source workflow | [`deliverable-1-workflow/sai-extremes/`](deliverable-1-workflow/sai-extremes/) | A tested Python package (`sai_extremes`) computing 24 ETCCDI fixed + percentile extremes indices, with a pluggable local/S3/Zarr I/O layer, catalog, regions, pipeline, tests, and a demo notebook. |
| **2** | Indices dataset | [`deliverable-2-dataset/`](deliverable-2-dataset/) | The multi-model indices dataset (CF-NetCDF in production), a data card, a machine-readable schema, the production driver, and a runnable demo that reproduces the dataset's structure. |
| **3** | Revised uncertainty entry | [`deliverable-3-uncertainty-entry/`](deliverable-3-uncertainty-entry/) | A revised *Extratropical Circulation* entry synthesising the new G6-1.5K-SAI/HiLLA multi-model evidence, with proposed ratings, mechanism, sources of spread, and what would reduce the uncertainty. |

## How the deliverables connect

```
   G6-1.5K-SAI / -HiLLA daily data (Cloud Hub)
                    │
        [Deliverable 1] sai_extremes workflow  ──►  pluggable I/O ─ kernels ─ xarray
                    │                                 (unit-tested ETCCDI definitions)
                    ▼
        [Deliverable 2] multi-model indices dataset  +  regional-means table  +  figures
                    │
                    ▼
        [Deliverable 3] revised "Extratropical Circulation" uncertainty entry
                         (quantified, reproducible, multi-model)
```

## Design choices worth knowing

* **Verifiable core.** Every index is a pure-NumPy *kernel* unit-tested against
  hand-computed values, then wrapped for xarray. The two layers are asserted to
  agree, so the production code carries the same logic that the tests check.
  This is why the workflow and the demo dataset could be built and validated even
  without the Cloud Hub data — the index math is exercised directly.
* **Catalog-driven, strategy-aware.** Model × scenario availability is
  declarative; the pipeline skips combinations that do not exist (e.g. MIROC has
  no HiLLA run in Duffey et al., 2026). Switching S3-NetCDF → Zarr is a one-line
  catalog edit.
* **Correct baseline.** Percentile indices use a quasi-equilibrium reference at
  the target global-mean temperature, per Duffey & Irvine (2024), to avoid
  mis-attributing transient warming to SAI.

## Reproduce

```bash
# Deliverable 1 — run the tests (NumPy-only path works anywhere):
cd deliverable-1-workflow/sai-extremes
python tests/test_kernels.py
python tests/test_percentiles.py
# full suite incl. xarray integration tests:  pip install -e ".[all]" && pytest

# Deliverable 2 — regenerate the demo dataset + figures:
python ../../deliverable-2-dataset/scripts/generate_demo_dataset.py

# Production (on the Cloud Hub, after pointing config/catalog.yaml at real data):
python ../../deliverable-2-dataset/scripts/run_production.py --outdir indices_dataset
```

## Status against the project plan

* **Weeks 2–3 (data & code familiarisation):** I/O layer for G6-1.5K-SAI/-HiLLA
  across the four models, ETCCDI reproduction, mid-latitude sanity checks — built
  and tested (Deliverable 1).
* **Weeks 4–6 (extremes workflow):** percentile-based indices added (Zhang 2005
  bootstrap); full index set runs for both scenarios and all models; dataset +
  open-source workflow produced (Deliverables 1 & 2).
* **Weeks 7–8 (circulation & spread):** jet / storm-track / blocking diagnostics
  and composite anomalies — *next*; the regions module and DJF selection are in
  place to support them.
* **Weeks 9–10 (synthesis):** revised uncertainty entry drafted (Deliverable 3),
  to be finalised with the quantified multi-model signal.

> **Note on the demo data.** The Cloud Hub was not reachable from the build
> environment, so the dataset files under `deliverable-2-dataset/demo_output/`
> were generated on **synthetic** GeoMIP-shaped data using the workflow's
> portable path. They reproduce the real dataset's structure, units and metadata
> and use the same tested kernels, but are not model output. Pointing the catalog
> at the Cloud Hub and running the production driver yields the real CF-NetCDF
> dataset with no code changes.
