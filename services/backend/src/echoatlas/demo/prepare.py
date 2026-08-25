"""Validate pipeline lineage and stage a browser-safe, local real-data bundle."""

from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Literal

from PIL import Image
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from echoatlas.processor.acquisition.models import (
    PinnedObject,
    ProcessingAoi,
    SelectionManifest,
    SourceLicense,
)
from echoatlas.processor.changes.models import (
    CandidateFeature,
    CandidateFeatureCollection,
    ChangeArtifactRecord,
    ChangeRunManifest,
)
from echoatlas.processor.previews.models import ArtifactRecord, ProcessingRunManifest


class PreparedDemoInputError(ValueError):
    """Raised when the source runs cannot safely support the prepared demo."""


class PreparedDemoOutputExistsError(FileExistsError):
    """Raised when preparation would overwrite an existing output directory."""


class DemoStory(BaseModel):
    model_config = ConfigDict(frozen=True, extra="ignore")

    title: str = Field(min_length=1)


class DemoAcquisition(BaseModel):
    model_config = ConfigDict(frozen=True, extra="ignore")

    item_id: str
    acquired_at: datetime
    item_url: str
    platform: str
    product_type: str
    polarizations: tuple[str, ...]
    resolution_range_m: float = Field(gt=0)
    incidence_angle_deg: float = Field(gt=0)
    object: PinnedObject


class DemoSelection(BaseModel):
    model_config = ConfigDict(frozen=True, extra="ignore")

    manifest_version: Literal["1.0.0"]
    selection_id: str
    status: Literal["approved"]
    accessed_at: datetime
    story: DemoStory
    license: SourceLicense
    processing_aoi: ProcessingAoi
    acquisitions: dict[str, DemoAcquisition]
    interpretation_limits: tuple[str, ...]
    sensitivity_controls: tuple[str, ...]

    @field_validator("acquisitions")
    @classmethod
    def validate_roles(cls, value: dict[str, DemoAcquisition]) -> dict[str, DemoAcquisition]:
        if set(value) != {"before", "after"}:
            raise ValueError("selection requires exactly before and after acquisitions")
        return value


class PreparedDemo(BaseModel):
    model_config = ConfigDict(frozen=True)

    output_directory: Path
    bundle_path: Path
    manifest_path: Path
    candidate_count: int = Field(ge=0)


def prepare_workbench_demo(
    *,
    selection_manifest_path: Path,
    preview_run: Path,
    change_run: Path,
    output_directory: Path,
) -> PreparedDemo:
    """Validate immutable run outputs and atomically stage display-only assets."""

    if output_directory.exists():
        raise PreparedDemoOutputExistsError(
            f"prepared demo output already exists: {output_directory}"
        )

    selection_document = _read_json(selection_manifest_path, "selection manifest")
    selection = _read_selection(selection_document)
    processing_path = preview_run / "processing-manifest.json"
    processing = _read_model(processing_path, ProcessingRunManifest, "processing manifest")
    change_path = change_run / "change-manifest.json"
    change = _read_model(change_path, ChangeRunManifest, "change manifest")

    candidate_record = _one_change_artifact(change, "candidate-geojson")
    candidate_path = _validated_artifact(change_run, candidate_record)
    candidates = _read_model(candidate_path, CandidateFeatureCollection, "candidate collection")
    _validate_lineage(
        selection=selection,
        processing=processing,
        processing_path=processing_path,
        change=change,
        preview_run=preview_run,
        change_run=change_run,
        candidates=candidates,
    )

    before_record = _one_preview_artifact(processing, "before", "thumbnail")
    after_record = _one_preview_artifact(processing, "after", "thumbnail")
    score_record = _one_change_artifact(change, "change-score-preview")
    overlay_record = _one_change_artifact(change, "candidate-overlay")
    source_assets: dict[str, tuple[Path, ArtifactRecord | ChangeArtifactRecord]] = {
        "before.png": (_validated_artifact(preview_run, before_record), before_record),
        "after.png": (_validated_artifact(preview_run, after_record), after_record),
        "change-score.png": (_validated_artifact(change_run, score_record), score_record),
        "candidate-overlay.png": (
            _validated_artifact(change_run, overlay_record),
            overlay_record,
        ),
        "candidates.geojson": (candidate_path, candidate_record),
    }
    _validate_display_dimensions(source_assets, processing)

    output_directory.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(
        tempfile.mkdtemp(prefix=f".{output_directory.name}-", dir=output_directory.parent)
    )
    try:
        for file_name, (source_path, _) in source_assets.items():
            shutil.copyfile(source_path, temporary / file_name)
        bundle = _build_bundle(selection, processing, change, candidates, source_assets)
        bundle_path = temporary / "bundle.json"
        bundle_path.write_text(f"{json.dumps(bundle, indent=2, sort_keys=True)}\n")
        staged_files = tuple(sorted(path for path in temporary.iterdir() if path.is_file()))
        preparation_manifest = {
            "prepared_demo_manifest_version": "1.0.0",
            "selection_id": selection.selection_id,
            "processing_run_id": processing.run_id,
            "change_run_id": change.change_run_id,
            "source_manifests": {
                "selection_sha256": _sha256(selection_manifest_path),
                "processing_sha256": _sha256(processing_path),
                "change_sha256": _sha256(change_path),
            },
            "staged_files": [
                {
                    "name": path.name,
                    "sha256": _sha256(path),
                    "size_bytes": path.stat().st_size,
                }
                for path in staged_files
            ],
            "exclusions": [
                "raw acquisition GeoTIFFs",
                "aligned raster GeoTIFFs",
                "candidate mask and change-score GeoTIFFs",
                "cache and provider payloads",
                "analyst assessment state",
            ],
        }
        manifest_path = temporary / "prepared-demo-manifest.json"
        manifest_path.write_text(f"{json.dumps(preparation_manifest, indent=2, sort_keys=True)}\n")
        temporary.replace(output_directory)
    except Exception:
        shutil.rmtree(temporary, ignore_errors=True)
        raise

    return PreparedDemo(
        output_directory=output_directory,
        bundle_path=output_directory / "bundle.json",
        manifest_path=output_directory / "prepared-demo-manifest.json",
        candidate_count=len(candidates.features),
    )


