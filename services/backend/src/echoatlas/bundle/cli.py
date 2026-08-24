"""Command-line entry points for generating and validating analysis bundles."""

from __future__ import annotations

import argparse
import json
import subprocess
from collections.abc import Sequence
from pathlib import Path

from echoatlas.bundle.fixture import FixtureCase, generate_fixture
from echoatlas.bundle.validator import BundleValidator


def generate_main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Generate a bounded synthetic bundle fixture")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--case", choices=[case.value for case in FixtureCase], default="valid")
    parser.add_argument("--software-commit", default=None)
    arguments = parser.parse_args(argv)
    commit = arguments.software_commit or _current_commit()
    output = generate_fixture(
        arguments.output,
        case=FixtureCase(arguments.case),
        software_commit=commit,
    )
    print(json.dumps({"case": arguments.case, "output": str(output)}, sort_keys=True))


def validate_main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Validate an EchoAtlas analysis bundle")
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument(
        "--schema-root",
        type=Path,
        default=Path("schemas/analysis-bundle/v1"),
    )
    arguments = parser.parse_args(argv)
    result = BundleValidator(arguments.schema_root).validate(arguments.bundle)
    print(
        json.dumps(
            {
                "bundle_id": result.manifest["bundle_id"],
                "missing_artifact_ids": result.missing_artifact_ids,
                "status": result.manifest["status"],
                "valid": True,
            },
            sort_keys=True,
        )
    )


def _current_commit() -> str:
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()
