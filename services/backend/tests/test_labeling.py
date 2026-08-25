from __future__ import annotations

import json
from pathlib import Path

import pytest

from echoatlas.evaluation.labeling import (
    LabelingValidationError,
    validate_labeling_export,
)

PACKET_ID = "labeling-" + "a" * 20
PROCESSING_RUN_ID = "preview-test"
MANIFEST_SHA256 = "b" * 64


def _packet_document() -> dict[str, object]:
    return {
        "labeling_packet_version": "1.0.0",
        "packet_id": PACKET_ID,
        "selection_id": "selection-test",
        "processing_aoi_id": "aoi-test",
        "processing_run_id": PROCESSING_RUN_ID,
        "source_processing_manifest_sha256": MANIFEST_SHA256,
        "source_license": {"provider": "Test", "spdx": "CC0-1.0"},
        "source_inputs": [
            {"role": "before", "item_id": "before-test"},
            {"role": "after", "item_id": "after-test"},
        ],
        "grid": {
            "crs": "EPSG:3857",
            "resolution": 1,
            "width": 10,
            "height": 10,
            "bounds": [0, 0, 10, 10],
            "transform": [1, 0, 0, 0, -1, 10, 0, 0, 1],
            "aoi_pixel_count": 100,
        },
        "artifacts": [
            {
                "role": role,
                "source_url": f"../../preview/{role}.png",
                "sha256": character * 64,
                "width": 10,
                "height": 10,
            }
            for role, character in (("before", "c"), ("after", "d"))
        ],
        "tiles": [{"tile_id": "T-001", "row": 1, "column": 1, "source_box": [0, 0, 10, 10]}],
        "tile_size": 768,
        "tile_overlap": 64,
        "interpretation_limits": ["Test-only imagery."],
        "sensitivity_controls": ["Keep local."],
        "labeling_boundary": "Candidates are absent; regions remain provisional.",
    }


def _region() -> dict[str, object]:
    points = [[1, 9], [3, 9], [3, 7]]
    return {
        "region_id": "T-001-R-01",
        "tile_id": "T-001",
        "points": points,
        "created_at": "2026-08-25T04:00:00Z",
        "review_status": "provisional-candidate-hidden",
        "geometry_crs": "EPSG:3857",
        "geometry": {
            "type": "Polygon",
            "coordinates": [[*points, points[0]]],
        },
        "projected_points": points,
        "pixel_points": [[1, 1], [3, 1], [3, 3]],
        "boundary": "Qualified adjudication required.",
    }


def _export_document() -> dict[str, object]:
    return {
        "labeling_export_version": "1.0.0",
        "packet_id": PACKET_ID,
        "processing_run_id": PROCESSING_RUN_ID,
        "source_processing_manifest_sha256": MANIFEST_SHA256,
        "reviewer": {"name": "Test reviewer", "role": "SAR domain reviewer"},
        "exported_at": "2026-08-25T04:05:00Z",
        "coverage": {"status": "complete", "reviewed_tiles": 1, "total_tiles": 1},
        "tile_reviews": [
            {
                "tile_id": "T-001",
                "decision": "regions-drawn",
                "note": "Synthetic contract test.",
                "saved_at": "2026-08-25T04:04:00Z",
            }
        ],
        "reference_regions": [_region()],
        "incomplete_drafts": [],
        "boundary": "Provisional labeling export; adjudication required.",
    }


def _write_documents(
    root: Path,
    export_document: dict[str, object],
    packet_document: dict[str, object] | None = None,
) -> tuple[Path, Path]:
    root.mkdir()
    packet_path = root / "labeling-packet.json"
    export_path = root / "labeling-export.json"
    packet_path.write_text(json.dumps(packet_document or _packet_document()))
    export_path.write_text(json.dumps(export_document))
    return packet_path, export_path


def test_complete_export_is_ready_only_for_adjudication(tmp_path: Path) -> None:
    packet_path, export_path = _write_documents(tmp_path / "ready", _export_document())

    report = validate_labeling_export(packet_path, export_path)

    assert report.ready_for_adjudication is True
    assert report.ready_for_evaluation is False
    assert report.reviewed_tile_count == 1
    assert report.provisional_region_count == 1
    assert report.blocking_issues == ()
    assert any("Deduplicate" in action for action in report.required_next_actions)
    assert any("never promotes" in limit for limit in report.limitations)