def _read_selection(document: dict[str, Any]) -> DemoSelection:
    try:
        SelectionManifest.model_validate(document)
        return DemoSelection.model_validate(document)
    except ValidationError as error:
        raise PreparedDemoInputError(f"selection manifest failed validation: {error}") from error


def _validate_lineage(
    *,
    selection: DemoSelection,
    processing: ProcessingRunManifest,
    processing_path: Path,
    change: ChangeRunManifest,
    preview_run: Path,
    change_run: Path,
    candidates: CandidateFeatureCollection,
) -> None:
    if preview_run.name != processing.run_id:
        raise PreparedDemoInputError("processing manifest ID does not match its directory")
    if change_run.name != change.change_run_id:
        raise PreparedDemoInputError("change manifest ID does not match its directory")
    if selection.selection_id != processing.selection_id:
        raise PreparedDemoInputError("selection and processing run do not share lineage")
    if selection.processing_aoi.id != processing.processing_aoi_id:
        raise PreparedDemoInputError("selection AOI does not match the processing run")
    if selection.processing_aoi.geometry_sha256 != processing.processing_aoi_geometry_sha256:
        raise PreparedDemoInputError("selection AOI checksum does not match the processing run")
    if change.source_processing_run_id != processing.run_id:
        raise PreparedDemoInputError("change and processing runs do not share lineage")
    if change.source_processing_manifest_sha256 != _sha256(processing_path):
        raise PreparedDemoInputError("processing manifest checksum does not match change run")
    if candidates.change_run_id != change.change_run_id:
        raise PreparedDemoInputError("candidate collection does not match change run")
    if candidates.source_processing_run_id != processing.run_id:
        raise PreparedDemoInputError("candidate collection does not match processing run")
    if len(candidates.features) != change.candidate_count:
        raise PreparedDemoInputError("candidate count does not match change manifest")
    expected_items = {
        role: acquisition.item_id for role, acquisition in selection.acquisitions.items()
    }
    processing_items = {
        str(source.get("role")): str(source.get("item_id")) for source in processing.inputs
    }
    if processing_items != expected_items:
        raise PreparedDemoInputError("processing inputs do not match pinned acquisitions")
    quality = processing.quality_report
    quality_path = quality.get("relative_path")
    quality_sha256 = quality.get("sha256")
    quality_size = quality.get("size_bytes")
    if not isinstance(quality_path, str) or not isinstance(quality_sha256, str):
        raise PreparedDemoInputError("processing quality report record is invalid")
    if not isinstance(quality_size, int):
        raise PreparedDemoInputError("processing quality report size is invalid")
    _validated_declared_artifact(
        preview_run,
        quality_path,
        expected_sha256=quality_sha256,
        expected_size=quality_size,
    )
    if quality_sha256 != change.source_quality_report_sha256:
        raise PreparedDemoInputError("quality report checksum does not match change run")


