"""Command-line entry point for deterministic baseline change candidates."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path

from echoatlas.processor.changes.models import ChangeParameters
from echoatlas.processor.changes.pipeline import ChangeInputError, process_change_candidates

_SELECTION_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Produce review-only change candidates from an immutable preview run."
    )
    parser.add_argument("--preview-run", required=True, type=Path)
    parser.add_argument("--data-root", default=Path("data"), type=Path)
    parser.add_argument("--software-commit")
    parser.add_argument("--score-threshold", default=0.5, type=float)
    parser.add_argument("--registration-tolerance-pixels", default=2, type=int)
    parser.add_argument("--opening-iterations", default=1, type=int)
    parser.add_argument("--closing-iterations", default=1, type=int)
    parser.add_argument("--minimum-component-pixels", default=512, type=int)
    parser.add_argument("--maximum-candidate-count", default=500, type=int)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    commit = args.software_commit or _current_commit()
    parameters = ChangeParameters(
        score_threshold=args.score_threshold,
        registration_tolerance_pixels=args.registration_tolerance_pixels,
        opening_iterations=args.opening_iterations,
        closing_iterations=args.closing_iterations,
        minimum_component_pixels=args.minimum_component_pixels,
        maximum_candidate_count=args.maximum_candidate_count,
    )
    selection_id = _selection_id(args.preview_run)
    result = process_change_candidates(
        args.preview_run,
        output_root=args.data_root / "derived" / selection_id / "changes",
        software_commit=commit,
        parameters=parameters,
    )
    print(
        json.dumps(
            {
                "change_run_id": result.change_run_id,
                "output_directory": str(result.output_directory),
                "manifest": str(result.manifest_path),
                "candidates": str(result.candidates_path),
                "artifacts": [artifact.model_dump(mode="json") for artifact in result.artifacts],
            },
            indent=2,
        )
    )
    return 0


def _current_commit() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL
        ).strip()
    except (OSError, subprocess.CalledProcessError) as error:
        raise ChangeInputError(
            "software commit could not be resolved; pass --software-commit explicitly"
        ) from error


def _selection_id(preview_run: Path) -> str:
    try:
        document = json.loads((preview_run / "processing-manifest.json").read_text())
        selection_id = document["selection_id"]
    except (OSError, json.JSONDecodeError, KeyError, TypeError) as error:
        raise ChangeInputError("source processing manifest has no usable selection ID") from error
    if not isinstance(selection_id, str) or not _SELECTION_ID_PATTERN.fullmatch(selection_id):
        raise ChangeInputError("source processing manifest has no usable selection ID")
    return selection_id


if __name__ == "__main__":
    raise SystemExit(main())