def test_partial_export_reports_coverage_and_draft_blockers(tmp_path: Path) -> None:
    document = _export_document()
    document["coverage"] = {"status": "partial", "reviewed_tiles": 0, "total_tiles": 1}
    document["tile_reviews"] = [{"tile_id": "T-001", "decision": "", "note": "", "saved_at": None}]
    document["reference_regions"] = []
    document["incomplete_drafts"] = [
        {
            "tile_id": "T-001",
            "points": [[1, 9], [2, 8]],
            "updated_at": "2026-08-25T04:03:00Z",
        }
    ]
    packet_path, export_path = _write_documents(tmp_path / "partial", document)

    report = validate_labeling_export(packet_path, export_path)

    assert report.ready_for_adjudication is False
    assert report.blocking_issues == (
        "tile coverage is incomplete: 0/1 reviewed",
        "1 incomplete labeling drafts remain",
    )


def test_export_must_match_packet_identity(tmp_path: Path) -> None:
    document = _export_document()
    document["packet_id"] = "labeling-" + "f" * 20
    packet_path, export_path = _write_documents(tmp_path / "identity", document)

    with pytest.raises(LabelingValidationError, match="packet ID"):
        validate_labeling_export(packet_path, export_path)


def test_region_pixel_coordinates_must_match_projected_points(tmp_path: Path) -> None:
    document = _export_document()
    regions = document["reference_regions"]
    assert isinstance(regions, list)
    regions[0]["pixel_points"] = [[2, 1], [3, 1], [3, 3]]
    packet_path, export_path = _write_documents(tmp_path / "pixels", document)

    with pytest.raises(LabelingValidationError, match="pixel coordinates are inconsistent"):
        validate_labeling_export(packet_path, export_path)


def test_tile_decision_cannot_contradict_saved_regions(tmp_path: Path) -> None:
    document = _export_document()
    reviews = document["tile_reviews"]
    assert isinstance(reviews, list)
    reviews[0]["decision"] = "reviewed-no-reference-region"
    packet_path, export_path = _write_documents(tmp_path / "contradiction", document)

    with pytest.raises(LabelingValidationError, match="marked no region"):
        validate_labeling_export(packet_path, export_path)


def test_export_cannot_self_promote_region_to_domain_reviewed(tmp_path: Path) -> None:
    document = _export_document()
    regions = document["reference_regions"]
    assert isinstance(regions, list)
    regions[0]["review_status"] = "domain-reviewed"
    packet_path, export_path = _write_documents(tmp_path / "promotion", document)

    with pytest.raises(LabelingValidationError, match="provisional-candidate-hidden"):
        validate_labeling_export(packet_path, export_path)


def test_reviewed_tile_requires_saved_timestamp(tmp_path: Path) -> None:
    document = _export_document()
    reviews = document["tile_reviews"]
    assert isinstance(reviews, list)
    reviews[0]["saved_at"] = None
    packet_path, export_path = _write_documents(tmp_path / "timestamp", document)

    with pytest.raises(LabelingValidationError, match="reviewed tiles require saved_at"):
        validate_labeling_export(packet_path, export_path)


def test_packet_tiles_must_stay_inside_declared_grid(tmp_path: Path) -> None:
    packet_document = _packet_document()
    packet_document["tiles"] = [
        {"tile_id": "T-001", "row": 1, "column": 1, "source_box": [5, 5, 10, 10]}
    ]
    packet_path, export_path = _write_documents(
        tmp_path / "packet-grid",
        _export_document(),
        packet_document,
    )

    with pytest.raises(LabelingValidationError, match="tile T-001 is out of bounds"):
        validate_labeling_export(packet_path, export_path)


def test_packet_requires_exactly_one_artifact_per_role(tmp_path: Path) -> None:
    packet_document = _packet_document()
    artifacts = packet_document["artifacts"]
    assert isinstance(artifacts, list)
    artifacts[1] = dict(artifacts[0])
    packet_path, export_path = _write_documents(
        tmp_path / "packet-artifacts",
        _export_document(),
        packet_document,
    )

    with pytest.raises(LabelingValidationError, match="one before and one after"):
        validate_labeling_export(packet_path, export_path)
