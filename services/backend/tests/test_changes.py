from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import cast

import numpy as np
import pytest
import rasterio  # type: ignore[import-untyped]
from affine import Affine
from rasterio.transform import from_origin  # type: ignore[import-untyped]

from echoatlas.processor.changes.models import ChangeParameters
from echoatlas.processor.changes.pipeline import (
    CandidateLimitError,
    ChangeInputError,
    ChangeOutputExistsError,
    process_change_candidates,
)
from echoatlas.processor.previews.models import (
    ArtifactRecord,
    GridRecord,
    ProcessingParameters,
    ProcessingRunManifest,
    QualityReport,
    RasterSourceRecord,
    RoleQualityRecord,
)

TEST_COMMIT = "a" * 40


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_aligned(path: Path, values: np.ndarray, transform: Affine) -> None:
    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        width=values.shape[1],
        height=values.shape[0],
        count=1,
        dtype="float32",
        crs="EPSG:3857",
        transform=transform,
        nodata=np.nan,
    ) as destination:
        destination.write(values.astype(np.float32), 1)


def _source_record(role: str, shape: tuple[int, int], transform: Affine) -> RasterSourceRecord:
    height, width = shape
    return RasterSourceRecord.model_validate(
        {
            "role": role,
            "item_id": f"{role}-item",
            "file_name": f"{role}.tif",
            "driver": "GTiff",
            "crs": "EPSG:3857",
            "dtype": "float32",
            "width": width,
            "height": height,
            "count": 1,
            "transform": tuple(transform),
            "resolution": [1, 1],
            "bounds": [0, 0, width, height],
            "wgs84_bounds": [0, 0, 0.001, 0.001],
            "nodata": "NaN",
            "color_interpretation": "gray",
            "rotated_transform": False,
        }
    )


def _preview_run(
    root: Path,
    before: np.ndarray,
    after: np.ndarray,
    *,
    after_transform: Affine | None = None,
) -> Path:
    run = root / "preview-test-run"
    aligned = run / "aligned"
    aligned.mkdir(parents=True)
    transform = from_origin(0, before.shape[0], 1, 1)
    _write_aligned(aligned / "before.tif", before, transform)
    _write_aligned(aligned / "after.tif", after, after_transform or transform)
    height, width = before.shape
    artifacts = tuple(
        ArtifactRecord(
            artifact_id=f"{role}-aligned-raster",
            role=cast(str, role),
            kind="aligned-raster",
            relative_path=f"aligned/{role}.tif",
            media_type="image/tiff",
            sha256=_sha256(aligned / f"{role}.tif"),
            size_bytes=(aligned / f"{role}.tif").stat().st_size,
            width=width,
            height=height,
        )
        for role in ("before", "after")
    )
    grid = GridRecord(
        crs="EPSG:3857",
        resolution=1,
        width=width,
        height=height,
        bounds=(0, 0, width, height),
        transform=cast(
            tuple[float, float, float, float, float, float, float, float, float],
            tuple(transform),
        ),
        aoi_pixel_count=width * height,
    )
    valid_counts = {
        "before": int(np.count_nonzero(np.isfinite(before))),
        "after": int(np.count_nonzero(np.isfinite(after))),
    }
    roles = tuple(
        RoleQualityRecord(
            role=cast(str, role),
            valid_pixel_count=valid_counts[role],
            aoi_pixel_count=width * height,
            valid_fraction=valid_counts[role] / (width * height),
            value_min=float(np.nanmin(values)),
            value_max=float(np.nanmax(values)),
            normalization_low=0,
            normalization_high=100,
        )
        for role, values in (("before", before), ("after", after))
    )
    quality = QualityReport(
        run_id=run.name,
        selection_id="change-test-v1",
        grid=grid,
        sources=cast(
            tuple[RasterSourceRecord, RasterSourceRecord],
            (
                _source_record("before", before.shape, transform),
                _source_record("after", after.shape, after_transform or transform),
            ),
        ),
        roles=cast(tuple[RoleQualityRecord, RoleQualityRecord], roles),
        common_valid_pixel_count=int(np.count_nonzero(np.isfinite(before) & np.isfinite(after))),
        common_valid_fraction=float(np.mean(np.isfinite(before) & np.isfinite(after))),
        warnings=("Synthetic source run.",),
    )
    quality_path = run / "quality-report.json"
    quality_path.write_text(
        f"{json.dumps(quality.model_dump(mode='json'), indent=2, sort_keys=True)}\n"
    )
    manifest = ProcessingRunManifest(
        run_id=run.name,
        selection_id="change-test-v1",
        processing_aoi_id="change-test-aoi",
        processing_aoi_geometry_sha256="a" * 64,
        source_license={"spdx": "CC-BY-4.0", "provider": "Test Provider"},
        inputs=cast(
            tuple[dict[str, object], dict[str, object]],
            ({"role": "before"}, {"role": "after"}),
        ),
        parameters=ProcessingParameters(target_crs="EPSG:3857", target_resolution=1),
        grid=grid,
        software={"echoatlas": "test"},
        artifacts=cast(tuple[ArtifactRecord, ...], artifacts),
        quality_report={
            "relative_path": "quality-report.json",
            "sha256": _sha256(quality_path),
            "size_bytes": quality_path.stat().st_size,
        },
        interpretation_limits=("Synthetic engineering test only.",),
        sensitivity_controls=("No public release.",),
    )
    (run / "processing-manifest.json").write_text(
        f"{json.dumps(manifest.model_dump(mode='json'), indent=2, sort_keys=True)}\n"
    )
    return run


