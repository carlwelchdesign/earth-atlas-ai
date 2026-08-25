"""Command-line entry point for deterministic candidate evaluation."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

from echoatlas.evaluation.harness import EvaluationInputError, evaluate_set
from echoatlas.evaluation.review import prepare_review_packet


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Evaluate review-only candidates against a versioned region set."
    )
    parser.add_argument("--evaluation-set", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--software-commit")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    commit = args.software_commit or _current_commit()
    report = evaluate_set(args.evaluation_set, software_commit=commit)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        f"{json.dumps(report.model_dump(mode='json'), indent=2, sort_keys=True)}\n"
    )
    print(args.output)
    return 0


def _current_commit() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL
        ).strip()
    except (OSError, subprocess.CalledProcessError) as error:
        raise EvaluationInputError(
            "software commit could not be resolved; pass --software-commit explicitly"
        ) from error


def review_main() -> int:
    parser = argparse.ArgumentParser(
        description="Prepare a local-only candidate review packet from validated outputs."
    )
    parser.add_argument("--change-run", required=True, type=Path)
    parser.add_argument("--preview-run", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    packet = prepare_review_packet(args.change_run, args.preview_run, args.output)
    print(
        json.dumps(
            {
                "packet_id": packet.packet_id,
                "candidate_count": len(packet.candidates),
                "index": str(args.output / "index.html"),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
