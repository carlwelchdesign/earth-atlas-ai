"""Render a Palantir import plan as deterministic, schema-inferable CSV tables."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import shutil
import tempfile
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from echoatlas.adapters.palantir import (
    ONTOLOGY_LINK_TYPES,
    ONTOLOGY_OBJECT_TYPES,
    OntologyLinkType,
    OntologyObjectType,
    PalantirImportPlan,
    PalantirOntologyObject,
)

TableKind = Literal["ontology_objects", "ontology_links", "media_uploads"]
OmissionReason = Literal["no_rows"]

_OBJECT_TABLE_NAMES: dict[OntologyObjectType, str] = {
    "AreaOfInterest": "area_of_interest",
    "Acquisition": "acquisition",
    "AnalysisRun": "analysis_run",
    "EvidenceArtifact": "evidence_artifact",
    "ChangeCandidate": "change_candidate",
    "AnalystAssessment": "analyst_assessment",
}

_LINK_TABLE_NAMES: dict[OntologyLinkType, str] = {
    "acquisitionCoversAoi": "acquisition_covers_aoi",
    "runUsesAcquisition": "run_uses_acquisition",
    "runProducesArtifact": "run_produces_artifact",
    "runProducesCandidate": "run_produces_candidate",
    "candidateAffectsAoi": "candidate_affects_aoi",
    "candidateReferencesArtifact": "candidate_references_artifact",
    "assessmentAssessesCandidate": "assessment_assesses_candidate",
    "assessmentReferencesArtifact": "assessment_references_artifact",
    "assessmentSupersedesAssessment": "assessment_supersedes_assessment",
}

_TIMESTAMP_PROPERTIES: dict[OntologyObjectType, tuple[str, ...]] = {
    "AreaOfInterest": (),
    "Acquisition": ("acquired_at",),
    "AnalysisRun": ("created_at",),
    "EvidenceArtifact": (),
    "ChangeCandidate": (),
    "AnalystAssessment": ("recorded_at",),
}


class PalantirTableEntry(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    kind: TableKind
    logical_name: str = Field(min_length=1, max_length=200)
    relative_path: str | None = Field(default=None, min_length=1, max_length=1000)
    row_count: int = Field(ge=0)
    columns: tuple[str, ...]
    sha256: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    upload_ready: bool
    omission_reason: OmissionReason | None = None

    @model_validator(mode="after")
    def validate_upload_state(self) -> PalantirTableEntry:
        if self.upload_ready:
            if self.row_count == 0 or self.relative_path is None or self.sha256 is None:
                raise ValueError("upload-ready tables require rows, a path, and a hash")
            if self.omission_reason is not None:
                raise ValueError("upload-ready tables cannot have an omission reason")
        elif (
            self.row_count != 0
            or self.relative_path is not None
            or self.sha256 is not None
            or self.omission_reason != "no_rows"
        ):
            raise ValueError("omitted tables must be empty and marked no_rows")
        return self


class PalantirTablePackageManifest(BaseModel):
    """Manifest for normalized files only; it does not authorize remote writes."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    package_version: Literal["1.3.0"] = "1.3.0"
    source_bundle_id: str = Field(min_length=1, max_length=200)
    source_manifest_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    source_import_plan_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    table_format: Literal["csv"] = "csv"
    nested_value_encoding: Literal["canonical_json"] = "canonical_json"
    timestamp_companion_encoding: Literal["utc_epoch_milliseconds"] = "utc_epoch_milliseconds"
    tables: tuple[PalantirTableEntry, ...]
    requires_authenticated_target: Literal[True] = True
    writes_performed: Literal[False] = False


def write_palantir_import_package(
    plan: PalantirImportPlan,
    output_directory: Path,
) -> PalantirTablePackageManifest:
    """Write an atomic normalized package without contacting Palantir.

    The destination must not already exist. This prevents rows from an older
    package from surviving a later export when an object or link disappears.
    """

    if output_directory.exists():
        raise FileExistsError(f"output directory already exists: {output_directory}")

    plan_bytes = plan.model_dump_json().encode("utf-8")
    rendered = _render_tables(plan)
    table_entries = tuple(
        PalantirTableEntry(
            kind=table.kind,
            logical_name=table.logical_name,
            relative_path=table.relative_path,
            row_count=table.row_count,
            columns=table.columns,
            sha256=_sha256_bytes(table.content) if table.content is not None else None,
            upload_ready=table.content is not None,
            omission_reason=None if table.content is not None else "no_rows",
        )
        for table in rendered
    )
    manifest = PalantirTablePackageManifest(
        source_bundle_id=plan.source_bundle_id,
        source_manifest_sha256=plan.source_manifest_sha256,
        source_import_plan_sha256=_sha256_bytes(plan_bytes),
        tables=table_entries,
    )

    output_directory.parent.mkdir(parents=True, exist_ok=True)
    temporary_directory = Path(
        tempfile.mkdtemp(
            prefix=f".{output_directory.name}.",
            dir=output_directory.parent,
        )
    )
    try:
        for table in rendered:
            if table.relative_path is None or table.content is None:
                continue
            destination = temporary_directory / table.relative_path
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(table.content)
        (temporary_directory / "package-manifest.json").write_text(
            f"{manifest.model_dump_json(indent=2)}\n",
            encoding="utf-8",
        )
        if output_directory.exists():
            raise FileExistsError(f"output directory already exists: {output_directory}")
        temporary_directory.rename(output_directory)
    except BaseException:
        shutil.rmtree(temporary_directory, ignore_errors=True)
        raise

    return manifest


@dataclass(frozen=True)
class _RenderedTable:
    kind: TableKind
    logical_name: str
    relative_path: str | None
    row_count: int
    columns: tuple[str, ...]
    content: bytes | None


