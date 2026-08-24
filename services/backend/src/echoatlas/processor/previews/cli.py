"""Command-line entry point for deterministic aligned SAR previews."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from echoatlas.processor.acquisition.cache import SafeAcquisitionCache
from echoatlas.processor.acquisition.cli import DEFAULT_ALLOWED_HOST
from echoatlas.processor.acquisition.models import load_selection_manifest
from echoatlas.processor.previews.models import ProcessingParameters
from echoatlas.processor.previews.pipeline import process_pair


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate and align the approved SAR pair into deterministic previews."
    )
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--data-root", default=Path("data"), type=Path)
    parser.add_argument("--target-crs", default="EPSG:32612")
    parser.add_argument("--target-resolution", default=1.0, type=float)
    parser.add_argument("--lower-percentile", default=2.0, type=float)
    parser.add_argument("--upper-percentile", default=98.0, type=float)
    parser.add_argument("--thumbnail-max-size", default=512, type=int)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    manifest = load_selection_manifest(args.manifest)
    cached = SafeAcquisitionCache(
        data_root=args.data_root,
        allowed_hosts=frozenset({DEFAULT_ALLOWED_HOST}),
    ).fetch_manifest(manifest, source_manifest_path=args.manifest)
    sources = {result.role: result.cache_path for result in cached}
    parameters = ProcessingParameters(
        target_crs=args.target_crs,
        target_resolution=args.target_resolution,
        lower_percentile=args.lower_percentile,
        upper_percentile=args.upper_percentile,
        thumbnail_max_size=args.thumbnail_max_size,
    )
    result = process_pair(
        manifest,
        sources,
        output_root=args.data_root / "derived" / manifest.selection_id,
        parameters=parameters,
    )
    print(
        json.dumps(
            {
                "run_id": result.run_id,
                "output_directory": str(result.output_directory),
                "manifest": str(result.manifest_path),
                "quality_report": str(result.quality_report_path),
                "artifacts": [artifact.model_dump(mode="json") for artifact in result.artifacts],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
