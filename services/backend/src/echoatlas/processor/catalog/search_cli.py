"""Bounded live smoke-test entry point for provider-neutral catalog search."""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

from echoatlas.processor.catalog.providers import (
    UMBRA_ROOT_URL,
    build_default_catalog_search_service,
)
from echoatlas.processor.catalog.search_models import (
    CatalogSearchRequest,
    GeoJsonPolygon,
    SearchAoi,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Search bounded Umbra and Sentinel-1 metadata without downloading imagery."
    )
    parser.add_argument("--bbox", required=True, help="west,south,east,north in WGS84")
    parser.add_argument("--start", required=True, help="timezone-aware ISO 8601 timestamp")
    parser.add_argument("--end", required=True, help="timezone-aware ISO 8601 timestamp")
    parser.add_argument(
        "--provider",
        action="append",
        choices=("umbra", "sentinel-1"),
        dest="providers",
    )
    parser.add_argument("--page-size", type=int, default=25)
    parser.add_argument(
        "--umbra-root-url",
        default=None,
        help="optional narrower public Umbra STAC catalog for a bounded smoke test",
    )
    parser.add_argument("--umbra-max-catalogs", type=int, default=500)
    parser.add_argument("--umbra-max-items", type=int, default=500)
    parser.add_argument("--output", type=Path)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    bbox = _bbox(args.bbox)
    west, south, east, north = bbox
    geometry = GeoJsonPolygon(
        coordinates=(
            (
                (west, south),
                (east, south),
                (east, north),
                (west, north),
                (west, south),
            ),
        )
    )
    request = CatalogSearchRequest(
        aoi=SearchAoi(bbox=bbox, geometry=geometry),
        start_at=datetime.fromisoformat(args.start.replace("Z", "+00:00")),
        end_at=datetime.fromisoformat(args.end.replace("Z", "+00:00")),
        providers=tuple(args.providers or ("umbra", "sentinel-1")),
        page_size=args.page_size,
    )
    payload = (
        build_default_catalog_search_service(
            umbra_root_url=args.umbra_root_url or UMBRA_ROOT_URL,
            umbra_max_catalogs=args.umbra_max_catalogs,
            umbra_max_items=args.umbra_max_items,
        )
        .search(request)
        .model_dump_json(indent=2)
    )
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(f"{payload}\n", encoding="utf-8")
    else:
        print(payload)
    return 0


def _bbox(value: str) -> tuple[float, float, float, float]:
    parts = tuple(float(part.strip()) for part in value.split(","))
    if len(parts) != 4:
        raise argparse.ArgumentTypeError("bbox requires west,south,east,north")
    return parts


if __name__ == "__main__":
    raise SystemExit(main())
