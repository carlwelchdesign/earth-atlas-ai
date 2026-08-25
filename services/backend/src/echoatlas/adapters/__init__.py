"""Optional platform adapters that consume validated EchoAtlas contracts."""

from echoatlas.adapters.palantir import PalantirImportPlan, plan_palantir_import
from echoatlas.adapters.palantir_package import (
    PalantirTablePackageManifest,
    write_palantir_import_package,
)

__all__ = [
    "PalantirImportPlan",
    "PalantirTablePackageManifest",
    "plan_palantir_import",
    "write_palantir_import_package",
]
