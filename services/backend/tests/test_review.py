from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
from PIL import Image

from echoatlas.evaluation.review import (
    ReviewInputError,
    ReviewOutputExistsError,
    prepare_review_packet,
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


def _write_image(path: Path, color: int | tuple[int, int, int]) -> None:
    mode = "RGB" if isinstance(color, tuple) else "L"
    Image.new(mode, (10, 10), color).save(path)


def _source_runs(root: Path) -> tuple[Path, Path]:
    preview = root / "preview-test"
    change = root / "change-test"
    preview.mkdir(parents=True)
    change.mkdir(parents=True)
    _write_image(preview / "before.png", 40)
    _write_image(preview / "after.png", 70)
    _write_image(change / "overlay.png", (30, 50, 70))
    grid = GridRecord(
        crs="EPSG:3857",
        resolution=1,
        width=10,
        height=10,
        bounds=(0, 0, 10, 10),
        transform=(1, 0, 0, 0, -1, 10, 0, 0, 1),
        aoi_pixel_count=100,
    )
    preview_records = tuple(
        ArtifactRecord(
            artifact_id=f"{role}-preview",
            role=role,
            kind="preview",
            relative_path=f"{role}.png",
            media_type="image/png",
            sha256=_sha256(preview / f"{role}.png"),
            size_bytes=(preview / f"{role}.png").stat().st_size,
            width=10,
            height=10,
        )
        for role in ("before", "after")
    )
    processing = ProcessingRunManifest.model_validate(
        {
            "run_id": preview.name,
            "selection_id": "review-fixture-v1",
            "processing_aoi_id": "review-aoi-v1",
            "processing_aoi_geometry_sha256": "a" * 64,
            "source_license": {"provider": "Test provider", "spdx": "CC0-1.0"},
            "inputs": [
                {"role": "before", "item_id": "before-source"},
                {"role": "after", "item_id": "after-source"},
            ],
            "parameters": ProcessingParameters().model_dump(mode="json"),
            "grid": grid.model_dump(mode="json"),
            "software": {"echoatlas": "test"},
            "artifacts": [record.model_dump(mode="json") for record in preview_records],
            "quality_report": {
                "relative_path": "quality.json",
                "sha256": "placeholder",
                "size_bytes": 1,
            },
            "interpretation_limits": ["Test candidates are not findings."],
            "sensitivity_controls": ["Keep test packet local."],
        }
    )
    quality_path = preview / "quality.json"
    quality_path.write_text('{"quality":"synthetic test"}\n')
    processing_document = processing.model_dump(mode="json")
    processing_document["quality_report"] = {
        "relative_path": "quality.json",
        "sha256": _sha256(quality_path),
        "size_bytes": quality_path.stat().st_size,
    }
    (preview / "processing-manifest.json").write_text(json.dumps(processing_document))
    feature = CandidateFeature(
        id="change-test-candidate-0001",
        geometry={
            "type": "Polygon",
            "coordinates": [[[1, 1], [3, 1], [3, 3], [1, 3], [1, 1]]],
        },
        properties=CandidateProperties(
            candidate_id="change-test-candidate-0001",
            change_run_id=change.name,
            source_processing_run_id=preview.name,
            measurements=CandidateMeasurements(
                pixel_count=4,
                area_square_meters=4,
                projected_bbox=(1, 1, 3, 3),
                wgs84_bbox=(0, 0, 0.1, 0.1),
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
    collection = CandidateFeatureCollection(
        change_run_id=change.name,
        source_processing_run_id=preview.name,
        warnings=("Test collection.",),
        features=(feature,),
    )
    candidate_path = change / "candidates.geojson"
    candidate_path.write_text(json.dumps(collection.model_dump(mode="json")))
    change_records = (
        ChangeArtifactRecord(
            artifact_id="candidate-overlay",
            kind="candidate-overlay",
            relative_path="overlay.png",
            media_type="image/png",
            sha256=_sha256(change / "overlay.png"),
            size_bytes=(change / "overlay.png").stat().st_size,
        ),
        ChangeArtifactRecord(
            artifact_id="candidate-geojson",
            kind="candidate-geojson",
            relative_path="candidates.geojson",
            media_type="application/geo+json",
            sha256=_sha256(candidate_path),
            size_bytes=candidate_path.stat().st_size,
        ),
    )
    manifest = ChangeRunManifest(
        change_run_id=change.name,
        source_processing_run_id=preview.name,
        source_processing_manifest_sha256=_sha256(preview / "processing-manifest.json"),
        source_quality_report_sha256=_sha256(quality_path),
        source_aligned_artifacts=({}, {}),
        software={"echoatlas": "test"},
        parameters=ChangeParameters(),
        common_valid_pixel_count=100,
        threshold_pixel_count=4,
        cleaned_pixel_count=4,
        candidate_pixel_count=4,
        candidate_count=1,
        artifacts=change_records,
        warnings=("Test run.",),
    )
    (change / "change-manifest.json").write_text(json.dumps(manifest.model_dump(mode="json")))
    return change, preview


def test_review_packet_preserves_lineage_and_references_local_images(tmp_path: Path) -> None:
    change, preview = _source_runs(tmp_path / "source")
    output = tmp_path / "review" / "packet"

    packet = prepare_review_packet(change, preview, output)

    assert packet.change_run_id == change.name
    assert packet.processing_run_id == preview.name
    assert len(packet.candidates) == 1
    assert [artifact.role for artifact in packet.artifacts] == [
        "before",
        "after",
        "candidate-overlay",
    ]
    assert all(artifact.source_url.startswith("../../source/") for artifact in packet.artifacts)
    html = (output / "index.html").read_text()
    assert "Candidate decisions are not independent reference regions" in html
    assert "supported-needs-independent-reference" in html
    assert "localStorage" in html
    assert not list(output.glob("*.png"))


def test_review_packet_rejects_modified_artifact(tmp_path: Path) -> None:
    change, preview = _source_runs(tmp_path / "source")
    with (preview / "before.png").open("ab") as handle:
        handle.write(b"modified")

    with pytest.raises(ReviewInputError, match="artifact size changed"):
        prepare_review_packet(change, preview, tmp_path / "packet")


def test_review_packet_rejects_modified_processing_manifest(tmp_path: Path) -> None:
    change, preview = _source_runs(tmp_path / "source")
    document = json.loads((preview / "processing-manifest.json").read_text())
    document["run_id"] = "different-preview"
    (preview / "processing-manifest.json").write_text(json.dumps(document))

    with pytest.raises(ReviewInputError, match="processing manifest checksum"):
        prepare_review_packet(change, preview, tmp_path / "packet")


def test_review_packet_never_overwrites_existing_output(tmp_path: Path) -> None:
    change, preview = _source_runs(tmp_path / "source")
    output = tmp_path / "packet"
    output.mkdir()

    with pytest.raises(ReviewOutputExistsError, match="already exists"):
        prepare_review_packet(change, preview, output)
