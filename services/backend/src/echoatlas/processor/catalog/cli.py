"""Command line entry point for metadata-only Umbra catalog indexing."""

from __future__ import annotations

import argparse
from pathlib import Path

from echoatlas.processor.catalog.http import SafeMetadataClient
from echoatlas.processor.catalog.indexer import CatalogIndexer
from echoatlas.processor.catalog.s3 import PublicS3ObjectResolver
from echoatlas.processor.catalog.stac import StacCatalogAdapter

DEFAULT_BUCKET_URL = "https://umbra-open-data-catalog.s3.us-west-2.amazonaws.com"
DEFAULT_ROOT_URL = f"{DEFAULT_BUCKET_URL}/stac/catalog.json"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Index bounded public Umbra metadata without downloading imagery."
    )
    parser.add_argument("--root-url", default=DEFAULT_ROOT_URL)
    parser.add_argument("--bucket-url", default=DEFAULT_BUCKET_URL)
    parser.add_argument("--max-catalogs", type=int, default=250)
    parser.add_argument("--max-items", type=int, default=250)
    parser.add_argument("--max-s3-pages", type=int, default=10)
    parser.add_argument("--index-output", type=Path)
    parser.add_argument("--report-output", type=Path)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    client = SafeMetadataClient(
        allowed_hosts=frozenset({"umbra-open-data-catalog.s3.us-west-2.amazonaws.com"})
    )
    index = CatalogIndexer(
        StacCatalogAdapter(client), PublicS3ObjectResolver(client, args.bucket_url)
    ).build(
        args.root_url,
        max_catalogs=args.max_catalogs,
        max_items=args.max_items,
        max_s3_pages=args.max_s3_pages,
    )
    if args.index_output:
        _write_json(args.index_output, index.model_dump_json(indent=2))
    report_json = index.report.model_dump_json(indent=2)
    if args.report_output:
        _write_json(args.report_output, report_json)
    if not args.index_output and not args.report_output:
        print(report_json)
    return 0


def _write_json(path: Path, payload: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"{payload}\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
