"""Command-line entry point for safe acquisition caching."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from echoatlas.processor.acquisition.cache import SafeAcquisitionCache
from echoatlas.processor.acquisition.models import load_selection_manifest

DEFAULT_ALLOWED_HOST = "umbra-open-data-catalog.s3.us-west-2.amazonaws.com"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Download approved pinned acquisitions into a verified local cache."
    )
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--data-root", default=Path("data"), type=Path)
    parser.add_argument("--max-object-bytes", default=1_000_000_000, type=int)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    manifest = load_selection_manifest(args.manifest)
    results = SafeAcquisitionCache(
        data_root=args.data_root,
        allowed_hosts=frozenset({DEFAULT_ALLOWED_HOST}),
        max_object_bytes=args.max_object_bytes,
    ).fetch_manifest(manifest, source_manifest_path=args.manifest)
    print(
        json.dumps(
            [
                {
                    "role": result.role,
                    "item_id": result.item_id,
                    "cache_path": str(result.cache_path),
                    "size_bytes": result.size_bytes,
                    "checksum_crc64nvme": result.checksum_crc64nvme,
                    "from_cache": result.from_cache,
                }
                for result in results
            ],
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
