from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pytest
import rasterio  # type: ignore[import-untyped]
from PIL import Image
from rasterio.transform import from_origin  # type: ignore[import-untyped]

from echoatlas.processor.acquisition.models import SelectionManifest, load_selection_manifest
from echoatlas.processor.previews.models import ProcessingParameters
from echoatlas.processor.previews.pipeline import (
    OutputExistsError,
    RasterValidationError,
    process_pair,
)


def _manifest(
    *, bbox: tuple[float, float, float, float] = (0.0, 0.0, 4.0, 4.0)
) -> SelectionManifest:
    west, south, east, north = bbox
    geometry: dict[str, object] = {
        "type": "Polygon",
        "coordinates": [
            [
                [west, south],
                [east, south],
                [east, north],
                [west, north],
                [west, south],
            ]
        ],
    }
    geometry_hash = hashlib.sha256(
        json.dumps(geometry, separators=(",", ":"), sort_keys=True).encode()
    ).hexdigest()

    def acquisition(role: str) -> dict[str, object]:
        return {
            "item_id": f"{role}-item",
            "acquired_at": "2025-01-01T00:00:00Z",
            "product_type": "GEC",
            "polarizations": ["VV"],
            "object": {
                "key": f"objects/{role}.tif",
                "url": f"https://data.example.test/objects/{role}.tif",
                "size_bytes": 1,
                "etag": f"{role}-etag",
                "checksum": {
                    "algorithm": "CRC64NVME",
                    "encoding": "base64",
                    "value": "AAAAAAAAAAA=",
                    "type": "FULL_OBJECT",
                },
            },
        }

    return SelectionManifest.model_validate(
        {
            "manifest_version": "1.0.0",
            "selection_id": "preview-test-v1",
            "status": "approved",
            "accessed_at": "2026-08-24T00:00:00Z",
            "license": {"spdx": "CC-BY-4.0", "provider": "Test Provider"},
            "processing_aoi": {
                "id": "test-aoi",
                "bbox": bbox,
                "geometry": geometry,
                "geometry_sha256": geometry_hash,
                "boundary": "Synthetic test area only.",
            },
            "acquisitions": {
                "before": acquisition("before"),
                "after": acquisition("after"),
            },
            "interpretation_limits": ["Synthetic engineering test only."],
            "sensitivity_controls": ["No public release."],
        }
    )


def _write_raster(
    path: Path,
    values: np.ndarray,
    *,
    crs: str | None = "EPSG:4326",
    nodata: float | None = 0,
    count: int = 1,
) -> None:
    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        width=values.shape[1],
        height=values.shape[0],
        count=count,
        dtype=values.dtype,
        crs=crs,
        transform=from_origin(-1, 5, 1, 1),
        nodata=nodata,
    ) as destination:
        for band in range(1, count + 1):
            destination.write(values, band)


def _sources(tmp_path: Path) -> tuple[dict[str, Path], np.ndarray]:
    values = np.arange(1, 37, dtype=np.uint8).reshape(6, 6)
    sources = {"before": tmp_path / "before.tif", "after": tmp_path / "after.tif"}
    _write_raster(sources["before"], values)
    _write_raster(sources["after"], values + 10)
    return sources, values


