from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from echoatlas.adapters.cli import palantir_package_main, palantir_plan_main
from echoatlas.adapters.palantir import ONTOLOGY_OBJECT_TYPES, plan_palantir_import
from echoatlas.adapters.palantir_package import write_palantir_import_package
from echoatlas.bundle.fixture import FixtureCase, generate_fixture
from echoatlas.bundle.validator import BundleValidator

SCHEMA_ROOT = Path("schemas/analysis-bundle/v1")
COMMIT = "a" * 40


def test_valid_bundle_maps_every_minimal_ontology_type(tmp_path: Path) -> None:
    root = generate_fixture(tmp_path / "bundle", software_commit=COMMIT)
    bundle = BundleValidator(SCHEMA_ROOT).validate(root)

    plan = plan_palantir_import(bundle)

    assert plan.ontology_object_types == ONTOLOGY_OBJECT_TYPES
    assert {item.object_type for item in plan.objects} == {
        "AreaOfInterest",
        "Acquisition",
        "AnalysisRun",
        "EvidenceArtifact",
        "ChangeCandidate",
    }
    assert len([item for item in plan.objects if item.object_type == "Acquisition"]) == 2
    assert len([item for item in plan.objects if item.object_type == "EvidenceArtifact"]) == 4
    assert len(plan.media_uploads) == 4
    assert plan.requires_authenticated_target is True
    assert plan.writes_performed is False
    assert any("system of record" in item for item in plan.policy_boundaries)


def test_projection_is_deterministic_across_equivalent_bundle_roots(tmp_path: Path) -> None:
    first_root = generate_fixture(tmp_path / "first", software_commit=COMMIT)
    second_root = generate_fixture(tmp_path / "second", software_commit=COMMIT)
    validator = BundleValidator(SCHEMA_ROOT)

    first = plan_palantir_import(validator.validate(first_root))
    second = plan_palantir_import(validator.validate(second_root))

    assert first.model_dump_json() == second.model_dump_json()


def test_assessment_maps_to_object_and_evidence_links(tmp_path: Path) -> None:
    root = generate_fixture(tmp_path / "assessed", software_commit=COMMIT)
    assessments = _read_json(root / "assessments.json")
    events = assessments["events"]
    assert isinstance(events, list)
    events.append(
        {
            "assessment_id": "assessment-synthetic-001",
            "candidate_id": "candidate-synthetic-001",
            "decision": "needs_context",
            "recorded_at": "2026-01-15T13:00:00Z",
            "analyst_id": "analyst-synthetic",
            "notes": "Synthetic mapping test only.",
            "evidence_artifact_ids": ["before-preview"],
        }
    )
    events.append(
        {
            "assessment_id": "assessment-synthetic-002",
            "candidate_id": "candidate-synthetic-001",
            "decision": "candidate_rejected",
            "recorded_at": "2026-01-15T14:00:00Z",
            "analyst_id": "analyst-synthetic",
            "notes": "Synthetic superseding event.",
            "evidence_artifact_ids": ["before-preview"],
            "supersedes_assessment_id": "assessment-synthetic-001",
        }
    )
    _write_component_and_refresh_manifest(root, "assessments", assessments)
    bundle = BundleValidator(SCHEMA_ROOT).validate(root)

    plan = plan_palantir_import(bundle)

    assessment = next(
        item
        for item in plan.objects
        if item.object_type == "AnalystAssessment"
        and item.properties["assessment_id"] == "assessment-synthetic-002"
    )
    assert assessment.properties["decision"] == "candidate_rejected"
    assessment_links = [
        link
        for link in plan.links
        if link.source_type == "AnalystAssessment"
        and link.source_primary_key == assessment.primary_key
    ]
    assert {link.link_type for link in assessment_links} == {
        "assessmentAssessesCandidate",
        "assessmentReferencesArtifact",
        "assessmentSupersedesAssessment",
    }


def test_partial_bundle_excludes_missing_artifact_from_media_uploads(tmp_path: Path) -> None:
    root = generate_fixture(
        tmp_path / "partial",
        case=FixtureCase.PARTIAL_SUCCESS,
        software_commit=COMMIT,
    )
    bundle = BundleValidator(SCHEMA_ROOT).validate(root)

    plan = plan_palantir_import(bundle)

    assert len(plan.media_uploads) == 3
    assert all("candidate-overlay" not in item.source_relative_path for item in plan.media_uploads)
    assert any("excluded from media uploads" in item for item in plan.warnings)


