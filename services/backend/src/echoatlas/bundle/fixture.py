"""Deterministic, bounded synthetic fixtures for the analysis-bundle contract."""

from __future__ import annotations

import hashlib
import json
import shutil
from enum import StrEnum
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw

from echoatlas.bundle.validator import SUPPORTED_BUNDLE_VERSION

FIXTURE_TIMESTAMP = "2026-01-15T12:00:00Z"
FIXTURE_BUNDLE_ID = "bundle-bingham-canyon-synthetic-v1"
FIXTURE_PROCESSING_RUN_ID = "processing-synthetic-v1"
FIXTURE_CHANGE_RUN_ID = "change-synthetic-v1"
FIXTURE_CANDIDATE_ID = "candidate-synthetic-001"


class FixtureCase(StrEnum):
    VALID = "valid"
    STALE_VERSION = "stale-version"
    MISSING_ARTIFACT = "missing-artifact"
    PARTIAL_SUCCESS = "partial-success"
    MALICIOUS_PATH = "malicious-path"


def generate_fixture(
    output_root: Path,
    *,
    case: FixtureCase = FixtureCase.VALID,
    software_commit: str = "0000000",
) -> Path:
    """Create one self-contained fixture without overwriting an existing path."""
    if output_root.exists():
        raise FileExistsError(f"fixture output already exists: {output_root}")
    output_root.mkdir(parents=True)
    try:
        artifacts = _write_artifacts(output_root)
        components = _write_components(output_root)
        manifest = _manifest(components, artifacts, software_commit)
        _apply_case(output_root, manifest, case)
        _write_json(output_root / "manifest.json", manifest)
    except Exception:
        shutil.rmtree(output_root)
        raise
    return output_root


def _write_artifacts(root: Path) -> list[dict[str, object]]:
    artifact_root = root / "artifacts"
    artifact_root.mkdir()
    paths = {
        "before-preview": artifact_root / "before.png",
        "after-preview": artifact_root / "after.png",
        "change-score-preview": artifact_root / "change-score.png",
        "candidate-overlay": artifact_root / "candidate-overlay.png",
    }
    before = Image.new("RGB", (32, 32), "#16202a")
    after = before.copy()
    before_draw = ImageDraw.Draw(before)
    after_draw = ImageDraw.Draw(after)
    before_draw.rectangle((8, 8, 23, 23), fill="#55697c")
    after_draw.rectangle((8, 8, 23, 23), fill="#8198aa")
    after_draw.rectangle((16, 12, 25, 21), fill="#b8c6cf")
    score = Image.new("RGB", (32, 32), "#080b10")
    score_draw = ImageDraw.Draw(score)
    score_draw.rectangle((14, 10, 26, 23), fill="#e2a63b")
    overlay = after.copy()
    overlay_draw = ImageDraw.Draw(overlay)
    overlay_draw.rectangle((13, 9, 27, 24), outline="#ffcc66", width=2)
    for image, path in (
        (before, paths["before-preview"]),
        (after, paths["after-preview"]),
        (score, paths["change-score-preview"]),
        (overlay, paths["candidate-overlay"]),
    ):
        image.save(path, format="PNG", optimize=False, compress_level=9)

    records: list[dict[str, object]] = []
    for artifact_id, path in paths.items():
        records.append(
            {
                "artifact_id": artifact_id,
                "kind": artifact_id,
                "path": path.relative_to(root).as_posix(),
                "media_type": "image/png",
                "sha256": _sha256(path),
                "size_bytes": path.stat().st_size,
                "required": artifact_id != "candidate-overlay",
                "status": "available",
            }
        )
    return records