def _parameters(**overrides: object) -> ChangeParameters:
    defaults: dict[str, object] = {
        "score_threshold": 0.5,
        "registration_tolerance_pixels": 0,
        "opening_iterations": 0,
        "closing_iterations": 0,
        "minimum_component_pixels": 4,
        "maximum_candidate_count": 20,
    }
    defaults.update(overrides)
    return ChangeParameters.model_validate(defaults)


def test_change_pipeline_emits_pending_candidate_geojson_and_reproducible_artifacts(
    tmp_path: Path,
) -> None:
    before = np.full((24, 24), 20, dtype=np.float32)
    after = before.copy()
    after[8:16, 9:17] = 90
    source = _preview_run(tmp_path / "source-a", before, after)

    result = process_change_candidates(
        source,
        output_root=tmp_path / "changes-a",
        software_commit=TEST_COMMIT,
        parameters=_parameters(),
    )

    manifest = json.loads(result.manifest_path.read_text())
    assert manifest["display_label"] == "Change candidates"
    assert manifest["candidate_count"] == 1
    assert manifest["candidate_pixel_count"] == 64
    assert manifest["parameters"]["score_threshold"] == 0.5
    assert manifest["software"]["commit"] == TEST_COMMIT
    assert len(manifest["artifacts"]) == 5

    candidates = json.loads(result.candidates_path.read_text())
    assert candidates["type"] == "FeatureCollection"
    assert candidates["display_label"] == "Change candidates"
    assert len(candidates["features"]) == 1
    feature = candidates["features"][0]
    assert feature["properties"]["display_label"] == "Change candidate"
    assert feature["properties"]["status"] == "pending"
    assert feature["properties"]["change_run_id"] == result.change_run_id
    assert feature["properties"]["source_processing_run_id"] == "preview-test-run"
    assert feature["properties"]["measurements"]["pixel_count"] == 64
    assert feature["properties"]["measurements"]["area_square_meters"] == 64
    assert feature["properties"]["score_components"]["mean_change_score"] == pytest.approx(0.7)
    assert feature["geometry"]["type"] == "Polygon"
    assert len(feature["properties"]["warnings"]) == 3
    serialized_candidates = result.candidates_path.read_text().lower()
    assert "confirmed change" not in serialized_candidates
    assert "damage" not in serialized_candidates

    second_source = _preview_run(tmp_path / "source-b", before, after)
    repeated = process_change_candidates(
        second_source,
        output_root=tmp_path / "changes-b",
        software_commit=TEST_COMMIT,
        parameters=_parameters(),
    )
    assert repeated.change_run_id == result.change_run_id
    assert [artifact.sha256 for artifact in repeated.artifacts] == [
        artifact.sha256 for artifact in result.artifacts
    ]

    with pytest.raises(ChangeOutputExistsError, match="already exists"):
        process_change_candidates(
            source,
            output_root=tmp_path / "changes-a",
            software_commit=TEST_COMMIT,
            parameters=_parameters(),
        )