def _build_bundle(
    selection: DemoSelection,
    processing: ProcessingRunManifest,
    change: ChangeRunManifest,
    candidates: CandidateFeatureCollection,
    source_assets: dict[str, tuple[Path, ArtifactRecord | ChangeArtifactRecord]],
) -> dict[str, Any]:
    before = selection.acquisitions["before"]
    after = selection.acquisitions["after"]
    artifacts = [
        _bundle_artifact("artifact-before", "Before SAR thumbnail", "before.png", source_assets),
        _bundle_artifact("artifact-after", "After SAR thumbnail", "after.png", source_assets),
        _bundle_artifact(
            "artifact-score-preview", "Change-score preview", "change-score.png", source_assets
        ),
        _bundle_artifact(
            "artifact-candidate-overlay",
            "Candidate overlay",
            "candidate-overlay.png",
            source_assets,
        ),
        _bundle_artifact(
            "artifact-candidates", "Candidate GeoJSON", "candidates.geojson", source_assets
        ),
    ]
    evidence_ids = [artifact["id"] for artifact in artifacts]
    return {
        "contractVersion": "1.0.0",
        "bundleId": f"bundle-{change.change_run_id}",
        "status": "succeeded",
        "createdAt": selection.accessed_at.isoformat().replace("+00:00", "Z"),
        "mission": {
            "title": selection.story.title,
            "boundaryLabel": selection.processing_aoi.boundary,
        },
        "freshness": {
            "state": "current",
            "evaluatedAt": selection.accessed_at.isoformat().replace("+00:00", "Z"),
            "reason": None,
        },
        "permissions": {"assessments": {"state": "allowed", "reason": None}},
        "acquisitions": [
            _bundle_acquisition("before", before),
            _bundle_acquisition("after", after),
        ],
        "candidates": [
            _bundle_candidate(feature, index, processing, evidence_ids)
            for index, feature in enumerate(candidates.features, start=1)
        ],
        "qualityWarnings": [],
        "evidence": {
            "lineage": "satellite-derived",
            "lineageNotice": (
                "These images and measurements are derived from the pinned public Umbra SAR "
                "acquisitions. Candidates are unreviewed engineering signals, not confirmed change."
            ),
            "attribution": (
                f"Umbra Lab Inc public SAR data · {selection.license.spdx} · derived by EchoAtlas"
            ),
            "license": {
                "label": "Creative Commons Attribution 4.0",
                "href": "https://creativecommons.org/licenses/by/4.0/",
                "status": "available",
            },
            "software": {
                "version": f"echoatlas {change.software.get('echoatlas', 'unknown')}",
                "commit": change.software.get("commit", "unknown"),
            },
            "run": {
                "id": change.change_run_id,
                "parameters": _run_parameters(processing, change),
            },
            "acquisitions": [
                _acquisition_evidence("before", before),
                _acquisition_evidence("after", after),
            ],
            "artifacts": artifacts,
            "warnings": list(
                dict.fromkeys(
                    [
                        *processing.interpretation_limits,
                        *change.warnings,
                        *candidates.warnings,
                    ]
                )
            ),
        },
    }


def _bundle_acquisition(
    role: Literal["before", "after"], source: DemoAcquisition
) -> dict[str, Any]:
    return {
        "id": source.item_id,
        "role": role,
        "acquiredAt": source.acquired_at.isoformat().replace("+00:00", "Z"),
        "label": role.capitalize(),
        "artifact": {
            "available": True,
            "mediaType": "image/png",
            "src": f"/generated-demo/{role}.png",
        },
    }


def _acquisition_evidence(
    role: Literal["before", "after"], source: DemoAcquisition
) -> dict[str, Any]:
    return {
        "acquisitionId": source.item_id,
        "provider": f"Umbra Lab Inc · {source.platform}",
        "productType": source.product_type,
        "polarization": ", ".join(source.polarizations),
        "resolutionMeters": source.resolution_range_m,
        "incidenceAngleDegrees": source.incidence_angle_deg,
        "source": {
            "label": f"{role.capitalize()} Umbra STAC item",
            "href": source.item_url,
            "status": "available",
        },
        "checksum": {
            "algorithm": source.object.checksum.algorithm,
            "value": source.object.checksum.value,
        },
    }


def _bundle_candidate(
    feature: CandidateFeature,
    index: int,
    processing: ProcessingRunManifest,
    evidence_ids: list[str],
) -> dict[str, Any]:
    measurements = feature.properties.measurements
    min_x, min_y, max_x, max_y = measurements.projected_bbox
    grid_min_x, grid_min_y, grid_max_x, grid_max_y = processing.grid.bounds
    grid_width = grid_max_x - grid_min_x
    grid_height = grid_max_y - grid_min_y
    return {
        "id": f"C-{index:03d}",
        "areaSquareMeters": measurements.area_square_meters,
        "pixelCount": measurements.pixel_count,
        "heuristicScore": feature.properties.score_components.mean_change_score,
        "warningCount": len(feature.properties.warnings),
        "evidenceArtifactIds": evidence_ids,
        "warnings": list(feature.properties.warnings),
        "mapPosition": {
            "leftPercent": _percent((min_x - grid_min_x) / grid_width),
            "topPercent": _percent((grid_max_y - max_y) / grid_height),
            "widthPercent": _percent((max_x - min_x) / grid_width),
            "heightPercent": _percent((max_y - min_y) / grid_height),
            "rotationDegrees": 0,
        },
    }


