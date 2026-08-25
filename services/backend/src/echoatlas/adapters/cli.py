"""Command-line entry points for optional platform projections."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path

from echoatlas.adapters.palantir import plan_palantir_import
from echoatlas.adapters.palantir_package import write_palantir_import_package
from echoatlas.bundle.validator import BundleValidator


def palantir_plan_main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Create a network-free Palantir import plan from a validated bundle"
    )
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--schema-root",
        type=Path,
        default=Path("schemas/analysis-bundle/v1"),
    )
    arguments = parser.parse_args(argv)
    bundle = BundleValidator(arguments.schema_root).validate(arguments.bundle)
    plan = plan_palantir_import(bundle)
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(
        f"{plan.model_dump_json(indent=2)}\n",
        encoding="utf-8",
    )
    print(arguments.output)


def palantir_package_main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Create normalized, network-free Palantir import tables"
    )
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--schema-root",
        type=Path,
        default=Path("schemas/analysis-bundle/v1"),
    )
    arguments = parser.parse_args(argv)
    bundle = BundleValidator(arguments.schema_root).validate(arguments.bundle)
    plan = plan_palantir_import(bundle)
    write_palantir_import_package(plan, arguments.output)
    print(arguments.output)
