"""Command-line interface for the local real-imagery workbench boundary."""

from __future__ import annotations

import argparse
from pathlib import Path

from echoatlas.demo.prepare import prepare_workbench_demo


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Stage a validated satellite-derived workbench demo locally."
    )
    parser.add_argument("--selection-manifest", type=Path, required=True)
    parser.add_argument("--preview-run", type=Path, required=True)
    parser.add_argument("--change-run", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    result = prepare_workbench_demo(
        selection_manifest_path=args.selection_manifest,
        preview_run=args.preview_run,
        change_run=args.change_run,
        output_directory=args.output,
    )
    print(f"Prepared {result.candidate_count} candidates at {result.output_directory}")
