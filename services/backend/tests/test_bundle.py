from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from echoatlas.bundle.fixture import FixtureCase, generate_fixture
from echoatlas.bundle.validator import (
    BundleIntegrityError,
    BundleReferenceError,
    BundleSchemaError,
    BundleValidator,
    MissingBundleFileError,
    UnsafeBundlePathError,
    UnsupportedBundleVersionError,
)

SCHEMA_ROOT = Path("schemas/analysis-bundle/v1")
COMMIT = "a" * 40


def test_valid_fixture_passes_contract_and_integrity_checks(tmp_path: Path) -> None:
    root = generate_fixture(tmp_path / "valid", software_commit=COMMIT)

    result = BundleValidator(SCHEMA_ROOT).validate(root)

    assert result.manifest["bundle_id"] == "bundle-bingham-canyon-synthetic-v1"
    assert result.manifest["status"] == "succeeded"
    assert result.missing_artifact_ids == ()
    assert len(result.available_artifacts) == 4
    assert result.components["summary"]["authoritative"] is False


def test_fixture_generation_is_byte_for_byte_deterministic(tmp_path: Path) -> None:
    first = generate_fixture(tmp_path / "first", software_commit=COMMIT)
    second = generate_fixture(tmp_path / "second", software_commit=COMMIT)

    first_files = {
        path.relative_to(first): path.read_bytes() for path in first.rglob("*") if path.is_file()
    }
    second_files = {
        path.relative_to(second): path.read_bytes() for path in second.rglob("*") if path.is_file()
    }

    assert first_files == second_files


def test_stale_version_is_rejected_before_schema_dispatch(tmp_path: Path) -> None:
    root = generate_fixture(
        tmp_path / "stale",
        case=FixtureCase.STALE_VERSION,
        software_commit=COMMIT,
    )

    with pytest.raises(UnsupportedBundleVersionError, match="0.9.0"):
        BundleValidator(SCHEMA_ROOT).validate(root)


def test_missing_required_artifact_is_rejected(tmp_path: Path) -> None:
    root = generate_fixture(
        tmp_path / "missing",
        case=FixtureCase.MISSING_ARTIFACT,
        software_commit=COMMIT,
    )

    with pytest.raises(MissingBundleFileError, match="before.png"):
        BundleValidator(SCHEMA_ROOT).validate(root)


def test_partial_bundle_accepts_declared_missing_optional_artifact(tmp_path: Path) -> None:
    root = generate_fixture(
        tmp_path / "partial",
        case=FixtureCase.PARTIAL_SUCCESS,
        software_commit=COMMIT,
    )

    result = BundleValidator(SCHEMA_ROOT).validate(root)

    assert result.manifest["status"] == "partial"
    assert result.missing_artifact_ids == ("candidate-overlay",)


def test_malicious_relative_path_is_rejected(tmp_path: Path) -> None:
    root = generate_fixture(
        tmp_path / "malicious",
        case=FixtureCase.MALICIOUS_PATH,
        software_commit=COMMIT,
    )

    with pytest.raises(BundleSchemaError, match="schema failed"):
        BundleValidator(SCHEMA_ROOT).validate(root)


def test_symlink_escape_is_rejected(tmp_path: Path) -> None:
    root = generate_fixture(tmp_path / "symlink", software_commit=COMMIT)
    outside = tmp_path / "outside.png"
    outside.write_bytes((root / "artifacts/before.png").read_bytes())
    inside = root / "artifacts/before.png"
    inside.unlink()
    inside.symlink_to(outside)

    with pytest.raises(UnsafeBundlePathError, match="escapes its root"):
        BundleValidator(SCHEMA_ROOT).validate(root)


def test_artifact_checksum_tampering_is_rejected(tmp_path: Path) -> None:
    root = generate_fixture(tmp_path / "tampered", software_commit=COMMIT)
    path = root / "artifacts/after.png"
    payload = bytearray(path.read_bytes())
    payload[-1] ^= 1
    path.write_bytes(payload)

    with pytest.raises(BundleIntegrityError, match="checksum changed"):
        BundleValidator(SCHEMA_ROOT).validate(root)


def test_unknown_candidate_evidence_reference_is_rejected(tmp_path: Path) -> None:
    root = generate_fixture(tmp_path / "bad-reference", software_commit=COMMIT)
    candidates = _read_json(root / "candidates.geojson")
    features = candidates["features"]
    assert isinstance(features, list)
    properties = features[0]["properties"]
    properties["evidence_artifact_ids"] = ["unknown-artifact"]
    _write_component_and_refresh_manifest(root, "candidates", candidates)

    with pytest.raises(BundleReferenceError, match="unavailable artifacts"):
        BundleValidator(SCHEMA_ROOT).validate(root)


def test_unexpected_manifest_field_is_rejected(tmp_path: Path) -> None:
    root = generate_fixture(tmp_path / "unexpected", software_commit=COMMIT)
    manifest = _read_json(root / "manifest.json")
    manifest["trusted"] = True
    _write_json(root / "manifest.json", manifest)

    with pytest.raises(BundleSchemaError, match="schema failed"):
        BundleValidator(SCHEMA_ROOT).validate(root)


def test_json_size_limit_is_enforced(tmp_path: Path) -> None:
    root = generate_fixture(tmp_path / "bounded", software_commit=COMMIT)

    with pytest.raises(BundleIntegrityError, match="size is outside"):
        BundleValidator(SCHEMA_ROOT, max_json_bytes=128).validate(root)


def _write_component_and_refresh_manifest(
    root: Path, component_name: str, document: dict[str, Any]
) -> None:
    manifest = _read_json(root / "manifest.json")
    components = manifest["components"]
    record = components[component_name]
    path = root / record["path"]
    _write_json(path, document)
    record["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    record["size_bytes"] = path.stat().st_size
    _write_json(root / "manifest.json", manifest)


def _read_json(path: Path) -> dict[str, Any]:
    document = json.loads(path.read_bytes())
    assert isinstance(document, dict)
    return document


def _write_json(path: Path, document: object) -> None:
    path.write_bytes(json.dumps(document, indent=2, sort_keys=True).encode() + b"\n")
