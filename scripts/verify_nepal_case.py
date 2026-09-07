#!/usr/bin/env python3
"""Verify the prepared Nepal release assets against their source manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

from PIL import Image


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def tile_xy(longitude: float, latitude: float, zoom: int) -> tuple[int, int]:
    scale = 2**zoom
    x = int((longitude + 180) / 360 * scale)
    latitude_radians = math.radians(latitude)
    y = int((1 - math.asinh(math.tan(latitude_radians)) / math.pi) / 2 * scale)
    return x, y


def expected_tiles(aoi: list[float], zooms: list[int]) -> set[tuple[int, int, int]]:
    west, south, east, north = aoi
    expected: set[tuple[int, int, int]] = set()
    for zoom in range(zooms[0], zooms[1] + 1):
        min_x, max_y = tile_xy(west, south, zoom)
        max_x, min_y = tile_xy(east, north, zoom)
        for x in range(min_x, max_x + 1):
            for y in range(min_y, max_y + 1):
                expected.add((zoom, x, y))
    return expected


def verify_role(generated: Path, role: str, expected: set[tuple[int, int, int]]) -> dict:
    tile_root = generated / "tiles" / role
    actual = {
        (int(path.parents[1].name), int(path.parent.name), int(path.stem))
        for path in tile_root.glob("*/*/*.png")
    }
    if actual != expected:
        raise ValueError(f"{role} tile coordinates do not match the declared AOI")

    transparent = 0
    opaque = 0
    for path in tile_root.glob("*/*/*.png"):
        with Image.open(path) as image:
            if image.mode != "RGBA" or image.size != (256, 256):
                raise ValueError(f"invalid tile format: {path}")
            alpha = image.getchannel("A")
            minimum, maximum = alpha.getextrema()
            transparent += int(minimum < 255)
            opaque += int(maximum > 0)
    if transparent == 0 or opaque != len(expected):
        raise ValueError(f"{role} tiles do not preserve transparent nodata and imagery")
    return {
        "tileCount": len(actual),
        "tilesWithTransparency": transparent,
        "tilesWithImagery": opaque,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-dir", type=Path, default=Path("data/raw/nepal-2026"))
    parser.add_argument(
        "--generated-dir",
        type=Path,
        default=Path("apps/workbench/public/generated-nepal"),
    )
    args = parser.parse_args()

    manifest = json.loads((args.generated_dir / "source-manifest.json").read_text())
    case = json.loads((args.generated_dir / "case.json").read_text())
    if manifest["caseId"] != case["caseId"] or manifest["caseVersion"] != case["caseVersion"]:
        raise ValueError("case identity differs between manifests")

    verified_sources = {}
    for name, expected_hash in manifest["sources"].items():
        actual_hash = sha256(args.source_dir / name)
        if actual_hash != expected_hash:
            raise ValueError(f"source checksum changed: {name}")
        verified_sources[name] = actual_hash

    tolerance = case["quality"]["alignmentToleranceMetres"]
    residuals = manifest["gridResidualMetres"]
    if len(residuals) != 5 or max(residuals) > tolerance:
        raise ValueError("five-point grid alignment is outside tolerance")
    if len(case["attribution"]) < 3 or not any(
        "Copernicus Sentinel" in entry for entry in case["attribution"]
    ):
        raise ValueError("required source attribution is missing")

    expected = expected_tiles(manifest["aoiWgs84"], manifest["zooms"])
    roles = {role: verify_role(args.generated_dir, role, expected) for role in ("before", "after")}
    for role in roles:
        if roles[role]["tileCount"] != manifest["tileCounts"][role]:
            raise ValueError(f"{role} tile count differs from manifest")
        with Image.open(args.generated_dir / f"{role}-thumbnail.png") as image:
            if image.width < 640 or image.height < 640:
                raise ValueError(f"{role} thumbnail is too small")

    print(
        json.dumps(
            {
                "case": f"{case['caseId']}@{case['caseVersion']}",
                "sources": verified_sources,
                "aoiWgs84": manifest["aoiWgs84"],
                "zooms": manifest["zooms"],
                "roles": roles,
                "alignmentToleranceMetres": tolerance,
                "gridResidualMetres": residuals,
                "attributionEntries": len(case["attribution"]),
                "status": "verified",
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
