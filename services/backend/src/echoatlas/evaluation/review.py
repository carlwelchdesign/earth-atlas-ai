"""Generate a local-only human review packet from validated pipeline outputs."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import Literal, cast
from urllib.parse import quote

from PIL import Image
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from echoatlas.evaluation.review_template import render_review_html
from echoatlas.processor.changes.models import (
    CandidateFeatureCollection,
    ChangeArtifactRecord,
    ChangeRunManifest,
)
from echoatlas.processor.previews.models import ArtifactRecord, ProcessingRunManifest


class ReviewInputError(ValueError):
    """Raised when source pipeline outputs cannot support a review packet."""


class ReviewOutputExistsError(FileExistsError):
    """Raised when packet generation would overwrite an existing directory."""


class ReviewArtifact(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    role: Literal["before", "after", "candidate-overlay"]
    source_url: str
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    width: int = Field(gt=0)
    height: int = Field(gt=0)


class ReviewCandidate(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    candidate_id: str
    projected_bbox: tuple[float, float, float, float]
    pixel_count: int = Field(gt=0)
    area_square_meters: float = Field(gt=0)
    mean_change_score: float = Field(ge=0, le=1)
    p95_change_score: float = Field(ge=0, le=1)
    warnings: tuple[str, ...]


class ReviewPacket(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    review_packet_version: Literal["1.0.0"] = "1.0.0"
    packet_id: str
    selection_id: str
    processing_aoi_id: str
    processing_run_id: str
    change_run_id: str
    source_license: dict[str, str]
    source_inputs: tuple[dict[str, object], dict[str, object]]
    grid: dict[str, object]
    artifacts: tuple[ReviewArtifact, ReviewArtifact, ReviewArtifact]
    candidates: tuple[ReviewCandidate, ...]
    interpretation_limits: tuple[str, ...]
    sensitivity_controls: tuple[str, ...]
    review_boundary: str = (
        "Candidate review decisions are audit evidence only. They are not independent "
        "reference regions and cannot establish pipeline accuracy."
    )


def prepare_review_packet(
    change_run: Path,
    preview_run: Path,
    output_directory: Path,
) -> ReviewPacket:
    """Validate immutable artifacts and atomically create a local HTML review packet."""

    if output_directory.exists():
        raise ReviewOutputExistsError(f"review output already exists: {output_directory}")
    manifest = _read_model(
        change_run / "change-manifest.json", ChangeRunManifest, "change manifest"
    )
    candidate_record = _change_record(manifest, "candidate-geojson")
    candidate_path = _validated_artifact(change_run, candidate_record)
    processing_manifest_path = preview_run / "processing-manifest.json"
    processing = _read_model(
        processing_manifest_path,
        ProcessingRunManifest,
        "processing manifest",
    )
    if _sha256(processing_manifest_path) != manifest.source_processing_manifest_sha256:
        raise ReviewInputError("processing manifest checksum does not match the change run")
    quality_path, quality_sha256, quality_size = _quality_record(processing)
    if quality_sha256 != manifest.source_quality_report_sha256:
        raise ReviewInputError("quality report checksum does not match the change run")
    _validated_declared_artifact(
        preview_run,
        quality_path,
        expected_sha256=quality_sha256,
        expected_size=quality_size,
    )
    candidates = _read_model(
        candidate_path,
        CandidateFeatureCollection,
        "candidate collection",
    )
    _validate_identity(change_run, preview_run, manifest, processing, candidates)

    before_record = _preview_record(processing, "before")
    after_record = _preview_record(processing, "after")
    overlay_record = _change_record(manifest, "candidate-overlay")
    before_path = _validated_artifact(preview_run, before_record)
    after_path = _validated_artifact(preview_run, after_record)
    overlay_path = _validated_artifact(change_run, overlay_record)
    dimensions = (processing.grid.width, processing.grid.height)
    for label, path in (
        ("before preview", before_path),
        ("after preview", after_path),
        ("candidate overlay", overlay_path),
    ):
        with Image.open(path) as image:
            if image.size != dimensions:
                raise ReviewInputError(
                    f"{label} dimensions {image.size} do not match grid {dimensions}"
                )

    output_directory.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(
        tempfile.mkdtemp(prefix=f".{output_directory.name}-", dir=output_directory.parent)
    )
    try:
        packet = _build_packet(
            manifest,
            processing,
            candidates,
            output_root=temporary,
            artifact_paths=(before_path, after_path, overlay_path),
            artifact_hashes=(
                before_record.sha256,
                after_record.sha256,
                overlay_record.sha256,
            ),
        )
        (temporary / "review-packet.json").write_text(
            f"{json.dumps(packet.model_dump(mode='json'), indent=2, sort_keys=True)}\n"
        )
        (temporary / "index.html").write_text(render_review_html(packet))
        temporary.replace(output_directory)
        return packet
    except Exception:
        shutil.rmtree(temporary, ignore_errors=True)
        raise


def _build_packet(
    manifest: ChangeRunManifest,
    processing: ProcessingRunManifest,
    candidates: CandidateFeatureCollection,
    *,
    output_root: Path,
    artifact_paths: tuple[Path, Path, Path],
    artifact_hashes: tuple[str, str, str],
) -> ReviewPacket:
    packet_identity = json.dumps(
        {
            "change_run_id": manifest.change_run_id,
            "candidate_hash": _change_record(manifest, "candidate-geojson").sha256,
            "artifact_hashes": artifact_hashes,
            "review_packet_version": "1.0.0",
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode()
    roles: tuple[Literal["before"], Literal["after"], Literal["candidate-overlay"]] = (
        "before",
        "after",
        "candidate-overlay",
    )
    artifacts = tuple(
        ReviewArtifact(
            role=cast(Literal["before", "after", "candidate-overlay"], role),
            source_url=_relative_url(output_root, path),
            sha256=sha256,
            width=processing.grid.width,
            height=processing.grid.height,
        )
        for role, path, sha256 in zip(
            roles,
            artifact_paths,
            artifact_hashes,
            strict=True,
        )
    )
    review_candidates = tuple(
        ReviewCandidate(
            candidate_id=feature.id,
            projected_bbox=feature.properties.measurements.projected_bbox,
            pixel_count=feature.properties.measurements.pixel_count,
            area_square_meters=feature.properties.measurements.area_square_meters,
            mean_change_score=feature.properties.score_components.mean_change_score,
            p95_change_score=feature.properties.score_components.p95_change_score,
            warnings=feature.properties.warnings,
        )
        for feature in candidates.features
    )
    return ReviewPacket(
        packet_id=f"review-{hashlib.sha256(packet_identity).hexdigest()[:20]}",
        selection_id=processing.selection_id,
        processing_aoi_id=processing.processing_aoi_id,
        processing_run_id=processing.run_id,
        change_run_id=manifest.change_run_id,
        source_license=processing.source_license,
        source_inputs=processing.inputs,
        grid=processing.grid.model_dump(mode="json"),
        artifacts=artifacts,  # type: ignore[arg-type]
        candidates=review_candidates,
        interpretation_limits=processing.interpretation_limits,
        sensitivity_controls=processing.sensitivity_controls,
    )


def _validate_identity(
    change_run: Path,
    preview_run: Path,
    manifest: ChangeRunManifest,
    processing: ProcessingRunManifest,
    candidates: CandidateFeatureCollection,
) -> None:
    if change_run.name != manifest.change_run_id:
        raise ReviewInputError("change manifest ID does not match its directory")
    if preview_run.name != processing.run_id:
        raise ReviewInputError("processing manifest ID does not match its directory")
    if manifest.source_processing_run_id != processing.run_id:
        raise ReviewInputError("change and processing runs do not share lineage")
    if candidates.change_run_id != manifest.change_run_id:
        raise ReviewInputError("candidate collection does not match the change run")
    if candidates.source_processing_run_id != processing.run_id:
        raise ReviewInputError("candidate collection does not match the processing run")
    if len(candidates.features) != manifest.candidate_count:
        raise ReviewInputError("candidate count does not match the change manifest")
    if any(
        feature.properties.change_run_id != manifest.change_run_id
        for feature in candidates.features
    ):
        raise ReviewInputError("candidate feature does not match the change run")


def _preview_record(
    processing: ProcessingRunManifest, role: Literal["before", "after"]
) -> ArtifactRecord:
    records = [
        record
        for record in processing.artifacts
        if record.role == role and record.kind == "preview"
    ]
    if len(records) != 1:
        raise ReviewInputError(f"processing manifest requires one {role} preview")
    return records[0]


def _change_record(
    manifest: ChangeRunManifest,
    kind: Literal["candidate-overlay", "candidate-geojson"],
) -> ChangeArtifactRecord:
    records = [record for record in manifest.artifacts if record.kind == kind]
    if len(records) != 1:
        raise ReviewInputError(f"change manifest requires one {kind} artifact")
    return records[0]


def _validated_artifact(root: Path, record: ArtifactRecord | ChangeArtifactRecord) -> Path:
    return _validated_declared_artifact(
        root,
        record.relative_path,
        expected_sha256=record.sha256,
        expected_size=record.size_bytes,
    )


def _validated_declared_artifact(
    root: Path,
    relative_path: str,
    *,
    expected_sha256: str,
    expected_size: int,
) -> Path:
    path = (root / relative_path).resolve()
    try:
        path.relative_to(root.resolve())
    except ValueError as error:
        raise ReviewInputError("artifact path escapes its run directory") from error
    try:
        size = path.stat().st_size
    except OSError as error:
        raise ReviewInputError(f"artifact could not be read: {relative_path}") from error
    if size != expected_size:
        raise ReviewInputError(f"artifact size changed: {relative_path}")
    if _sha256(path) != expected_sha256:
        raise ReviewInputError(f"artifact checksum changed: {relative_path}")
    return path


def _quality_record(processing: ProcessingRunManifest) -> tuple[str, str, int]:
    relative_path = processing.quality_report.get("relative_path")
    sha256 = processing.quality_report.get("sha256")
    size_bytes = processing.quality_report.get("size_bytes")
    if (
        not isinstance(relative_path, str)
        or not isinstance(sha256, str)
        or not isinstance(size_bytes, int)
    ):
        raise ReviewInputError("processing manifest has no usable quality-report record")
    return relative_path, sha256, size_bytes


def _relative_url(output_root: Path, source: Path) -> str:
    relative = os.path.relpath(source.resolve(), output_root.resolve())
    return quote(Path(relative).as_posix(), safe="/.-_~")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _read_model[T: BaseModel](path: Path, model: type[T], label: str) -> T:
    try:
        return model.model_validate_json(path.read_text())
    except OSError as error:
        raise ReviewInputError(f"{label} could not be read: {path}") from error
    except ValidationError as error:
        raise ReviewInputError(f"{label} failed validation: {error}") from error