def test_cli_writes_plan_without_network_access(tmp_path: Path) -> None:
    root = generate_fixture(tmp_path / "cli-bundle", software_commit=COMMIT)
    output = tmp_path / "projection" / "palantir-import-plan.json"

    palantir_plan_main(
        [
            "--bundle",
            str(root),
            "--schema-root",
            str(SCHEMA_ROOT),
            "--output",
            str(output),
        ]
    )

    document = _read_json(output)
    assert document["source_bundle_id"] == "bundle-bingham-canyon-synthetic-v1"
    assert document["requires_authenticated_target"] is True
    assert document["writes_performed"] is False


def test_package_writes_normalized_tables_with_hashes(tmp_path: Path) -> None:
    root = generate_fixture(tmp_path / "bundle", software_commit=COMMIT)
    bundle = BundleValidator(SCHEMA_ROOT).validate(root)
    output = tmp_path / "package"
    plan = plan_palantir_import(bundle)

    manifest = write_palantir_import_package(plan, output)

    assert manifest.source_bundle_id == "bundle-bingham-canyon-synthetic-v1"
    assert manifest.package_version == "1.3.0"
    assert manifest.timestamp_companion_encoding == "utc_epoch_milliseconds"
    assert len(manifest.tables) == 17
    assert manifest.requires_authenticated_target is True
    assert manifest.writes_performed is False
    for table in manifest.tables:
        if not table.upload_ready:
            continue
        assert table.relative_path is not None
        assert table.sha256 is not None
        content = (output / table.relative_path).read_bytes()
        assert hashlib.sha256(content).hexdigest() == table.sha256

    candidate_table = _read_csv(output / "objects/change_candidate.csv")
    assert len(candidate_table) == 1
    assert candidate_table[0]["status"] == "pending"
    assert isinstance(json.loads(candidate_table[0]["geometry"]), dict)
    assert isinstance(json.loads(candidate_table[0]["evidence_artifact_ids"]), list)

    acquisition_table = _read_csv(output / "objects/acquisition.csv")
    assert {row["acquired_at"]: row["acquired_at_epoch_millis"] for row in acquisition_table} == {
        "2025-01-10T12:00:00Z": "1736510400000",
        "2025-02-10T12:00:00Z": "1739188800000",
    }

    run_table = _read_csv(output / "objects/analysis_run.csv")
    assert run_table[0]["created_at"] == "2026-01-15T12:00:00Z"
    assert run_table[0]["created_at_epoch_millis"] == "1768478400000"

    assessment_record = next(
        table for table in manifest.tables if table.logical_name == "analyst_assessment"
    )
    assert assessment_record.row_count == 0
    assert assessment_record.columns == ("primary_key",)
    assert assessment_record.upload_ready is False
    assert assessment_record.omission_reason == "no_rows"
    assert assessment_record.relative_path is None
    assert assessment_record.sha256 is None
    assert not (output / "objects/analyst_assessment.csv").exists()

    run_candidate_links = _read_csv(output / "links/run_produces_candidate.csv")
    assert run_candidate_links == [
        {
            "source_primary_key": next(
                item.primary_key for item in plan.objects if item.object_type == "AnalysisRun"
            ),
            "target_primary_key": next(
                item.primary_key for item in plan.objects if item.object_type == "ChangeCandidate"
            ),
        }
    ]

    expected_link_counts = {
        "acquisition_covers_aoi": 2,
        "run_uses_acquisition": 2,
        "run_produces_artifact": 4,
        "run_produces_candidate": 1,
        "candidate_affects_aoi": 1,
        "candidate_references_artifact": 3,
    }
    for logical_name, row_count in expected_link_counts.items():
        table = next(item for item in manifest.tables if item.logical_name == logical_name)
        assert table.row_count == row_count
        assert table.upload_ready is True
        assert len(_read_csv(output / f"links/{logical_name}.csv")) == row_count

    assessment_link_names = {
        "assessment_assesses_candidate",
        "assessment_references_artifact",
        "assessment_supersedes_assessment",
    }
    for logical_name in assessment_link_names:
        table = next(item for item in manifest.tables if item.logical_name == logical_name)
        assert table.row_count == 0
        assert table.upload_ready is False
        assert table.omission_reason == "no_rows"
        assert not (output / f"links/{logical_name}.csv").exists()

    assert len(_read_csv(output / "ontology_links.csv")) == len(plan.links)


