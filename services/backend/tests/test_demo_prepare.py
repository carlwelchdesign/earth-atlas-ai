from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
from PIL import Image

from echoatlas.demo.prepare import (
    PreparedDemoInputError,
    PreparedDemoOutputExistsError,
    prepare_workbench_demo,
)
from echoatlas.processor.changes.models import (
    CandidateFeature,
    CandidateFeatureCollection,
    CandidateMeasurements,
    CandidateProperties,
    CandidateScoreComponents,
    ChangeArtifactRecord,
    ChangeParameters,
    ChangeRunManifest,
)
from echoatlas.processor.previews.models import (
    ArtifactRecord,
    GridRecord,
    ProcessingParameters,
    ProcessingRunManifest,
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, document: object) -> None:
    path.write_text(f"{json.dumps(document, sort_keys=True)}\n")


def _write_png(path: Path, *, size: tuple[int, int], color: int | tuple[int, int, int]) -> None:
    mode = "RGB" if isinstance(color, tuple) else "L"
    Image.new(mode, size, color).save(path)


def _source_runs(root: Path) -> tuple[Path, Path, Path]:
    selection_path = root / "selection.json"
    preview = root / "preview-test"
    change = root / "change-test"
    (preview / "thumbs").mkdir(parents=True)
    change.mkdir()

    geometry = {
        "type": "Polygon",
        "coordinates": [[[0, 0], [0.1, 0], [0.1, 0.1], [0, 0.1], [0, 0]]],
    }
    geometry_sha256 = hashlib.sha256(
        json.dumps(geometry, separators=(",", ":"), sort_keys=True).encode()
    ).hexdigest()
    acquisitions = {}
    for role, item_id, platform, checksum in (
        ("before", "before-item", "Umbra-01", "AAAAAAAAAAA="),
        ("after", "after-item", "Umbra-02", "AQEBAQEBAQE="),
    ):
        acquisitions[role] = {
            "item_id": item_id,
            "acquired_at": "2025-01-01T00:00:00Z" if role == "before" else "2025-02-01T00:00:00Z",
            "item_url": (
                f"https://umbra-open-data-catalog.s3.us-west-2.amazonaws.com/stac/{item_id}.json"
            ),
            "platform": platform,
            "product_type": "GEC",
            "polarizations": ["VV"],
            "resolution_range_m": 0.5,
            "incidence_angle_deg": 40,
            "object": {
                "key": f"imagery/{item_id}.tif",
                "url": (
                    "https://umbra-open-data-catalog.s3.us-west-2.amazonaws.com/"
                    f"imagery/{item_id}.tif"
                ),
                "size_bytes": 100,
                "etag": f"{item_id}-etag",
                "checksum": {
                    "algorithm": "CRC64NVME",
                    "encoding": "base64",
                    "value": checksum,
                    "type": "FULL_OBJECT",
                },
            },
        }
    selection = {
        "manifest_version": "1.0.0",
        "selection_id": "selection-test",
        "status": "approved",
        "accessed_at": "2026-01-01T00:00:00Z",
        "story": {"title": "Real satellite test"},
        "license": {"spdx": "CC-BY-4.0", "provider": "Umbra Lab Inc"},
        "processing_aoi": {
            "id": "aoi-test",
            "bbox": [0, 0, 0.1, 0.1],
            "geometry": geometry,
            "geometry_sha256": geometry_sha256,
            "boundary": "Test boundary",
        },
        "acquisitions": acquisitions,
        "interpretation_limits": ["Candidates are not findings."],
        "sensitivity_controls": ["Keep derived outputs local."],
    }
    _write_json(selection_path, selection)

    for role, color in (("before", 40), ("after", 70)):
        _write_png(preview / "thumbs" / f"{role}.png", size=(8, 10), color=color)
    _write_png(change / "score.png", size=(10, 10), color=50)
    _write_png(change / "overlay.png", size=(10, 10), color=(30, 50, 70))

    preview_records = tuple(
        ArtifactRecord(
            artifact_id=f"{role}-thumbnail",
            role=role,
            kind="thumbnail",
            relative_path=f"thumbs/{role}.png",
            media_type="image/png",
            sha256=_sha256(preview / "thumbs" / f"{role}.png"),
            size_bytes=(preview / "thumbs" / f"{role}.png").stat().st_size,
            width=8,
            height=10,
        )
        for role in ("before", "after")
    )
    quality_path = preview / "quality.json"
    _write_json(quality_path, {"warnings": []})
    processing = ProcessingRunManifest(
        run_id=preview.name,
        selection_id="selection-test",
        processing_aoi_id="aoi-test",
        processing_aoi_geometry_sha256=geometry_sha256,
        source_license={"provider": "Umbra Lab Inc", "spdx": "CC-BY-4.0"},
        inputs=(
            {"role": "before", "item_id": "before-item"},
            {"role": "after", "item_id": "after-item"},
        ),
        parameters=ProcessingParameters(target_crs="EPSG:3857"),
        grid=GridRecord(
            crs="EPSG:3857",
            resolution=1,
            width=10,
            height=10,
            bounds=(0, 0, 10, 10),
            transform=(1, 0, 0, 0, -1, 10, 0, 0, 1),
            aoi_pixel_count=100,
        ),
        software={"echoatlas": "test"},
        artifacts=preview_records,
        quality_report={
            "relative_path": "quality.json",
            "sha256": _sha256(quality_path),
            "size_bytes": quality_path.stat().st_size,
        },
        interpretation_limits=("Candidates are not findings.",),
        sensitivity_controls=("Keep derived outputs local.",),
    )
    processing_path = preview / "processing-manifest.json"
    _write_json(processing_path, processing.model_dump(mode="json"))

    feature = CandidateFeature(
        id="change-test-candidate-0001",
        geometry={
            "type": "Polygon",
            "coordinates": [[[2, 3], [4, 3], [4, 6], [2, 6], [2, 3]]],
        },
        properties=CandidateProperties(
            candidate_id="change-test-candidate-0001",
            change_run_id=change.name,
            source_processing_run_id=preview.name,
            measurements=CandidateMeasurements(
                pixel_count=6,
                area_square_meters=6,
                projected_bbox=(2, 3, 4, 6),
                wgs84_bbox=(0.02, 0.03, 0.04, 0.06),
            ),
            score_components=CandidateScoreComponents(
                mean_change_score=0.7,
                p95_change_score=0.8,
                max_change_score=0.9,
                mean_signed_normalized_delta=0.2,
                brightening_pixel_fraction=0.75,
                darkening_pixel_fraction=0.25,
            ),
            warnings=("Machine candidate pending review.",),
        ),
    )
    candidates = CandidateFeatureCollection(
        change_run_id=change.name,
        source_processing_run_id=preview.name,
        warnings=("Collection warning.",),
        features=(feature,),
    )
    candidate_path = change / "candidates.geojson"
    _write_json(candidate_path, candidates.model_dump(mode="json"))

    change_artifacts = []
    for artifact_id, kind, relative_path, media_type in (
        ("change-score-preview", "change-score-preview", "score.png", "image/png"),
        ("candidate-overlay", "candidate-overlay", "overlay.png", "image/png"),
        (
            "candidate-geojson",
            "candidate-geojson",
            "candidates.geojson",
            "application/geo+json",
        ),
    ):
        path = change / relative_path
        change_artifacts.append(
            ChangeArtifactRecord(
                artifact_id=artifact_id,
                kind=kind,
                relative_path=relative_path,
                media_type=media_type,
                sha256=_sha256(path),
                size_bytes=path.stat().st_size,
            )
        )
    change_manifest = ChangeRunManifest(
        change_run_id=change.name,
        source_processing_run_id=preview.name,
        source_processing_manifest_sha256=_sha256(processing_path),
        source_quality_report_sha256=_sha256(quality_path),
        source_aligned_artifacts=(
            {"role": "before", "artifact_id": "before-aligned"},
            {"role": "after", "artifact_id": "after-aligned"},
        ),
        software={"echoatlas": "0.1.0", "commit": "a" * 40},
        parameters=ChangeParameters(),
        common_valid_pixel_count=100,
        threshold_pixel_count=6,
        cleaned_pixel_count=6,
        candidate_pixel_count=6,
        candidate_count=1,
        artifacts=tuple(change_artifacts),
        warnings=("Candidates remain unreviewed.",),
    )
    _write_json(change / "change-manifest.json", change_manifest.model_dump(mode="json"))
    return selection_path, preview, change