def _write_components(root: Path) -> dict[str, dict[str, object]]:
    geometry: dict[str, object] = {
        "type": "Polygon",
        "coordinates": [
            [
                [-112.18, 40.50],
                [-112.12, 40.50],
                [-112.12, 40.55],
                [-112.18, 40.55],
                [-112.18, 40.50],
            ]
        ],
    }
    geometry_hash = hashlib.sha256(_canonical_json(geometry)).hexdigest()
    documents: dict[str, dict[str, Any]] = {
        "aoi": {
            "type": "Feature",
            "contract_version": SUPPORTED_BUNDLE_VERSION,
            "bundle_id": FIXTURE_BUNDLE_ID,
            "geometry": geometry,
            "properties": {
                "aoi_id": "aoi-bingham-canyon-approved-boundary",
                "label": "Bingham Canyon synthetic demonstration boundary",
                "boundary": (
                    "Approved demonstration boundary; coordinates are illustrative and must not "
                    "be used for navigation, safety, or operational decisions."
                ),
                "geometry_sha256": geometry_hash,
            },
        },
        "acquisitions": {
            "contract_version": SUPPORTED_BUNDLE_VERSION,
            "bundle_id": FIXTURE_BUNDLE_ID,
            "acquisitions": [
                _acquisition("before", "2025-01-10T12:00:00Z", "before-source"),
                _acquisition("after", "2025-02-10T12:00:00Z", "after-source"),
            ],
        },
        "candidates": {
            "type": "FeatureCollection",
            "contract_version": SUPPORTED_BUNDLE_VERSION,
            "bundle_id": FIXTURE_BUNDLE_ID,
            "change_run_id": FIXTURE_CHANGE_RUN_ID,
            "source_processing_run_id": FIXTURE_PROCESSING_RUN_ID,
            "display_label": "Change candidates",
            "warnings": [
                "Synthetic demonstration only; candidate output is not an assessment or alert."
            ],
            "features": [
                {
                    "type": "Feature",
                    "id": FIXTURE_CANDIDATE_ID,
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [
                            [
                                [-112.16, 40.515],
                                [-112.14, 40.515],
                                [-112.14, 40.535],
                                [-112.16, 40.535],
                                [-112.16, 40.515],
                            ]
                        ],
                    },
                    "properties": {
                        "candidate_id": FIXTURE_CANDIDATE_ID,
                        "display_label": "Change candidate",
                        "status": "pending",
                        "change_run_id": FIXTURE_CHANGE_RUN_ID,
                        "source_processing_run_id": FIXTURE_PROCESSING_RUN_ID,
                        "measurements": {
                            "pixel_count": 130,
                            "area_square_meters": 13000.0,
                            "projected_bbox": [0.0, 0.0, 100.0, 130.0],
                            "wgs84_bbox": [-112.16, 40.515, -112.14, 40.535],
                        },
                        "score_components": {
                            "mean_change_score": 0.61,
                            "p95_change_score": 0.83,
                            "max_change_score": 0.92,
                            "mean_signed_normalized_delta": 0.36,
                            "brightening_pixel_fraction": 0.72,
                            "darkening_pixel_fraction": 0.08,
                        },
                        "evidence_artifact_ids": [
                            "before-preview",
                            "after-preview",
                            "change-score-preview",
                        ],
                        "warnings": [
                            "Machine-generated candidate requiring analyst review and context."
                        ],
                    },
                }
            ],
        },
        "assessments": {
            "contract_version": SUPPORTED_BUNDLE_VERSION,
            "bundle_id": FIXTURE_BUNDLE_ID,
            "append_only": True,
            "events": [],
        },
        "summary": {
            "contract_version": SUPPORTED_BUNDLE_VERSION,
            "bundle_id": FIXTURE_BUNDLE_ID,
            "summary_id": "summary-synthetic-001",
            "status": "draft",
            "authoritative": False,
            "generator": {
                "kind": "fixture",
                "provider": "EchoAtlas",
                "model": "deterministic-synthetic-fixture",
                "version": "1",
                "generated_at": FIXTURE_TIMESTAMP,
            },
            "text": (
                "One synthetic change candidate is present. Analyst review and external context "
                "are required before drawing conclusions."
            ),
            "candidate_ids": [FIXTURE_CANDIDATE_ID],
            "evidence_artifact_ids": ["change-score-preview"],
            "warnings": ["Fixture text is non-authoritative and is not an analyst finding."],
        },
    }
    records: dict[str, dict[str, object]] = {}
    file_names = {
        "aoi": "aoi.geojson",
        "acquisitions": "acquisitions.json",
        "candidates": "candidates.geojson",
        "assessments": "assessments.json",
        "summary": "summary.json",
    }
    for name, document in documents.items():
        path = root / file_names[name]
        _write_json(path, document)
        records[name] = {
            "path": path.relative_to(root).as_posix(),
            "sha256": _sha256(path),
            "size_bytes": path.stat().st_size,
        }
    return records


