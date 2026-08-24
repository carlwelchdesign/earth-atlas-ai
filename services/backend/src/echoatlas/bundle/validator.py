"""Fail-closed schema, integrity, path, and reference validation for bundle v1."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import cast

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource

SUPPORTED_BUNDLE_VERSION = "1.0.0"
SCHEMA_FILES = {
    "manifest": "manifest.schema.json",
    "aoi": "aoi.schema.json",
    "acquisitions": "acquisitions.schema.json",
    "candidates": "candidates.schema.json",
    "assessments": "assessments.schema.json",
    "summary": "summary.schema.json",
}


class BundleValidationError(ValueError):
    """Base class for invalid or unsafe bundles."""


class UnsupportedBundleVersionError(BundleValidationError):
    """The bundle major/minor version is not supported by this validator."""


class BundleSchemaError(BundleValidationError):
    """A bundle document does not satisfy its JSON Schema."""


class UnsafeBundlePathError(BundleValidationError):
    """A bundle path is non-canonical or escapes the bundle root."""


class MissingBundleFileError(BundleValidationError):
    """A required component or available artifact is absent."""


class BundleIntegrityError(BundleValidationError):
    """A component or artifact differs from its manifest record."""


class BundleReferenceError(BundleValidationError):
    """Cross-document identifiers do not resolve consistently."""


@dataclass(frozen=True)
class ValidatedBundle:
    root: Path
    manifest: dict[str, object]
    components: dict[str, dict[str, object]]
    available_artifacts: tuple[Path, ...]
    missing_artifact_ids: tuple[str, ...]


class BundleValidator:
    def __init__(
        self,
        schema_root: Path,
        *,
        max_json_bytes: int = 5 * 1024 * 1024,
        max_artifact_bytes: int = 256 * 1024 * 1024,
    ) -> None:
        if max_json_bytes <= 0 or max_artifact_bytes <= 0:
            raise ValueError("bundle size limits must be positive")
        self._schema_root = schema_root
        self._max_json_bytes = max_json_bytes
        self._max_artifact_bytes = max_artifact_bytes
        self._validators = self._load_validators()

    def validate(self, bundle_root: Path) -> ValidatedBundle:
        try:
            resolved_root = bundle_root.resolve(strict=True)
        except OSError as error:
            raise MissingBundleFileError(f"bundle root could not be opened: {error}") from error
        if not resolved_root.is_dir():
            raise MissingBundleFileError("bundle root must be a directory")

        manifest_path = self._resolve_path(resolved_root, "manifest.json")
        manifest = self._read_json(manifest_path)
        version = manifest.get("bundle_version")
        if version != SUPPORTED_BUNDLE_VERSION:
            raise UnsupportedBundleVersionError(
                f"unsupported bundle version {version!r}; expected {SUPPORTED_BUNDLE_VERSION}"
            )
        self._validate_schema("manifest", manifest)

        bundle_id = cast(str, manifest["bundle_id"])
        components = self._validate_components(resolved_root, manifest, bundle_id)
        available, missing = self._validate_artifacts(resolved_root, manifest)
        self._validate_bundle_state(manifest, missing)
        self._validate_references(manifest, components, available)
        return ValidatedBundle(
            root=resolved_root,
            manifest=manifest,
            components=components,
            available_artifacts=tuple(path for _, path in available.values()),
            missing_artifact_ids=tuple(missing),
        )

    def _load_validators(self) -> dict[str, Draft202012Validator]:
        schemas: dict[str, dict[str, object]] = {}
        for path in sorted(self._schema_root.glob("*.schema.json")):
            try:
                document = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as error:
                raise BundleSchemaError(f"schema could not be loaded: {path}: {error}") from error
            if not isinstance(document, dict) or not isinstance(document.get("$id"), str):
                raise BundleSchemaError(f"schema requires an object root and $id: {path}")
            schemas[path.name] = document
        required = {"common.schema.json", *SCHEMA_FILES.values()}
        if set(schemas) != required:
            missing = sorted(required - set(schemas))
            unexpected = sorted(set(schemas) - required)
            raise BundleSchemaError(
                f"schema set mismatch; missing={missing}, unexpected={unexpected}"
            )
        try:
            resources = [
                (cast(str, schema["$id"]), Resource.from_contents(schema))
                for schema in schemas.values()
            ]
            registry = Registry().with_resources(resources)
            validators: dict[str, Draft202012Validator] = {}
            for name, file_name in SCHEMA_FILES.items():
                schema = schemas[file_name]
                Draft202012Validator.check_schema(schema)
                validators[name] = Draft202012Validator(
                    schema,
                    registry=registry,
                    format_checker=FormatChecker(),
                )
        except Exception as error:
            raise BundleSchemaError(f"schema set is invalid: {error}") from error
        return validators

    def _validate_components(
        self, root: Path, manifest: dict[str, object], bundle_id: str
    ) -> dict[str, dict[str, object]]:
        records = cast(dict[str, dict[str, object]], manifest["components"])
        components: dict[str, dict[str, object]] = {}
        seen_paths: set[Path] = set()
        for name, record in records.items():
            path = self._resolve_path(root, cast(str, record["path"]))
            if path in seen_paths:
                raise BundleReferenceError(f"component path is reused: {path.name}")
            seen_paths.add(path)
            self._verify_file_record(path, record, self._max_json_bytes)
            document = self._read_json(path)
            self._validate_schema(name, document)
            if document.get("bundle_id") != bundle_id:
                raise BundleReferenceError(f"{name} component has a different bundle ID")
            if document.get("contract_version") != SUPPORTED_BUNDLE_VERSION:
                raise BundleReferenceError(f"{name} component has a different contract version")
            components[name] = document
        return components

    def _validate_artifacts(
        self, root: Path, manifest: dict[str, object]
    ) -> tuple[dict[str, tuple[dict[str, object], Path]], list[str]]:
        records = cast(list[dict[str, object]], manifest["artifacts"])
        available: dict[str, tuple[dict[str, object], Path]] = {}
        missing: list[str] = []
        seen_paths: set[Path] = set()
        seen_ids: set[str] = set()
        for record in records:
            artifact_id = cast(str, record["artifact_id"])
            if artifact_id in seen_ids:
                raise BundleReferenceError(f"artifact ID is duplicated: {artifact_id}")
            seen_ids.add(artifact_id)
            path = self._resolve_path(root, cast(str, record["path"]))
            if path in seen_paths:
                raise BundleReferenceError(f"artifact path is reused: {record['path']}")
            seen_paths.add(path)
            if record["status"] == "missing":
                if path.exists():
                    raise BundleIntegrityError(f"artifact marked missing is present: {artifact_id}")
                missing.append(artifact_id)
                continue
            self._verify_file_record(path, record, self._max_artifact_bytes)
            self._verify_media_signature(path, cast(str, record["media_type"]))
            available[artifact_id] = (record, path)
        return available, missing

    def _validate_bundle_state(
        self, manifest: dict[str, object], missing_artifact_ids: list[str]
    ) -> None:
        status = manifest["status"]
        if status == "succeeded" and missing_artifact_ids:
            raise BundleReferenceError("a succeeded bundle cannot contain missing artifacts")
        if status == "partial" and not missing_artifact_ids:
            raise BundleReferenceError(
                "a partial bundle must declare at least one missing artifact"
            )
        warnings = cast(list[object], manifest["warnings"])
        if status == "partial" and not warnings:
            raise BundleReferenceError("a partial bundle must explain its degraded state")

    def _validate_references(
        self,
        manifest: dict[str, object],
        components: dict[str, dict[str, object]],
        available: dict[str, tuple[dict[str, object], Path]],
    ) -> None:
        artifact_ids = set(available)
        acquisitions = cast(list[dict[str, object]], components["acquisitions"]["acquisitions"])
        roles = [cast(str, record["role"]) for record in acquisitions]
        if sorted(roles) != ["after", "before"]:
            raise BundleReferenceError("acquisitions must contain exactly before and after roles")
        acquisition_ids = [record["acquisition_id"] for record in acquisitions]
        if len(set(acquisition_ids)) != len(acquisition_ids):
            raise BundleReferenceError("acquisition IDs must be unique")

        candidates_document = components["candidates"]
        if candidates_document["change_run_id"] != manifest["change_run_id"]:
            raise BundleReferenceError("candidate and manifest change-run IDs differ")
        if candidates_document["source_processing_run_id"] != manifest["source_processing_run_id"]:
            raise BundleReferenceError("candidate and manifest processing-run IDs differ")
        features = cast(list[dict[str, object]], candidates_document["features"])
        candidate_ids: set[str] = set()
        for feature in features:
            properties = cast(dict[str, object], feature["properties"])
            candidate_id = cast(str, properties["candidate_id"])
            if feature["id"] != candidate_id:
                raise BundleReferenceError("candidate feature ID and property ID differ")
            if candidate_id in candidate_ids:
                raise BundleReferenceError(f"candidate ID is duplicated: {candidate_id}")
            candidate_ids.add(candidate_id)
            self._require_available_artifacts(
                cast(list[str], properties["evidence_artifact_ids"]), artifact_ids
            )

        assessments = cast(list[dict[str, object]], components["assessments"]["events"])
        prior_assessments: set[str] = set()
        for event in assessments:
            assessment_id = cast(str, event["assessment_id"])
            if assessment_id in prior_assessments:
                raise BundleReferenceError(f"assessment ID is duplicated: {assessment_id}")
            if event["candidate_id"] not in candidate_ids:
                raise BundleReferenceError(
                    f"assessment references an unknown candidate: {event['candidate_id']}"
                )
            self._require_available_artifacts(
                cast(list[str], event["evidence_artifact_ids"]), artifact_ids
            )
            supersedes = event.get("supersedes_assessment_id")
            if supersedes is not None and supersedes not in prior_assessments:
                raise BundleReferenceError(
                    f"assessment supersedes an unknown or later event: {supersedes}"
                )
            prior_assessments.add(assessment_id)

        summary = components.get("summary")
        if summary is not None:
            unknown_candidates = set(cast(list[str], summary["candidate_ids"])) - candidate_ids
            if unknown_candidates:
                raise BundleReferenceError(
                    f"summary references unknown candidates: {sorted(unknown_candidates)}"
                )
            self._require_available_artifacts(
                cast(list[str], summary["evidence_artifact_ids"]), artifact_ids
            )

        aoi = components["aoi"]
        geometry = cast(dict[str, object], aoi["geometry"])
        properties = cast(dict[str, object], aoi["properties"])
        canonical = json.dumps(geometry, separators=(",", ":"), sort_keys=True).encode()
        if hashlib.sha256(canonical).hexdigest() != properties["geometry_sha256"]:
            raise BundleIntegrityError("AOI geometry checksum does not match")
        coordinates = cast(list[list[list[float]]], geometry["coordinates"])
        if any(ring[0] != ring[-1] for ring in coordinates):
            raise BundleSchemaError("AOI polygon rings must be closed")

    def _require_available_artifacts(
        self, references: list[str], available_artifact_ids: set[str]
    ) -> None:
        unknown = set(references) - available_artifact_ids
        if unknown:
            raise BundleReferenceError(
                f"document references unavailable artifacts: {sorted(unknown)}"
            )

    def _validate_schema(self, name: str, document: dict[str, object]) -> None:
        validator = self._validators.get(name)
        if validator is None:
            raise BundleSchemaError(f"no validator exists for component: {name}")
        errors = sorted(
            validator.iter_errors(document),
            key=lambda error: tuple(str(part) for part in error.path),
        )
        if not errors:
            return
        error = errors[0]
        location = "/".join(str(part) for part in error.absolute_path) or "<root>"
        raise BundleSchemaError(f"{name} schema failed at {location}: {error.message}")

    def _read_json(self, path: Path) -> dict[str, object]:
        if not path.is_file():
            raise MissingBundleFileError(f"bundle JSON file is missing: {path.name}")
        size = path.stat().st_size
        if size <= 0 or size > self._max_json_bytes:
            raise BundleIntegrityError(f"bundle JSON size is outside its limit: {path.name}")
        try:
            document = json.loads(path.read_bytes())
        except (OSError, json.JSONDecodeError) as error:
            raise BundleSchemaError(
                f"bundle JSON could not be parsed: {path.name}: {error}"
            ) from error
        if not isinstance(document, dict):
            raise BundleSchemaError(f"bundle JSON root must be an object: {path.name}")
        return document

    def _resolve_path(self, root: Path, value: str) -> Path:
        if "\\" in value or "://" in value or "\x00" in value:
            raise UnsafeBundlePathError(f"bundle path is unsafe: {value!r}")
        pure_path = PurePosixPath(value)
        if pure_path.is_absolute() or any(part in {"", ".", ".."} for part in pure_path.parts):
            raise UnsafeBundlePathError(f"bundle path is unsafe: {value!r}")
        if pure_path.as_posix() != value:
            raise UnsafeBundlePathError(f"bundle path is not canonical: {value!r}")
        candidate = (root / Path(*pure_path.parts)).resolve(strict=False)
        if not candidate.is_relative_to(root):
            raise UnsafeBundlePathError(f"bundle path escapes its root: {value!r}")
        return candidate

    def _verify_file_record(self, path: Path, record: dict[str, object], size_limit: int) -> None:
        if not path.is_file():
            raise MissingBundleFileError(f"bundle file is missing: {record['path']}")
        actual_size = path.stat().st_size
        expected_size = cast(int, record["size_bytes"])
        if actual_size <= 0 or actual_size > size_limit:
            raise BundleIntegrityError(f"bundle file exceeds its size limit: {record['path']}")
        if actual_size != expected_size:
            raise BundleIntegrityError(f"bundle file size changed: {record['path']}")
        if self._sha256_file(path) != record["sha256"]:
            raise BundleIntegrityError(f"bundle file checksum changed: {record['path']}")

    def _verify_media_signature(self, path: Path, media_type: str) -> None:
        signatures = {
            "image/png": b"\x89PNG\r\n\x1a\n",
            "application/pdf": b"%PDF-",
        }
        expected = signatures.get(media_type)
        if expected is None:
            return
        try:
            with path.open("rb") as handle:
                actual = handle.read(len(expected))
        except OSError as error:
            raise BundleIntegrityError(f"artifact could not be inspected: {path.name}") from error
        if actual != expected:
            raise BundleIntegrityError(
                f"artifact signature does not match {media_type}: {path.name}"
            )

    @staticmethod
    def _sha256_file(path: Path) -> str:
        checksum = hashlib.sha256()
        try:
            with path.open("rb") as handle:
                while payload := handle.read(1024 * 1024):
                    checksum.update(payload)
        except OSError as error:
            raise BundleIntegrityError(f"bundle file could not be read: {path.name}") from error
        return checksum.hexdigest()