def _percent(ratio: float) -> float:
    return round(min(max(ratio * 100, 0), 100), 6)


def _run_parameters(
    processing: ProcessingRunManifest, change: ChangeRunManifest
) -> list[dict[str, str]]:
    return [
        {
            "name": "Target grid",
            "value": f"{processing.grid.crs} · {processing.grid.resolution:g} m",
        },
        {
            "name": "Normalization",
            "value": (
                f"{processing.parameters.normalization} · "
                f"{processing.parameters.lower_percentile:g}–"
                f"{processing.parameters.upper_percentile:g} percentile"
            ),
        },
        {"name": "Resampling", "value": processing.parameters.resampling},
        {"name": "Filter", "value": processing.parameters.filter},
        {"name": "Score method", "value": change.parameters.score_method},
        {"name": "Score threshold", "value": f"{change.parameters.score_threshold:g}"},
        {
            "name": "Registration tolerance",
            "value": f"{change.parameters.registration_tolerance_pixels} px",
        },
        {
            "name": "Minimum component",
            "value": f"{change.parameters.minimum_component_pixels} px",
        },
    ]


def _bundle_artifact(
    artifact_id: str,
    label: str,
    file_name: str,
    source_assets: dict[str, tuple[Path, ArtifactRecord | ChangeArtifactRecord]],
) -> dict[str, Any]:
    path, record = source_assets[file_name]
    return {
        "id": artifact_id,
        "label": label,
        "mediaType": record.media_type,
        "path": f"/generated-demo/{file_name}",
        "sha256": record.sha256,
        "sizeBytes": path.stat().st_size,
        "required": True,
        "available": True,
    }


def _validate_display_dimensions(
    assets: dict[str, tuple[Path, ArtifactRecord | ChangeArtifactRecord]],
    processing: ProcessingRunManifest,
) -> None:
    expected_grid = (processing.grid.width, processing.grid.height)
    for file_name in ("before.png", "after.png"):
        path, record = assets[file_name]
        if not isinstance(record, ArtifactRecord):
            raise PreparedDemoInputError(f"{file_name} is not a preview artifact")
        with Image.open(path) as image:
            if image.size != (record.width, record.height):
                raise PreparedDemoInputError(f"{file_name} dimensions do not match its manifest")
    for file_name in ("change-score.png", "candidate-overlay.png"):
        path, _ = assets[file_name]
        with Image.open(path) as image:
            if image.size != expected_grid:
                raise PreparedDemoInputError(
                    f"{file_name} dimensions {image.size} do not match grid {expected_grid}"
                )


def _one_preview_artifact(
    processing: ProcessingRunManifest,
    role: Literal["before", "after"],
    kind: Literal["thumbnail"],
) -> ArtifactRecord:
    records = [
        record for record in processing.artifacts if record.role == role and record.kind == kind
    ]
    if len(records) != 1:
        raise PreparedDemoInputError(f"processing manifest requires one {role} {kind}")
    return records[0]


def _one_change_artifact(
    change: ChangeRunManifest,
    kind: Literal["change-score-preview", "candidate-overlay", "candidate-geojson"],
) -> ChangeArtifactRecord:
    records = [record for record in change.artifacts if record.kind == kind]
    if len(records) != 1:
        raise PreparedDemoInputError(f"change manifest requires one {kind} artifact")
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
        raise PreparedDemoInputError("artifact path escapes its run directory") from error
    try:
        size = path.stat().st_size
    except OSError as error:
        raise PreparedDemoInputError(f"artifact could not be read: {relative_path}") from error
    if size != expected_size:
        raise PreparedDemoInputError(f"artifact size changed: {relative_path}")
    if _sha256(path) != expected_sha256:
        raise PreparedDemoInputError(f"artifact checksum changed: {relative_path}")
    return path


def _read_json(path: Path, label: str) -> dict[str, Any]:
    try:
        document: Any = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as error:
        raise PreparedDemoInputError(f"{label} could not be read: {path}") from error
    if not isinstance(document, dict):
        raise PreparedDemoInputError(f"{label} root must be an object")
    return document


def _read_model[T: BaseModel](path: Path, model: type[T], label: str) -> T:
    try:
        return model.model_validate_json(path.read_text())
    except OSError as error:
        raise PreparedDemoInputError(f"{label} could not be read: {path}") from error
    except ValidationError as error:
        raise PreparedDemoInputError(f"{label} failed validation: {error}") from error


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()
