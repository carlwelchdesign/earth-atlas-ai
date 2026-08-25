"""Optional platform adapters that consume validated EchoAtlas contracts."""

from echoatlas.adapters.palantir import PalantirImportPlan, plan_palantir_import

__all__ = ["PalantirImportPlan", "plan_palantir_import"]