def test_speckle_and_nodata_boundaries_do_not_create_candidates(tmp_path: Path) -> None:
    before = np.full((20, 20), 20, dtype=np.float32)
    after = before.copy()
    after[10, 10] = 100
    after[:, -1] = np.nan
    source = _preview_run(tmp_path / "source", before, after)

    result = process_change_candidates(
        source,
        output_root=tmp_path / "changes",
        software_commit=TEST_COMMIT,
        parameters=_parameters(opening_iterations=1, minimum_component_pixels=1),
    )

    manifest = json.loads(result.manifest_path.read_text())
    assert manifest["threshold_pixel_count"] == 1
    assert manifest["cleaned_pixel_count"] == 0
    assert manifest["candidate_count"] == 0
    assert json.loads(result.candidates_path.read_text())["features"] == []


def test_one_pixel_registration_tolerance_suppresses_simple_shift_edges(tmp_path: Path) -> None:
    before = np.full((20, 20), 10, dtype=np.float32)
    before[5:15, 5:10] = 90
    after = np.full((20, 20), 10, dtype=np.float32)
    after[5:15, 6:11] = 90
    source = _preview_run(tmp_path / "source", before, after)

    without_tolerance = process_change_candidates(
        source,
        output_root=tmp_path / "without-tolerance",
        software_commit=TEST_COMMIT,
        parameters=_parameters(registration_tolerance_pixels=0, minimum_component_pixels=1),
    )
    with_tolerance = process_change_candidates(
        source,
        output_root=tmp_path / "with-tolerance",
        software_commit=TEST_COMMIT,
        parameters=_parameters(registration_tolerance_pixels=1, minimum_component_pixels=1),
    )

    assert json.loads(without_tolerance.manifest_path.read_text())["candidate_count"] == 2
    assert json.loads(with_tolerance.manifest_path.read_text())["candidate_count"] == 0


def test_diagonal_pixels_follow_declared_connectivity(tmp_path: Path) -> None:
    before = np.full((12, 12), 10, dtype=np.float32)
    after = before.copy()
    after[5, 5] = 90
    after[6, 6] = 90
    source = _preview_run(tmp_path / "source", before, after)

    connected = process_change_candidates(
        source,
        output_root=tmp_path / "connected",
        software_commit=TEST_COMMIT,
        parameters=_parameters(connectivity=8, minimum_component_pixels=1),
    )
    separated = process_change_candidates(
        source,
        output_root=tmp_path / "separated",
        software_commit=TEST_COMMIT,
        parameters=_parameters(connectivity=4, minimum_component_pixels=1),
    )

    assert json.loads(connected.manifest_path.read_text())["candidate_count"] == 1
    assert json.loads(separated.manifest_path.read_text())["candidate_count"] == 2


def test_changed_hash_grid_and_manifest_are_rejected(tmp_path: Path) -> None:
    values = np.full((12, 12), 20, dtype=np.float32)
    changed_hash = _preview_run(tmp_path / "hash", values, values)
    with (changed_hash / "aligned" / "before.tif").open("ab") as handle:
        handle.write(b"changed")
    with pytest.raises(ChangeInputError, match="size changed"):
        process_change_candidates(
            changed_hash,
            output_root=tmp_path / "hash-output",
            software_commit=TEST_COMMIT,
            parameters=_parameters(),
        )

    changed_grid = _preview_run(
        tmp_path / "grid",
        values,
        values,
        after_transform=from_origin(1, values.shape[0], 1, 1),
    )
    with pytest.raises(ChangeInputError, match="transform changed"):
        process_change_candidates(
            changed_grid,
            output_root=tmp_path / "grid-output",
            software_commit=TEST_COMMIT,
            parameters=_parameters(),
        )

    changed_manifest = _preview_run(tmp_path / "manifest", values, values)
    document = json.loads((changed_manifest / "processing-manifest.json").read_text())
    document["run_id"] = "different-run"
    (changed_manifest / "processing-manifest.json").write_text(json.dumps(document))
    with pytest.raises(ChangeInputError, match="does not match its directory"):
        process_change_candidates(
            changed_manifest,
            output_root=tmp_path / "manifest-output",
            software_commit=TEST_COMMIT,
            parameters=_parameters(),
        )


def test_candidate_limit_fails_closed(tmp_path: Path) -> None:
    before = np.zeros((16, 16), dtype=np.float32)
    after = before.copy()
    after[2, 2] = 100
    after[2, 12] = 100
    source = _preview_run(tmp_path / "source", before, after)

    with pytest.raises(CandidateLimitError, match="above the configured maximum"):
        process_change_candidates(
            source,
            output_root=tmp_path / "changes",
            software_commit=TEST_COMMIT,
            parameters=_parameters(minimum_component_pixels=1, maximum_candidate_count=1),
        )