def test_package_normalizes_timestamp_offsets_without_losing_source_value(
    tmp_path: Path,
) -> None:
    root = generate_fixture(tmp_path / "bundle", software_commit=COMMIT)
    bundle = BundleValidator(SCHEMA_ROOT).validate(root)
    plan = plan_palantir_import(bundle)
    objects = tuple(
        item.model_copy(
            update={
                "properties": {
                    **item.properties,
                    "created_at": "2026-01-15T04:00:00-08:00",
                }
            }
        )
        if item.object_type == "AnalysisRun"
        else item
        for item in plan.objects
    )

    write_palantir_import_package(
        plan.model_copy(update={"objects": objects}),
        tmp_path / "package",
    )

    run = _read_csv(tmp_path / "package/objects/analysis_run.csv")[0]
    assert run["created_at"] == "2026-01-15T04:00:00-08:00"
    assert run["created_at_epoch_millis"] == "1768478400000"


@pytest.mark.parametrize(
    "created_at",
    ["2026-01-15T12:00:00.000001Z", "2026-01-15T12:00:00.0000001Z"],
)
def test_package_rejects_lossy_sub_millisecond_timestamp(
    tmp_path: Path,
    created_at: str,
) -> None:
    root = generate_fixture(tmp_path / "bundle", software_commit=COMMIT)
    bundle = BundleValidator(SCHEMA_ROOT).validate(root)
    plan = plan_palantir_import(bundle)
    objects = tuple(
        item.model_copy(
            update={
                "properties": {
                    **item.properties,
                    "created_at": created_at,
                }
            }
        )
        if item.object_type == "AnalysisRun"
        else item
        for item in plan.objects
    )

    with pytest.raises(ValueError, match="sub-millisecond precision"):
        write_palantir_import_package(
            plan.model_copy(update={"objects": objects}),
            tmp_path / "package",
        )


def test_package_is_byte_deterministic_across_equivalent_roots(tmp_path: Path) -> None:
    validator = BundleValidator(SCHEMA_ROOT)
    first_bundle = validator.validate(
        generate_fixture(tmp_path / "first-bundle", software_commit=COMMIT)
    )
    second_bundle = validator.validate(
        generate_fixture(tmp_path / "second-bundle", software_commit=COMMIT)
    )
    first_output = tmp_path / "first-package"
    second_output = tmp_path / "second-package"

    write_palantir_import_package(plan_palantir_import(first_bundle), first_output)
    write_palantir_import_package(plan_palantir_import(second_bundle), second_output)

    first_files = {
        path.relative_to(first_output): path.read_bytes()
        for path in sorted(first_output.rglob("*"))
        if path.is_file()
    }
    second_files = {
        path.relative_to(second_output): path.read_bytes()
        for path in sorted(second_output.rglob("*"))
        if path.is_file()
    }
    assert first_files == second_files


def test_package_refuses_to_merge_with_existing_output(tmp_path: Path) -> None:
    root = generate_fixture(tmp_path / "bundle", software_commit=COMMIT)
    bundle = BundleValidator(SCHEMA_ROOT).validate(root)
    output = tmp_path / "package"
    output.mkdir()
    marker = output / "stale-record.csv"
    marker.write_text("must remain untouched\n", encoding="utf-8")

    with pytest.raises(FileExistsError, match="output directory already exists"):
        write_palantir_import_package(plan_palantir_import(bundle), output)

    assert marker.read_text(encoding="utf-8") == "must remain untouched\n"


def test_package_cli_preserves_partial_media_boundary(tmp_path: Path) -> None:
    root = generate_fixture(
        tmp_path / "partial",
        case=FixtureCase.PARTIAL_SUCCESS,
        software_commit=COMMIT,
    )
    output = tmp_path / "package"

    palantir_package_main(
        [
            "--bundle",
            str(root),
            "--schema-root",
            str(SCHEMA_ROOT),
            "--output",
            str(output),
        ]
    )

    manifest = _read_json(output / "package-manifest.json")
    media_record = next(
        table for table in manifest["tables"] if table["logical_name"] == "media_uploads"
    )
    assert media_record["row_count"] == 3
    media_rows = _read_csv(output / "media_uploads.csv")
    assert len(media_rows) == 3
    assert all("candidate-overlay" not in row["source_relative_path"] for row in media_rows)


def _write_component_and_refresh_manifest(
    root: Path, component_name: str, document: dict[str, Any]
) -> None:
    manifest = _read_json(root / "manifest.json")
    components = manifest["components"]
    assert isinstance(components, dict)
    record = components[component_name]
    assert isinstance(record, dict)
    path = root / str(record["path"])
    _write_json(path, document)
    record["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    record["size_bytes"] = path.stat().st_size
    _write_json(root / "manifest.json", manifest)


def _read_json(path: Path) -> dict[str, Any]:
    document = json.loads(path.read_bytes())
    assert isinstance(document, dict)
    return document


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def _write_json(path: Path, document: object) -> None:
    path.write_bytes(json.dumps(document, indent=2, sort_keys=True).encode() + b"\n")