def _render_tables(plan: PalantirImportPlan) -> tuple[_RenderedTable, ...]:
    rendered: list[_RenderedTable] = []
    for object_type in ONTOLOGY_OBJECT_TYPES:
        objects = sorted(
            (item for item in plan.objects if item.object_type == object_type),
            key=lambda item: item.primary_key,
        )
        object_values = [_object_values(item) for item in objects]
        columns = _object_columns(object_values)
        rows = []
        for item, values in zip(objects, object_values, strict=True):
            rows.append(
                {
                    "primary_key": item.primary_key,
                    **{key: values.get(key, "") for key in columns[1:]},
                }
            )
        logical_name = _OBJECT_TABLE_NAMES[object_type]
        rendered.append(
            _render_table(
                "ontology_objects",
                logical_name,
                f"objects/{logical_name}.csv",
                columns,
                rows,
            )
        )

    link_columns = (
        "link_type",
        "source_type",
        "source_primary_key",
        "target_type",
        "target_primary_key",
    )
    link_rows = [
        {
            "link_type": item.link_type,
            "source_type": item.source_type,
            "source_primary_key": item.source_primary_key,
            "target_type": item.target_type,
            "target_primary_key": item.target_primary_key,
        }
        for item in sorted(
            plan.links,
            key=lambda item: (
                item.link_type,
                item.source_primary_key,
                item.target_primary_key,
            ),
        )
    ]
    rendered.append(
        _render_table(
            "ontology_links",
            "ontology_links",
            "ontology_links.csv",
            link_columns,
            link_rows,
        )
    )

    join_columns = ("source_primary_key", "target_primary_key")
    for link_type in ONTOLOGY_LINK_TYPES:
        logical_name = _LINK_TABLE_NAMES[link_type]
        join_rows = [
            {
                "source_primary_key": item.source_primary_key,
                "target_primary_key": item.target_primary_key,
            }
            for item in sorted(
                (item for item in plan.links if item.link_type == link_type),
                key=lambda item: (item.source_primary_key, item.target_primary_key),
            )
        ]
        rendered.append(
            _render_table(
                "ontology_links",
                logical_name,
                f"links/{logical_name}.csv",
                join_columns,
                join_rows,
            )
        )

    media_columns = (
        "artifact_primary_key",
        "source_relative_path",
        "media_type",
        "sha256",
        "size_bytes",
    )
    media_rows = [
        {
            "artifact_primary_key": item.artifact_primary_key,
            "source_relative_path": item.source_relative_path,
            "media_type": item.media_type,
            "sha256": item.sha256,
            "size_bytes": str(item.size_bytes),
        }
        for item in sorted(plan.media_uploads, key=lambda item: item.artifact_primary_key)
    ]
    rendered.append(
        _render_table(
            "media_uploads",
            "media_uploads",
            "media_uploads.csv",
            media_columns,
            media_rows,
        )
    )
    return tuple(rendered)


def _render_table(
    kind: TableKind,
    logical_name: str,
    relative_path: str,
    columns: tuple[str, ...],
    rows: list[dict[str, str]],
) -> _RenderedTable:
    if not rows:
        return _RenderedTable(
            kind=kind,
            logical_name=logical_name,
            relative_path=None,
            row_count=0,
            columns=columns,
            content=None,
        )
    return _RenderedTable(
        kind=kind,
        logical_name=logical_name,
        relative_path=relative_path,
        row_count=len(rows),
        columns=columns,
        content=_csv_bytes(columns, rows),
    )


def _object_values(item: PalantirOntologyObject) -> dict[str, str]:
    values = {key: _cell_value(value) for key, value in item.properties.items()}
    for source_column in _TIMESTAMP_PROPERTIES[item.object_type]:
        if source_column not in item.properties:
            continue
        companion_column = f"{source_column}_epoch_millis"
        if companion_column in item.properties:
            raise ValueError(
                f"ontology properties cannot use reserved timestamp companion column "
                f"{companion_column}"
            )
        values[companion_column] = str(
            _utc_epoch_millis(item.properties[source_column], source_column)
        )
    return values


def _object_columns(object_values: list[dict[str, str]]) -> tuple[str, ...]:
    property_columns = sorted({key for values in object_values for key in values})
    if "primary_key" in property_columns:
        raise ValueError("ontology properties cannot use the reserved primary_key column")
    return ("primary_key", *property_columns)


def _utc_epoch_millis(value: object, source_column: str) -> int:
    if not isinstance(value, str):
        raise TypeError(f"{source_column} must be an RFC3339 string")
    fractional = re.search(r"\.(\d+)(?=Z$|[+-]\d{2}:\d{2}$)", value)
    if fractional is not None and any(digit != "0" for digit in fractional.group(1)[3:]):
        raise ValueError(
            f"{source_column} has sub-millisecond precision that cannot be represented without loss"
        )
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise ValueError(f"{source_column} must be a valid RFC3339 timestamp") from error
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{source_column} must include a UTC offset")

    utc_value = parsed.astimezone(UTC)
    if utc_value.microsecond % 1000:
        raise ValueError(
            f"{source_column} has sub-millisecond precision that cannot be represented without loss"
        )
    delta = utc_value - datetime(1970, 1, 1, tzinfo=UTC)
    return delta.days * 86_400_000 + delta.seconds * 1000 + delta.microseconds // 1000


def _cell_value(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    if isinstance(value, (str, int, float)):
        return str(value)
    raise TypeError(f"unsupported normalized property value: {type(value).__name__}")


def _csv_bytes(columns: tuple[str, ...], rows: list[dict[str, str]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=columns, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


def _sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()