def test_prepares_satellite_bundle_without_raw_rasters(tmp_path: Path) -> None:
    selection, preview, change = _source_runs(tmp_path)
    output = tmp_path / "generated-demo"

    result = prepare_workbench_demo(
        selection_manifest_path=selection,
        preview_run=preview,
        change_run=change,
        output_directory=output,
    )

    assert result.candidate_count == 1
    assert sorted(path.name for path in output.iterdir()) == [
        "after.png",
        "before.png",
        "bundle.json",
        "candidate-overlay.png",
        "candidates.geojson",
        "change-score.png",
        "prepared-demo-manifest.json",
    ]
    assert not list(output.rglob("*.tif"))
    bundle = json.loads(result.bundle_path.read_text())
    assert bundle["evidence"]["lineage"] == "satellite-derived"
    assert bundle["mission"]["title"] == "Real satellite test"
    assert bundle["acquisitions"][0]["artifact"]["src"] == "/generated-demo/before.png"
    assert bundle["candidates"][0]["mapPosition"] == {
        "heightPercent": 30.0,
        "leftPercent": 20.0,
        "rotationDegrees": 0,
        "topPercent": 40.0,
        "widthPercent": 20.0,
    }
    assert bundle["evidence"]["acquisitions"][0]["provider"] == ("Umbra Lab Inc · Umbra-01")