def test_process_pair_aligns_normalizes_and_records_provenance(tmp_path: Path) -> None:
    sources, before_values = _sources(tmp_path)
    parameters = ProcessingParameters(
        target_crs="EPSG:4326",
        target_resolution=1,
        lower_percentile=0,
        upper_percentile=100,
        thumbnail_max_size=64,
        min_valid_fraction=1,
    )

    result = process_pair(
        _manifest(), sources, output_root=tmp_path / "derived-a", parameters=parameters
    )

    assert result.output_directory.name == result.run_id
    with rasterio.open(result.output_directory / "aligned" / "before.tif") as aligned:
        assert aligned.crs.to_string() == "EPSG:4326"
        assert aligned.bounds == pytest.approx((0, 0, 4, 4))
        assert aligned.read(1) == pytest.approx(before_values[1:5, 1:5])
    with Image.open(result.output_directory / "previews" / "before.png") as preview:
        expected = np.rint((before_values[1:5, 1:5] - 8) / (29 - 8) * 254 + 1).astype(np.uint8)
        assert np.asarray(preview) == pytest.approx(expected, abs=1)
    with Image.open(result.output_directory / "thumbnails" / "before.png") as thumbnail:
        assert max(thumbnail.size) <= 64

    quality = json.loads(result.quality_report_path.read_text())
    assert quality["grid"]["aoi_pixel_count"] == 16
    assert quality["common_valid_fraction"] == 1
    assert quality["roles"][0]["normalization_low"] == pytest.approx(8)
    assert quality["roles"][0]["normalization_high"] == pytest.approx(29)
    assert len(quality["warnings"]) >= 4

    run_manifest = json.loads(result.manifest_path.read_text())
    assert run_manifest["parameters"]["filter"] == "none"
    assert run_manifest["parameters"]["resampling"] == "bilinear"
    assert run_manifest["interpretation_limits"] == ["Synthetic engineering test only."]
    assert run_manifest["sensitivity_controls"] == ["No public release."]
    assert {artifact["kind"] for artifact in run_manifest["artifacts"]} == {
        "aligned-raster",
        "preview",
        "thumbnail",
    }

    repeated = process_pair(
        _manifest(), sources, output_root=tmp_path / "derived-b", parameters=parameters
    )
    assert repeated.run_id == result.run_id
    assert [artifact.sha256 for artifact in repeated.artifacts] == [
        artifact.sha256 for artifact in result.artifacts
    ]

    with pytest.raises(OutputExistsError, match="already exists"):
        process_pair(
            _manifest(), sources, output_root=tmp_path / "derived-a", parameters=parameters
        )


@pytest.mark.parametrize(
    ("source_options", "message"),
    [
        ({"crs": None}, "missing a CRS"),
        ({"nodata": None}, "must declare nodata"),
        ({"count": 2}, "exactly one band"),
    ],
)
def test_process_pair_rejects_incompatible_rasters(
    tmp_path: Path, source_options: dict[str, object], message: str
) -> None:
    values = np.arange(1, 37, dtype=np.uint8).reshape(6, 6)
    before = tmp_path / "before.tif"
    after = tmp_path / "after.tif"
    _write_raster(before, values, **source_options)  # type: ignore[arg-type]
    _write_raster(after, values)

    with pytest.raises(RasterValidationError, match=message):
        process_pair(
            _manifest(),
            {"before": before, "after": after},
            output_root=tmp_path / "derived",
            parameters=ProcessingParameters(target_crs="EPSG:4326", target_resolution=1),
        )


def test_process_pair_rejects_corrupt_and_nonoverlapping_sources(tmp_path: Path) -> None:
    valid = np.arange(1, 37, dtype=np.uint8).reshape(6, 6)
    after = tmp_path / "after.tif"
    _write_raster(after, valid)
    corrupt = tmp_path / "before.tif"
    corrupt.write_bytes(b"not-a-tiff")

    with pytest.raises(RasterValidationError, match="could not be opened"):
        process_pair(
            _manifest(),
            {"before": corrupt, "after": after},
            output_root=tmp_path / "corrupt-output",
            parameters=ProcessingParameters(target_crs="EPSG:4326", target_resolution=1),
        )

    before = tmp_path / "before-valid.tif"
    _write_raster(before, valid)
    with pytest.raises(RasterValidationError, match="does not intersect"):
        process_pair(
            _manifest(bbox=(20, 20, 24, 24)),
            {"before": before, "after": after},
            output_root=tmp_path / "nonoverlap-output",
            parameters=ProcessingParameters(target_crs="EPSG:4326", target_resolution=1),
        )


def test_process_pair_rejects_insufficient_valid_aoi_coverage(tmp_path: Path) -> None:
    sparse = np.zeros((6, 6), dtype=np.uint8)
    sparse[2, 2] = 10
    before = tmp_path / "before.tif"
    after = tmp_path / "after.tif"
    _write_raster(before, sparse)
    _write_raster(after, sparse)

    with pytest.raises(RasterValidationError, match="valid AOI coverage"):
        process_pair(
            _manifest(),
            {"before": before, "after": after},
            output_root=tmp_path / "derived",
            parameters=ProcessingParameters(
                target_crs="EPSG:4326", target_resolution=1, min_valid_fraction=0.99
            ),
        )


def test_production_selection_manifest_satisfies_processing_contract() -> None:
    repository_root = Path(__file__).resolve().parents[3]
    manifest = load_selection_manifest(repository_root / "fixtures/demo/selection-manifest.v1.json")

    assert manifest.processing_aoi.id == "bingham-canyon-central-pit-v1"
    assert len(manifest.interpretation_limits) >= 1
    assert len(manifest.sensitivity_controls) >= 1
