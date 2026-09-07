#!/usr/bin/env python3
"""Prepare the bounded Nepal investigation assets from pinned local sources."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import shutil
import tempfile
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import rasterio
import shapefile
from PIL import Image
from rasterio.enums import Resampling
from rasterio.transform import from_bounds
from rasterio.warp import reproject, transform, transform_geom

AOI = (85.3, 28.08, 85.42, 28.28)
ZOOMS = range(8, 15)
TILE_SIZE = 256
WEB_MERCATOR_LIMIT = 20037508.342789244
EXPECTED = {
    "before-tci.tif": "d87a9f98b759ff52ca6781ed1403828eaf5743fb662604e6b65d343cdfbb0ab0",  # noqa: E501  # pragma: allowlist secret
    "after-tci.tif": "7b98c0d9d0164be5f329073227dd2bd2966518b5c3bc9b1769e37dc903d21b8e",  # noqa: E501  # pragma: allowlist secret
    "unosat-flood-extent.zip": "867b5bebb4881d1b8f88af31df7f784f5db612fa651c911d81d7304bf5be0dda",  # noqa: E501  # pragma: allowlist secret
    "unosat-analysis-extent.zip": (
        "7487b21cd2239cdb8c4913e31d3e08d1ce61462db032859bbfb853721e4424cb"  # noqa: E501  # pragma: allowlist secret
    ),
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def check_sources(source_dir: Path) -> dict[str, str]:
    actual: dict[str, str] = {}
    for filename, expected in EXPECTED.items():
        path = source_dir / filename
        if not path.is_file():
            raise FileNotFoundError(f"Required pinned source is missing: {path}")
        actual[filename] = sha256(path)
        if actual[filename] != expected:
            raise ValueError(f"Checksum mismatch for {filename}")
    return actual


def tile_xy(longitude: float, latitude: float, zoom: int) -> tuple[int, int]:
    scale = 2**zoom
    x = int((longitude + 180) / 360 * scale)
    latitude = max(min(latitude, 85.05112878), -85.05112878)
    radians = math.radians(latitude)
    y = int((1 - math.asinh(math.tan(radians)) / math.pi) / 2 * scale)
    return x, y


def tile_bounds_3857(x: int, y: int, zoom: int) -> tuple[float, float, float, float]:
    span = WEB_MERCATOR_LIMIT * 2 / 2**zoom
    left = -WEB_MERCATOR_LIMIT + x * span
    right = left + span
    top = WEB_MERCATOR_LIMIT - y * span
    bottom = top - span
    return left, bottom, right, top


def render_rgba(
    dataset: rasterio.io.DatasetReader,
    bounds_3857: tuple[float, float, float, float],
    width: int,
    height: int,
) -> np.ndarray[Any, np.dtype[np.uint8]]:
    rgb = np.zeros((3, height, width), dtype=np.uint8)
    destination_transform = from_bounds(*bounds_3857, width, height)
    for band in range(1, 4):
        reproject(
            source=rasterio.band(dataset, band),
            destination=rgb[band - 1],
            src_transform=dataset.transform,
            src_crs=dataset.crs,
            src_nodata=0,
            dst_transform=destination_transform,
            dst_crs="EPSG:3857",
            dst_nodata=0,
            resampling=Resampling.bilinear,
        )
    alpha = np.where(np.any(rgb != 0, axis=0), 255, 0).astype(np.uint8)
    return np.dstack((rgb[0], rgb[1], rgb[2], alpha))


def save_png(array: np.ndarray[Any, np.dtype[np.uint8]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(array, mode="RGBA").save(path, optimize=True)


def render_tiles(source: Path, output: Path) -> int:
    count = 0
    with rasterio.open(source) as dataset:
        for zoom in ZOOMS:
            min_x, max_y = tile_xy(AOI[0], AOI[1], zoom)
            max_x, min_y = tile_xy(AOI[2], AOI[3], zoom)
            for x in range(min_x, max_x + 1):
                for y in range(min_y, max_y + 1):
                    save_png(
                        render_rgba(dataset, tile_bounds_3857(x, y, zoom), TILE_SIZE, TILE_SIZE),
                        output / str(zoom) / str(x) / f"{y}.png",
                    )
                    count += 1
    return count


def render_thumbnail(source: Path, output: Path) -> None:
    left, bottom = transform("EPSG:4326", "EPSG:3857", [AOI[0]], [AOI[1]])
    right, top = transform("EPSG:4326", "EPSG:3857", [AOI[2]], [AOI[3]])
    with rasterio.open(source) as dataset:
        save_png(
            render_rgba(dataset, (left[0], bottom[0], right[0], top[0]), 720, 960),
            output,
        )


def simplify(points: list[list[float]], maximum_points: int = 500) -> list[list[float]]:
    if len(points) <= maximum_points:
        return points
    unclosed = points[:-1] if points[0] == points[-1] else points
    stride = math.ceil(len(unclosed) / (maximum_points - 1))
    result = unclosed[::stride]
    if result[0] != result[-1]:
        result.append(result[0])
    return result


def signed_area(ring: list[list[float]]) -> float:
    return (
        sum(
            ring[index][0] * ring[index + 1][1] - ring[index + 1][0] * ring[index][1]
            for index in range(len(ring) - 1)
        )
        / 2
    )


def overlaps_aoi(ring: list[list[float]]) -> bool:
    longitudes = [point[0] for point in ring]
    latitudes = [point[1] for point in ring]
    return not (
        max(longitudes) < AOI[0]
        or min(longitudes) > AOI[2]
        or max(latitudes) < AOI[1]
        or min(latitudes) > AOI[3]
    )


def focus_in_aoi(ring: list[list[float]]) -> list[float]:
    inside = [
        point for point in ring if AOI[0] <= point[0] <= AOI[2] and AOI[1] <= point[1] <= AOI[3]
    ]
    if not inside:
        raise ValueError("Reference geometry intersects the AOI without a usable focus point")
    return [
        round((min(p[0] for p in inside) + max(p[0] for p in inside)) / 2, 6),
        round((min(p[1] for p in inside) + max(p[1] for p in inside)) / 2, 6),
    ]


def source_observations(source_zip: Path) -> list[dict[str, Any]]:
    with tempfile.TemporaryDirectory() as temporary:
        with zipfile.ZipFile(source_zip) as archive:
            archive.extractall(temporary)
        shapefile_path = next(Path(temporary).glob("*.shp"))
        feature = shapefile.Reader(str(shapefile_path)).shape(0).__geo_interface__

    transformed = transform_geom("EPSG:32645", "EPSG:4326", feature, precision=7)
    polygons = (
        transformed["coordinates"]
        if transformed["type"] == "MultiPolygon"
        else [transformed["coordinates"]]
    )
    candidates: list[tuple[float, list[list[list[float]]]]] = []
    for polygon in polygons:
        outer = polygon[0]
        if overlaps_aoi(outer):
            candidates.append((abs(signed_area(outer)), polygon))
    candidates.sort(key=lambda value: value[0], reverse=True)
    observations = []
    for index, (_, polygon) in enumerate(candidates[:3], start=1):
        simplified = [simplify(ring) for ring in polygon]
        outer = simplified[0]
        focus = focus_in_aoi(polygon[0])
        observations.append(
            {
                "id": f"unosat-reference-area-{index}",
                "title": f"UNOSAT preliminary reference area {index}",
                "statement": (
                    "UNOSAT mapped this geometry within its preliminary satellite-detected "
                    "flood, mudflow, and rockflow extent."
                ),
                "geometry": {"type": "Polygon", "coordinates": simplified},
                "focus": focus,
                "evidenceReference": f"UNOSAT source feature 1, mapped part {index}",
                "citationId": "unosat-extent",
                "limitations": [
                    "UNOSAT labels the analysis preliminary and not field validated.",
                    "The source combines Sentinel-2 and PlanetScope interpretation; "
                    "EchoAtlas did not compute this geometry.",
                ],
            }
        )
    if len(observations) < 3:
        raise ValueError("The pinned UNOSAT source did not yield three AOI reference areas")
    return observations


def polygon_from_aoi() -> dict[str, Any]:
    west, south, east, north = AOI
    return {
        "type": "Polygon",
        "coordinates": [
            [[west, south], [east, south], [east, north], [west, north], [west, south]]
        ],
    }


def grid_residuals(source_dir: Path) -> list[float]:
    controls = [(85.31, 28.09), (85.41, 28.09), (85.36, 28.18), (85.31, 28.27), (85.41, 28.27)]
    with (
        rasterio.open(source_dir / "before-tci.tif") as before,
        rasterio.open(source_dir / "after-tci.tif") as after,
    ):
        if (
            before.crs != after.crs
            or before.transform != after.transform
            or before.shape != after.shape
        ):
            raise ValueError("Pinned acquisitions do not share the declared source grid")
        xs, ys = transform(
            "EPSG:4326", before.crs, [c[0] for c in controls], [c[1] for c in controls]
        )
        residuals = []
        for x, y in zip(xs, ys, strict=True):
            before_row, before_col = before.index(x, y)
            after_row, after_col = after.index(x, y)
            residuals.append(float(math.hypot(before_col - after_col, before_row - after_row) * 10))
    if any(value > 10 for value in residuals):
        raise ValueError("Shared-grid residual exceeds the approved 10 m tolerance")
    return residuals


def build_case(source_dir: Path, output_dir: Path, checksums: dict[str, str]) -> dict[str, Any]:
    residuals = grid_residuals(source_dir)
    return {
        "contractVersion": "1.0.0",
        "caseId": "nepal-flood-2026",
        "caseVersion": "1.0.0",
        "title": "Nepal flood investigation",
        "location": "Bhote Koshi–Trishuli corridor, Rasuwa, Nepal",
        "question": (
            "What does the cited satellite evidence support about the "
            "26 August 2026 flood corridor?"
        ),
        "event": {
            "occurredAt": "2026-08-26",
            "summary": (
                "A severe flash flood affected the Bhote Koshi–Trishuli river corridors. "
                "This prepared case compares fixed Sentinel-2 views from before "
                "and after the event."
            ),
        },
        "aoi": polygon_from_aoi(),
        "coverage": polygon_from_aoi(),
        "acquisitions": [
            {
                "role": "before",
                "itemId": "S2C_45RUM_20260812_0_L2A",
                "productId": "S2C_MSIL2A_20260812T045701_N0512_R119_T45RUM_20260812T100317.SAFE",
                "acquiredAt": "2026-08-12T05:10:48.070000Z",
                "tileTemplate": "/generated-nepal/tiles/before/{z}/{x}/{y}.png",
                "thumbnail": "/generated-nepal/before-thumbnail.png",
                "sourceUrl": "https://earth-search.aws.element84.com/v1/collections/sentinel-2-l2a/items/S2C_45RUM_20260812_0_L2A",
                "checksumSha256": checksums["before-tci.tif"],
                "crs": "EPSG:32645",
                "resolutionMetres": 10,
                "cloudCoverPercent": 18.746611,
                "cloudShadowPercent": 0.655973,
                "nodataPercent": 9.007575,
            },
            {
                "role": "after",
                "itemId": "S2B_45RUM_20260827_0_L2A",
                "productId": "S2B_MSIL2A_20260827T045659_N0512_R119_T45RUM_20260827T084453.SAFE",
                "acquiredAt": "2026-08-27T05:10:45.885000Z",
                "tileTemplate": "/generated-nepal/tiles/after/{z}/{x}/{y}.png",
                "thumbnail": "/generated-nepal/after-thumbnail.png",
                "sourceUrl": "https://earth-search.aws.element84.com/v1/collections/sentinel-2-l2a/items/S2B_45RUM_20260827_0_L2A",
                "checksumSha256": checksums["after-tci.tif"],
                "crs": "EPSG:32645",
                "resolutionMetres": 10,
                "cloudCoverPercent": 78.471315,
                "cloudShadowPercent": 0.469819,
                "nodataPercent": 8.594341,
            },
        ],
        "citations": [
            {
                "id": "who-event",
                "publisher": "World Health Organization",
                "title": "2026 Rasuwa flash floods",
                "url": "https://www.who.int/nepal/emergencies/2026-rasuwa-flash-floods",
                "accessedAt": "2026-09-07",
            },
            {
                "id": "esa-comparison",
                "publisher": "European Space Agency",
                "title": "Sentinel-2 captures before and after Nepal flash flood",
                "url": "https://www.esa.int/ESA_Multimedia/Images/2026/08/Sentinel-2_captures_before_and_after_Nepal_flash_flood",
                "accessedAt": "2026-09-07",
            },
            {
                "id": "unosat-extent",
                "publisher": "UNOSAT",
                "title": "Nepal: Satellite detected mudflow and rockflow extent",
                "url": "https://ihp-wins.unesco.org/dataset/nepal-satellite-detected-mudflow-and-rockflow-extent-nepal",
                "accessedAt": "2026-09-07",
            },
        ],
        "observations": source_observations(source_dir / "unosat-flood-extent.zip"),
        "attribution": [
            "Contains modified Copernicus Sentinel data (2026), accessed through "
            "Element 84 Earth Search.",
            "Preliminary reference geometry: UNOSAT, DOI 10.63253/1y26ihdq.",
            "Basemap: © OpenStreetMap contributors.",
        ],
        "quality": {
            "summary": (
                "Cloud and shadow obscure substantial parts of the 27 August image; "
                "conclusions are limited to visible areas."
            ),
            "limitations": [
                "The after scene reports 78.471315% cloud cover across the full Sentinel-2 tile.",
                "UNOSAT's reference geometry is preliminary and not field validated.",
                "A common source grid supports display alignment but does not establish "
                "absolute orthorectification accuracy.",
                "Panning changes location only; both acquisition dates remain fixed.",
            ],
            "alignmentToleranceMetres": 10,
            "measuredGridResidualMetres": residuals,
        },
        "preparedAt": datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "preparation": {
            "command": (
                "~/.local/bin/uv run --group processing python scripts/prepare_nepal_case.py"
            ),
            "sourceManifest": "/generated-nepal/source-manifest.json",
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-dir", type=Path, default=Path("data/raw/nepal-2026"))
    parser.add_argument(
        "--output-dir", type=Path, default=Path("apps/workbench/public/generated-nepal")
    )
    args = parser.parse_args()
    checksums = check_sources(args.source_dir)
    if args.output_dir.exists():
        shutil.rmtree(args.output_dir)
    args.output_dir.mkdir(parents=True)
    counts = {}
    for role in ("before", "after"):
        source = args.source_dir / f"{role}-tci.tif"
        counts[role] = render_tiles(source, args.output_dir / "tiles" / role)
        render_thumbnail(source, args.output_dir / f"{role}-thumbnail.png")
    case = build_case(args.source_dir, args.output_dir, checksums)
    source_manifest = {
        "manifestVersion": "1.0.0",
        "caseId": case["caseId"],
        "caseVersion": case["caseVersion"],
        "aoiWgs84": list(AOI),
        "zooms": [min(ZOOMS), max(ZOOMS)],
        "tileSize": TILE_SIZE,
        "tileCounts": counts,
        "sources": checksums,
        "gridResidualMetres": case["quality"]["measuredGridResidualMetres"],
    }
    (args.output_dir / "case.json").write_text(json.dumps(case, indent=2) + "\n")
    (args.output_dir / "source-manifest.json").write_text(
        json.dumps(source_manifest, indent=2) + "\n"
    )
    print(json.dumps(source_manifest, indent=2))


if __name__ == "__main__":
    main()