def test_rejects_changed_declared_artifact(tmp_path: Path) -> None:
    selection, preview, change = _source_runs(tmp_path)
    (preview / "thumbs" / "before.png").write_bytes(b"changed")

    with pytest.raises(PreparedDemoInputError, match="artifact size changed"):
        prepare_workbench_demo(
            selection_manifest_path=selection,
            preview_run=preview,
            change_run=change,
            output_directory=tmp_path / "generated-demo",
        )


def test_rejects_mismatched_candidate_lineage(tmp_path: Path) -> None:
    selection, preview, change = _source_runs(tmp_path)
    document = json.loads((change / "candidates.geojson").read_text())
    document["source_processing_run_id"] = "other-run"
    _write_json(change / "candidates.geojson", document)
    manifest = json.loads((change / "change-manifest.json").read_text())
    record = next(item for item in manifest["artifacts"] if item["kind"] == "candidate-geojson")
    record["sha256"] = _sha256(change / "candidates.geojson")
    record["size_bytes"] = (change / "candidates.geojson").stat().st_size
    _write_json(change / "change-manifest.json", manifest)

    with pytest.raises(PreparedDemoInputError, match="candidate collection does not match"):
        prepare_workbench_demo(
            selection_manifest_path=selection,
            preview_run=preview,
            change_run=change,
            output_directory=tmp_path / "generated-demo",
        )


def test_refuses_to_overwrite_prepared_output(tmp_path: Path) -> None:
    selection, preview, change = _source_runs(tmp_path)
    output = tmp_path / "generated-demo"
    output.mkdir()

    with pytest.raises(PreparedDemoOutputExistsError):
        prepare_workbench_demo(
            selection_manifest_path=selection,
            preview_run=preview,
            change_run=change,
            output_directory=output,
        )
