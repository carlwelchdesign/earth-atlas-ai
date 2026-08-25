"""Render a Palantir import plan as deterministic, schema-inferable CSV tables."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import shutil
import tempfile
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from echoatlas.adapters.palantir import (
    ONTOLOGY_OBJECT_TYPES,
    OntologyObjectType,
    PalantirImportPlan,
    PalantirOntologyObject,
)

TableKind = Literal["ontology_objects", "ontology_links", "media_uploads"]

_OBJECT_TABLE_NAMES: dict[OntologyObjectType, str] = {
    "AreaOfInterest": "area_of_interest",
    "Acquisition": "acquisition",
    "AnalysisRun": "analysis_run",
    "EvidenceArtifact": "evidence_artifact",
    "ChangeCandidate": "change_candidate",
    "AnalystAssessment": "analyst_assessment",
}


class PalantirTableFile(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    kind: TableKind
    logical_name: str = Field(min_length=1, max_length=200)
    relative_path: str = Field(min_length=1, max_length=1000)
    row_count: int = Field(ge=0)
    columns: tuple[str, ...]
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")


class PalantirTablePackageManifest(BaseModel):
    """Manifest for normalized files only; it does not authorize remote writes."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    package_version: Literal["1.0.0"] = "1.0.0"
    source_bundle_id: str = Field(min_length=1, max_length=200)
    source_manifest_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    source_import_plan_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    table_format: Literal["csv"] = "csv"
    nested_value_encoding: Literal["canonical_json"] = "canonical_json"
    tables: tuple[PalantirTableFile, ...]
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
    table_files = tuple(
        PalantirTableFile(
            kind=kind,
            logical_name=logical_name,
            relative_path=relative_path,
            row_count=row_count,
            columns=columns,
            sha256=_sha256_bytes(content),
        )
        for kind, logical_name, relative_path, row_count, columns, content in rendered
    )
    manifest = PalantirTablePackageManifest(
        source_bundle_id=plan.source_bundle_id,
        source_manifest_sha256=plan.source_manifest_sha256,
        source_import_plan_sha256=_sha256_bytes(plan_bytes),
        tables=table_files,
    )

    output_directory.parent.mkdir(parents=True, exist_ok=True)
    temporary_directory = Path(
        tempfile.mkdtemp(
            prefix=f".{output_directory.name}.",
            dir=output_directory.parent,
        )
    )
    try:
        for _, _, relative_path, _, _, content in rendered:
            destination = temporary_directory / relative_path
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(content)
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


def _render_tables(
    plan: PalantirImportPlan,
) -> tuple[
    tuple[TableKind, str, str, int, tuple[str, ...], bytes],
    ...,
]:
    rendered: list[tuple[TableKind, str, str, int, tuple[str, ...], bytes]] = []
    for object_type in ONTOLOGY_OBJECT_TYPES:
        objects = sorted(
            (item for item in plan.objects if item.object_type == object_type),
            key=lambda item: item.primary_key,
        )
        columns = _object_columns(objects)
        rows = [
            {
                "primary_key": item.primary_key,
                **{key: _cell_value(item.properties.get(key)) for key in columns[1:]},
            }
            for item in objects
        ]
        logical_name = _OBJECT_TABLE_NAMES[object_type]
        relative_path = f"objects/{logical_name}.csv"
        rendered.append(
            (
                "ontology_objects",
                logical_name,
                relative_path,
                len(rows),
                columns,
                _csv_bytes(columns, rows),
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
        (
            "ontology_links",
            "ontology_links",
            "ontology_links.csv",
            len(link_rows),
            link_columns,
            _csv_bytes(link_columns, link_rows),
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
        (
            "media_uploads",
            "media_uploads",
            "media_uploads.csv",
            len(media_rows),
            media_columns,
            _csv_bytes(media_columns, media_rows),
        )
    )
    return tuple(rendered)


def _object_columns(objects: list[PalantirOntologyObject]) -> tuple[str, ...]:
    property_columns = sorted({key for item in objects for key in item.properties})
    if "primary_key" in property_columns:
        raise ValueError("ontology properties cannot use the reserved primary_key column")
    return ("primary_key", *property_columns)


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
