"""Generate the demo extremes-indices dataset (Deliverable 2).

Runs the *portable* NumPy path of the workflow on synthetic GeoMIP-shaped data
for every available model x scenario, and writes:

* ``demo_output/etccdi_<MODEL>_<SCENARIO>.npz`` -- all 24 index fields + coords.
* ``demo_output/indices_regional_means.csv``    -- tidy, analysis-ready table of
  cos(lat)-weighted regional means per index/model/scenario/year.
* ``demo_output/figs/*.png``                     -- example diagnostics.

On the Cloud Hub the *same* index definitions are written as CF-NetCDF by
``sai_extremes.pipeline.run_all`` (the production path). This script exists so
the dataset's structure is reproducible with NumPy alone. See DATA_CARD.md.
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "deliverable-1-workflow" / "sai-extremes" / "src"))

from sai_extremes import synthetic, pipeline, regions  # noqa: E402
from sai_extremes.indices import INDEX_REGISTRY  # noqa: E402
from sai_extremes.catalog import load_catalog  # noqa: E402

OUT = Path(__file__).resolve().parents[1] / "demo_output"
FIGS = OUT / "figs"
OUT.mkdir(parents=True, exist_ok=True)
FIGS.mkdir(parents=True, exist_ok=True)

# Small but non-trivial grid covering the NH mid-latitude / Euro-Atlantic domain.
GRID = dict(nlat=6, nlon=12, lat_range=(20.0, 80.0), lon_range=(-100.0, 60.0))
BASE_YEARS = (2050, 2056)
ANALYSIS_YEARS = (2060, 2066)

REGION_LIST = ["NH_midlat", "Euro_Atlantic", "Mediterranean", "Eurasia_high", "Northern_Europe"]


def cos_lat_region_mean(field_year, lat, lon, region):
    """cos(lat)-weighted mean of a (nlat,nlon) field over a named region box."""
    lat_s, lat_n, lon_w, lon_e = regions.REGIONS[region]
    la = (lat >= lat_s) & (lat <= lat_n)
    lo = (lon >= lon_w) & (lon <= lon_e)
    if not la.any() or not lo.any():
        return np.nan
    sub = field_year[np.ix_(la, lo)]
    w = np.cos(np.deg2rad(lat[la]))[:, None] * np.ones((1, lo.sum()))
    m = ~np.isnan(sub)
    if not m.any():
        return np.nan
    return float(np.sum(sub[m] * w[m]) / np.sum(w[m]))


def main():
    cat = load_catalog(ROOT / "deliverable-1-workflow" / "sai-extremes" / "config" / "catalog.yaml")
    pairs = cat.available_pairs()
    print(f"Available model x scenario pairs: {pairs}")

    rows = []
    results = {}
    for model, scenario in pairs:
        print(f"  computing {model}/{scenario} ...", flush=True)
        base = synthetic.generate_daily(model, "baseline", years=BASE_YEARS, **GRID)
        daily = synthetic.generate_daily(model, scenario, years=ANALYSIS_YEARS, **GRID)
        res = pipeline.compute_all_indices_numpy(daily, base=base)
        results[(model, scenario)] = res

        npz_path = OUT / f"etccdi_{model}_{scenario}.npz"
        np.savez_compressed(
            npz_path,
            years=res["years"], lat=res["lat"], lon=res["lon"],
            **{f"index__{k}": v for k, v in res["fields"].items()},
        )
        # Tidy regional means
        for idx, field in res["fields"].items():
            for yi, year in enumerate(res["years"]):
                for region in REGION_LIST:
                    rows.append({
                        "model": model, "scenario": scenario, "index": idx,
                        "region": region, "year": int(year),
                        "value": cos_lat_region_mean(field[yi], res["lat"], res["lon"], region),
                        "units": INDEX_REGISTRY[idx].units,
                    })

    csv_path = OUT / "indices_regional_means.csv"
    with open(csv_path, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["model", "scenario", "index", "region", "year", "value", "units"])
        w.writeheader()
        w.writerows(rows)
    print(f"  wrote {csv_path} ({len(rows)} rows)")

    _make_figures(results)
    print("Done.")
    return results, rows


def _make_figures(results):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    models = sorted({m for (m, s) in results})
    scenarios = ["G6-1.5K-SAI", "G6-1.5K-HiLLA"]

    # Fig 1: inter-model spread of Eurasian-winter FD (frost days), SAI vs HiLLA.
    def region_index_mean(model, scenario, index, region):
        if (model, scenario) not in results:
            return np.nan
        res = results[(model, scenario)]
        vals = [cos_lat_region_mean(res["fields"][index][yi], res["lat"], res["lon"], region)
                for yi in range(res["years"].size)]
        return np.nanmean(vals)

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))
    for ax, index, region, title in [
        (axes[0], "FD", "Eurasia_high", "Frost days (FD), Eurasia 50-70N"),
        (axes[1], "TX90p", "Euro_Atlantic", "Warm days (TX90p), Euro-Atlantic"),
    ]:
        x = np.arange(len(models))
        width = 0.38
        for k, sc in enumerate(scenarios):
            vals = [region_index_mean(m, sc, index, region) for m in models]
            ax.bar(x + (k - 0.5) * width, vals, width, label=sc)
        ax.set_xticks(x); ax.set_xticklabels(models, rotation=0)
        ax.set_title(title); ax.set_ylabel(INDEX_REGISTRY[index].units)
        ax.grid(axis="y", alpha=0.3)
    axes[0].legend(fontsize=8, loc="upper right")
    fig.suptitle("Inter-model spread of mid-latitude winter extremes: SAI vs HiLLA (synthetic demo)",
                 fontsize=11)
    fig.tight_layout()
    fig.savefig(FIGS / "intermodel_spread.png", dpi=130)
    plt.close(fig)

    # Fig 2: example map of TX90p for the first available SAI run.
    key = next(((m, s) for (m, s) in results if s == "G6-1.5K-SAI"), None)
    if key:
        res = results[key]
        field = np.nanmean(res["fields"]["TX90p"], axis=0)
        fig, ax = plt.subplots(figsize=(7, 4.2))
        im = ax.pcolormesh(res["lon"], res["lat"], field, shading="auto", cmap="RdBu_r")
        ax.set_title(f"TX90p (% warm days), {key[0]} {key[1]} (synthetic demo)")
        ax.set_xlabel("longitude"); ax.set_ylabel("latitude")
        fig.colorbar(im, ax=ax, label="%")
        fig.tight_layout()
        fig.savefig(FIGS / "tx90p_map_example.png", dpi=130)
        plt.close(fig)


if __name__ == "__main__":
    main()