def _acquisition(role: str, acquired_at: str, source_item_id: str) -> dict[str, object]:
    return {
        "acquisition_id": f"acquisition-{role}-synthetic",
        "role": role,
        "acquired_at": acquired_at,
        "provider": "EchoAtlas synthetic fixture",
        "source_item_id": source_item_id,
        "platform": "synthetic-sar",
        "product_type": "synthetic-amplitude-preview",
        "polarizations": ["VV"],
        "source": {
            "uri": f"https://example.invalid/echoatlas/{source_item_id}",
            "size_bytes": 1024,
            "checksum": {"algorithm": "sha256", "value": "0" * 64},
            "license_spdx": "CC0-1.0",
        },
        "quality": {
            "resolution_meters": 10.0,
            "incidence_angle_degrees": 35.0,
            "valid_aoi_fraction": 1.0,
        },
        "quality_warnings": ["Synthetic acquisition; no satellite measurement is represented."],
    }


def _manifest(
    components: dict[str, dict[str, object]],
    artifacts: list[dict[str, object]],
    software_commit: str,
) -> dict[str, object]:
    return {
        "bundle_version": SUPPORTED_BUNDLE_VERSION,
        "bundle_id": FIXTURE_BUNDLE_ID,
        "status": "succeeded",
        "created_at": FIXTURE_TIMESTAMP,
        "source_processing_run_id": FIXTURE_PROCESSING_RUN_ID,
        "change_run_id": FIXTURE_CHANGE_RUN_ID,
        "software": {"commit": software_commit, "echoatlas": "0.1.0"},
        "license": {
            "source_data_spdx": "CC0-1.0",
            "source_provider": "EchoAtlas synthetic fixture",
            "bundle_content_spdx": "CC0-1.0",
            "synthetic_fixture": True,
        },
        "parameters": {
            "processing": {"mode": "deterministic-synthetic"},
            "change": {"threshold": 0.5, "minimum_pixels": 8},
        },
        "components": components,
        "artifacts": artifacts,
        "warnings": [
            "Synthetic demonstration only; not suitable for safety or operational decisions."
        ],
    }


def _apply_case(root: Path, manifest: dict[str, object], case: FixtureCase) -> None:
    artifacts = manifest["artifacts"]
    if not isinstance(artifacts, list):
        raise TypeError("fixture manifest artifacts must be a list")
    records = {str(record["artifact_id"]): record for record in artifacts}
    if case is FixtureCase.VALID:
        return
    if case is FixtureCase.STALE_VERSION:
        manifest["bundle_version"] = "0.9.0"
        return
    if case is FixtureCase.MISSING_ARTIFACT:
        (root / str(records["before-preview"]["path"])).unlink()
        return
    if case is FixtureCase.PARTIAL_SUCCESS:
        overlay = records["candidate-overlay"]
        (root / str(overlay["path"])).unlink()
        overlay["status"] = "missing"
        manifest["status"] = "partial"
        manifest["warnings"] = [
            "Synthetic optional overlay was intentionally omitted; core evidence remains available."
        ]
        return
    if case is FixtureCase.MALICIOUS_PATH:
        records["change-score-preview"]["path"] = "../../outside.png"
        return
    raise ValueError(f"unsupported fixture case: {case}")


def _write_json(path: Path, document: object) -> None:
    path.write_bytes(json.dumps(document, indent=2, sort_keys=True).encode() + b"\n")


def _canonical_json(document: object) -> bytes:
    return json.dumps(document, separators=(",", ":"), sort_keys=True).encode()


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()
