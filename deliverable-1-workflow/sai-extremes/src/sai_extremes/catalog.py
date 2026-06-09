"""Model / scenario / variable catalog.

A thin, YAML-backed registry that maps a (model, scenario, variable) request to
a storage backend and a set of URIs. Keeping this declarative means the I/O code
and the indices code never hard-code paths, and swapping S3 NetCDF for Zarr is a
one-line edit in ``config/catalog.yaml``.

Not every model ran every scenario. The June 2026 multi-model HiLLA paper
(Duffey et al., 2026) used UKESM1, CESM2-WACCM and E3SMv3; MIROC contributes to
G6-1.5K-SAI but not (yet) to the HiLLA ensemble. The catalog encodes this with
``available`` flags so the pipeline skips missing combinations gracefully
instead of failing late.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

import yaml

DEFAULT_CATALOG = Path(__file__).resolve().parents[2] / "config" / "catalog.yaml"

MODELS = ["CESM", "MIROC", "UKESM", "E3SMv3"]
SCENARIOS = ["G6-1.5K-SAI", "G6-1.5K-HiLLA"]


@dataclass
class Catalog:
    raw: Dict

    def models(self) -> List[str]:
        return list(self.raw.get("models", {}))

    def scenarios(self) -> List[str]:
        return list(self.raw.get("scenarios", []))

    def is_available(self, model: str, scenario: str) -> bool:
        m = self.raw["models"].get(model, {})
        return scenario in m.get("scenarios", {}) and \
            m["scenarios"][scenario].get("available", False)

    def available_pairs(self):
        """All (model, scenario) pairs flagged available."""
        out = []
        for model in self.models():
            for scenario in self.scenarios():
                if self.is_available(model, scenario):
                    out.append((model, scenario))
        return out

    def entry(self, model: str, scenario: str) -> Dict:
        if model not in self.raw["models"]:
            raise KeyError(f"Model '{model}' not in catalog ({self.models()}).")
        msc = self.raw["models"][model].get("scenarios", {})
        if scenario not in msc:
            raise KeyError(f"Scenario '{scenario}' not catalogued for {model}.")
        e = msc[scenario]
        if not e.get("available", False):
            raise KeyError(
                f"{model}/{scenario} is catalogued but not yet available "
                f"(available=False). Reason: {e.get('note', 'not stated')}.")
        # Resolve backend defaults from the model/global level.
        backend = e.get("backend", self.raw["models"][model].get("backend",
                        self.raw.get("default_backend", "s3-netcdf")))
        return {
            "backend": backend,
            "backend_kwargs": e.get("backend_kwargs",
                                    self.raw.get("backend_kwargs", {}).get(backend, {})),
            "uris": e["uris"],
            "calendar": e.get("calendar", self.raw["models"][model].get("calendar")),
            "note": e.get("note"),
        }


def load_catalog(path=None) -> Catalog:
    path = Path(path) if path else DEFAULT_CATALOG
    with open(path) as fh:
        return Catalog(yaml.safe_load(fh))
