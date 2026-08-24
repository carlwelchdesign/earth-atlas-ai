"""Deterministic baseline scoring and vectorization for review-only candidates."""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import shutil
from pathlib import Path
from typing import Literal, cast
from uuid import uuid4

import numpy as np
import numpy.typing as npt
import rasterio  # type: ignore[import-untyped]
from affine import Affine
from PIL import Image
from PIL import __version__ as pillow_version
from pydantic import ValidationError
from rasterio.features import shapes  # type: ignore[import-untyped]
from rasterio.transform import array_bounds  # type: ignore[import-untyped]
from rasterio.warp import transform_geom  # type: ignore[import-untyped]
from scipy import __version__ as scipy_version  # type: ignore[import-untyped]
from scipy import ndimage

from echoatlas import __version__
from echoatlas.processor.changes.models import (
    CandidateFeature,
    CandidateFeatureCollection,
    CandidateMeasurements,
    CandidateProperties,
    CandidateScoreComponents,
    ChangeArtifactRecord,
    ChangeParameters,
    ChangeProcessingResult,
    ChangeRunManifest,
)
from echoatlas.processor.previews.models import (
    ArtifactRecord,
    GridRecord,
    ProcessingRunManifest,
    QualityReport,
    RoleQualityRecord,
)

_COMMIT_PATTERN = re.compile(r"^[a-f0-9]{7,64}$")


class ChangeProcessingError(RuntimeError):
    """Base class for candidate-processing failures."""


class ChangeInputError(ChangeProcessingError):
    """The source preview run is incomplete, inconsistent, or modified."""


class CandidateLimitError(ChangeProcessingError):
    """The declared policy produces too many review candidates."""


class ChangeOutputExistsError(ChangeProcessingError):
    """A deterministic change-run output already exists and is immutable."""


def process_change_candidates(
    preview_run_directory: Path,
    *,
    output_root: Path,
    software_commit: str,
    parameters: ChangeParameters | None = None,
) -> ChangeProcessingResult:
    config = parameters or ChangeParameters()
    commit = software_commit.lower()
    if not _COMMIT_PATTERN.fullmatch(commit):
        raise ChangeInputError("software commit must be a 7-64 character lowercase Git SHA")

    processing_manifest, quality_report = _load_source_contract(preview_run_directory)
    source_manifest_sha = _sha256_file(preview_run_directory / "processing-manifest.json")
    source_quality_sha = _sha256_file(preview_run_directory / "quality-report.json")
    aligned_artifacts = _aligned_artifacts(processing_manifest)
    aligned_paths = {
        artifact.role: _verified_artifact_path(preview_run_directory, artifact)
        for artifact in aligned_artifacts
    }
    change_run_id = _change_run_id(
        processing_manifest,
        source_manifest_sha,
        source_quality_sha,
        aligned_artifacts,
        config,
        commit,
    )
    final_directory = output_root / change_run_id
    if final_directory.exists():
        raise ChangeOutputExistsError(f"change output already exists: {final_directory}")

    grid = processing_manifest.grid
    before = _read_aligned("before", aligned_paths["before"], grid)
    after = _read_aligned("after", aligned_paths["after"], grid)
    ranges = _normalization_ranges(quality_report)
    before_normalized = _normalize(before, ranges["before"])
    after_normalized = _normalize(after, ranges["after"])
    common_valid = np.isfinite(before_normalized) & np.isfinite(after_normalized)
    if config.registration_tolerance_pixels:
        common_valid = ndimage.binary_erosion(
            common_valid,
            structure=np.ones((3, 3), dtype=np.bool_),
            iterations=config.registration_tolerance_pixels,
            border_value=0,
        )
    common_valid_count = int(np.count_nonzero(common_valid))
    if common_valid_count == 0:
        raise ChangeInputError("source run has no common valid pixels after edge guard")

    score = _symmetric_neighborhood_score(
        before_normalized,
        after_normalized,
        common_valid,
        config.registration_tolerance_pixels,
    )
    threshold_mask = (score >= config.score_threshold) & common_valid
    cleaned_mask = _clean_mask(threshold_mask, config)
    candidate_mask, labels, candidate_count = _retain_candidates(cleaned_mask, config)
    if candidate_count > config.maximum_candidate_count:
        raise CandidateLimitError(
            f"policy produced {candidate_count} candidates, above the configured maximum "
            f"of {config.maximum_candidate_count}"
        )

    warnings = _warnings(config)
    features = _candidate_features(
        labels,
        score,
        after_normalized - before_normalized,
        grid,
        change_run_id,
        processing_manifest.run_id,
    )
    feature_collection = CandidateFeatureCollection(
        change_run_id=change_run_id,
        source_processing_run_id=processing_manifest.run_id,
        warnings=warnings,
        features=features,
    )

    output_root.mkdir(parents=True, exist_ok=True)
    working_directory = output_root / f".{change_run_id}.{uuid4().hex}.tmp"
    try:
        working_directory.mkdir()
        score_path = working_directory / "change-score.tif"
        score_preview_path = working_directory / "change-score.png"
        mask_path = working_directory / "candidate-mask.tif"
        overlay_path = working_directory / "candidate-overlay.png"
        candidates_path = working_directory / "candidates.geojson"
        _write_score_raster(score_path, score, common_valid, grid, change_run_id)
        _write_mask_raster(mask_path, candidate_mask, common_valid, grid, change_run_id)
        _write_score_preview(score_preview_path, score, common_valid)
        _write_overlay(overlay_path, after_normalized, common_valid, candidate_mask)
        _write_json(candidates_path, feature_collection.model_dump(mode="json"))

        artifacts = (
            _artifact("change-score-raster", score_path, working_directory),
            _artifact("change-score-preview", score_preview_path, working_directory),
            _artifact("candidate-mask-raster", mask_path, working_directory),
            _artifact("candidate-overlay", overlay_path, working_directory),
            _artifact("candidate-geojson", candidates_path, working_directory),
        )
        manifest = ChangeRunManifest(
            change_run_id=change_run_id,
            source_processing_run_id=processing_manifest.run_id,
            source_processing_manifest_sha256=source_manifest_sha,
            source_quality_report_sha256=source_quality_sha,
            source_aligned_artifacts=cast(
                tuple[dict[str, object], dict[str, object]],
                tuple(artifact.model_dump(mode="json") for artifact in aligned_artifacts),
            ),
            software={
                "commit": commit,
                "echoatlas": __version__,
                "numpy": np.__version__,
                "scipy": scipy_version,
                "rasterio": rasterio.__version__,
                "gdal": rasterio.__gdal_version__,
                "pillow": pillow_version,
            },
            parameters=config,
            common_valid_pixel_count=common_valid_count,
            threshold_pixel_count=int(np.count_nonzero(threshold_mask)),
            cleaned_pixel_count=int(np.count_nonzero(cleaned_mask)),
            candidate_pixel_count=int(np.count_nonzero(candidate_mask)),
            candidate_count=candidate_count,
            artifacts=artifacts,
            warnings=warnings,
        )
        manifest_path = working_directory / "change-manifest.json"
        _write_json(manifest_path, manifest.model_dump(mode="json"))
        os.rename(working_directory, final_directory)
    except Exception:
        shutil.rmtree(working_directory, ignore_errors=True)
        raise

    return ChangeProcessingResult(
        change_run_id=change_run_id,
        output_directory=final_directory,
        manifest_path=final_directory / "change-manifest.json",
        candidates_path=final_directory / "candidates.geojson",
        artifacts=artifacts,
    )


def _load_source_contract(
    preview_run_directory: Path,
) -> tuple[ProcessingRunManifest, QualityReport]:
    manifest_path = preview_run_directory / "processing-manifest.json"
    quality_path = preview_run_directory / "quality-report.json"
    try:
        manifest = ProcessingRunManifest.model_validate_json(manifest_path.read_text())
        quality = QualityReport.model_validate_json(quality_path.read_text())
    except (OSError, ValidationError) as error:
        raise ChangeInputError(f"source preview contract is invalid: {error}") from error
    if manifest.run_id != preview_run_directory.name:
        raise ChangeInputError("source processing run ID does not match its directory")
    if quality.run_id != manifest.run_id or quality.selection_id != manifest.selection_id:
        raise ChangeInputError("source quality report does not match the processing manifest")
    expected_quality = manifest.quality_report
    if expected_quality.get("relative_path") != "quality-report.json":
        raise ChangeInputError("source quality report path is not canonical")
    if expected_quality.get("sha256") != _sha256_file(quality_path):
        raise ChangeInputError("source quality report checksum does not match")
    return manifest, quality


def _aligned_artifacts(
    manifest: ProcessingRunManifest,
) -> tuple[ArtifactRecord, ArtifactRecord]:
    records: dict[str, ArtifactRecord] = {}
    for artifact in manifest.artifacts:
        if artifact.kind == "aligned-raster":
            records[artifact.role] = artifact
    if set(records) != {"before", "after"}:
        raise ChangeInputError("source manifest must contain one aligned raster for each role")
    return records["before"], records["after"]


def _verified_artifact_path(root: Path, artifact: ArtifactRecord) -> Path:
    candidate = (root / artifact.relative_path).resolve()
    resolved_root = root.resolve()
    if not candidate.is_relative_to(resolved_root):
        raise ChangeInputError(
            f"source artifact path escapes the run directory: {artifact.artifact_id}"
        )
    if not candidate.is_file():
        raise ChangeInputError(f"source artifact is missing: {artifact.artifact_id}")
    if candidate.stat().st_size != artifact.size_bytes:
        raise ChangeInputError(f"source artifact size changed: {artifact.artifact_id}")
    if _sha256_file(candidate) != artifact.sha256:
        raise ChangeInputError(f"source artifact checksum changed: {artifact.artifact_id}")
    return candidate


def _read_aligned(
    role: Literal["before", "after"], path: Path, grid: GridRecord
) -> npt.NDArray[np.float32]:
    try:
        with rasterio.open(path) as source:
            if source.driver != "GTiff" or source.count != 1:
                raise ChangeInputError(f"{role} aligned artifact is not a single-band GeoTIFF")
            if source.crs is None or source.crs.to_string() != grid.crs:
                raise ChangeInputError(f"{role} aligned artifact CRS changed")
            if source.width != grid.width or source.height != grid.height:
                raise ChangeInputError(f"{role} aligned artifact dimensions changed")
            if not np.allclose(tuple(source.transform), grid.transform, rtol=0, atol=1e-9):
                raise ChangeInputError(f"{role} aligned artifact transform changed")
            if source.nodata is None or not math.isnan(source.nodata):
                raise ChangeInputError(f"{role} aligned artifact must use NaN nodata")
            values = source.read(1, out_dtype="float32")
    except rasterio.errors.RasterioIOError as error:
        raise ChangeInputError(f"{role} aligned artifact could not be opened: {error}") from error
    return cast(npt.NDArray[np.float32], values)


def _normalization_ranges(
    quality: QualityReport,
) -> dict[str, tuple[float, float]]:
    records: dict[str, RoleQualityRecord] = {record.role: record for record in quality.roles}
    if set(records) != {"before", "after"}:
        raise ChangeInputError("quality report normalization roles are incomplete")
    ranges = {
        role: (record.normalization_low, record.normalization_high)
        for role, record in records.items()
    }
    if any(
        not math.isfinite(low) or not math.isfinite(high) or low >= high
        for low, high in ranges.values()
    ):
        raise ChangeInputError("quality report contains an invalid normalization range")
    return ranges


def _normalize(
    values: npt.NDArray[np.float32], limits: tuple[float, float]
) -> npt.NDArray[np.float32]:
    low, high = limits
    normalized = np.clip((values - low) / (high - low), 0, 1)
    return cast(npt.NDArray[np.float32], normalized.astype(np.float32, copy=False))


def _symmetric_neighborhood_score(
    before: npt.NDArray[np.float32],
    after: npt.NDArray[np.float32],
    common_valid: npt.NDArray[np.bool_],
    tolerance: int,
) -> npt.NDArray[np.float32]:
    forward = _directed_neighborhood_difference(after, before, tolerance)
    reverse = _directed_neighborhood_difference(before, after, tolerance)
    score = np.maximum(forward, reverse)
    score[~common_valid] = np.nan
    return cast(npt.NDArray[np.float32], score)


def _directed_neighborhood_difference(
    center: npt.NDArray[np.float32],
    neighbor: npt.NDArray[np.float32],
    tolerance: int,
) -> npt.NDArray[np.float32]:
    height, width = center.shape
    minimum = np.full(center.shape, np.inf, dtype=np.float32)
    for row_offset in range(-tolerance, tolerance + 1):
        for column_offset in range(-tolerance, tolerance + 1):
            center_rows = slice(max(0, -row_offset), min(height, height - row_offset))
            neighbor_rows = slice(max(0, row_offset), min(height, height + row_offset))
            center_columns = slice(max(0, -column_offset), min(width, width - column_offset))
            neighbor_columns = slice(max(0, column_offset), min(width, width + column_offset))
            difference = np.abs(
                center[center_rows, center_columns] - neighbor[neighbor_rows, neighbor_columns]
            )
            target = minimum[center_rows, center_columns]
            np.minimum(target, difference, out=target, where=np.isfinite(difference))
    return minimum


def _clean_mask(
    threshold_mask: npt.NDArray[np.bool_], parameters: ChangeParameters
) -> npt.NDArray[np.bool_]:
    structure = np.ones(
        (parameters.morphology_kernel_size, parameters.morphology_kernel_size), dtype=np.bool_
    )
    cleaned = threshold_mask
    if parameters.opening_iterations:
        cleaned = ndimage.binary_opening(
            cleaned, structure=structure, iterations=parameters.opening_iterations
        )
    if parameters.closing_iterations:
        cleaned = ndimage.binary_closing(
            cleaned, structure=structure, iterations=parameters.closing_iterations
        )
    return cleaned


def _retain_candidates(
    cleaned_mask: npt.NDArray[np.bool_], parameters: ChangeParameters
) -> tuple[npt.NDArray[np.bool_], npt.NDArray[np.int32], int]:
    structure = ndimage.generate_binary_structure(2, 2 if parameters.connectivity == 8 else 1)
    initial_labels, count = ndimage.label(cleaned_mask, structure=structure)
    counts = np.bincount(initial_labels.ravel())
    keep = np.zeros(count + 1, dtype=np.bool_)
    if count:
        keep[1:] = counts[1:] >= parameters.minimum_component_pixels
    retained = keep[initial_labels]
    labels, final_count = ndimage.label(retained, structure=structure, output=np.int32)
    return (
        cast(npt.NDArray[np.bool_], retained),
        cast(npt.NDArray[np.int32], labels),
        int(final_count),
    )


def _candidate_features(
    labels: npt.NDArray[np.int32],
    score: npt.NDArray[np.float32],
    signed_delta: npt.NDArray[np.float32],
    grid: GridRecord,
    change_run_id: str,
    source_processing_run_id: str,
) -> tuple[CandidateFeature, ...]:
    count = int(labels.max())
    if count == 0:
        return ()
    transform = Affine(*grid.transform[:6])
    geometries = {
        int(value): cast(dict[str, object], geometry)
        for geometry, value in shapes(
            labels,
            mask=labels > 0,
            connectivity=8,
            transform=transform,
        )
    }
    slices = ndimage.find_objects(labels)
    features: list[CandidateFeature] = []
    for label_value in range(1, count + 1):
        region_slice = slices[label_value - 1]
        geometry = geometries.get(label_value)
        if region_slice is None or geometry is None:
            raise ChangeProcessingError(f"candidate label {label_value} could not be vectorized")
        local_labels = labels[region_slice]
        local_mask = local_labels == label_value
        candidate_scores = score[region_slice][local_mask]
        candidate_delta = signed_delta[region_slice][local_mask]
        row_slice, column_slice = region_slice
        projected_bbox = array_bounds(
            row_slice.stop - row_slice.start,
            column_slice.stop - column_slice.start,
            transform * Affine.translation(column_slice.start, row_slice.start),
        )
        wgs84_geometry = cast(
            dict[str, object], transform_geom(grid.crs, "EPSG:4326", geometry, precision=9)
        )
        wgs84_bbox = _geometry_bounds(wgs84_geometry)
        candidate_id = f"{change_run_id}-candidate-{label_value:04d}"
        features.append(
            CandidateFeature(
                id=candidate_id,
                geometry=wgs84_geometry,
                properties=CandidateProperties(
                    candidate_id=candidate_id,
                    change_run_id=change_run_id,
                    source_processing_run_id=source_processing_run_id,
                    measurements=CandidateMeasurements(
                        pixel_count=int(candidate_scores.size),
                        area_square_meters=float(candidate_scores.size * grid.resolution**2),
                        projected_bbox=cast(
                            tuple[float, float, float, float],
                            tuple(float(value) for value in projected_bbox),
                        ),
                        wgs84_bbox=wgs84_bbox,
                    ),
                    score_components=CandidateScoreComponents(
                        mean_change_score=float(candidate_scores.mean()),
                        p95_change_score=float(np.percentile(candidate_scores, 95)),
                        max_change_score=float(candidate_scores.max()),
                        mean_signed_normalized_delta=float(candidate_delta.mean()),
                        brightening_pixel_fraction=float(np.mean(candidate_delta > 0)),
                        darkening_pixel_fraction=float(np.mean(candidate_delta < 0)),
                    ),
                    warnings=_candidate_warnings(),
                ),
            )
        )
    return tuple(features)


def _geometry_bounds(geometry: dict[str, object]) -> tuple[float, float, float, float]:
    coordinates = geometry.get("coordinates")
    points: list[tuple[float, float]] = []

    def collect(value: object) -> None:
        if isinstance(value, (list, tuple)):
            if len(value) >= 2 and all(isinstance(item, (int, float)) for item in value[:2]):
                points.append((float(value[0]), float(value[1])))
            else:
                for item in value:
                    collect(item)

    collect(coordinates)
    if not points:
        raise ChangeProcessingError("candidate geometry contains no coordinates")
    x_values, y_values = zip(*points, strict=True)
    return min(x_values), min(y_values), max(x_values), max(y_values)


def _write_score_raster(
    path: Path,
    score: npt.NDArray[np.float32],
    valid: npt.NDArray[np.bool_],
    grid: GridRecord,
    change_run_id: str,
) -> None:
    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        width=grid.width,
        height=grid.height,
        count=1,
        dtype="float32",
        crs=grid.crs,
        transform=Affine(*grid.transform[:6]),
        nodata=np.nan,
        compress="deflate",
        predictor=3,
        tiled=True,
        blockxsize=256,
        blockysize=256,
    ) as destination:
        destination.write(score, 1)
        destination.write_mask(valid.astype(np.uint8) * 255)
        destination.update_tags(
            ECHOATLAS_CHANGE_RUN_ID=change_run_id,
            ECHOATLAS_PRODUCT="engineering-change-score",
        )


def _write_mask_raster(
    path: Path,
    candidate_mask: npt.NDArray[np.bool_],
    valid: npt.NDArray[np.bool_],
    grid: GridRecord,
    change_run_id: str,
) -> None:
    values = candidate_mask.astype(np.uint8)
    values[~valid] = 255
    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        width=grid.width,
        height=grid.height,
        count=1,
        dtype="uint8",
        crs=grid.crs,
        transform=Affine(*grid.transform[:6]),
        nodata=255,
        compress="deflate",
        tiled=True,
        blockxsize=256,
        blockysize=256,
    ) as destination:
        destination.write(values, 1)
        destination.write_mask(valid.astype(np.uint8) * 255)
        destination.update_tags(
            ECHOATLAS_CHANGE_RUN_ID=change_run_id,
            ECHOATLAS_PRODUCT="candidate-mask",
        )


def _write_score_preview(
    path: Path, score: npt.NDArray[np.float32], valid: npt.NDArray[np.bool_]
) -> None:
    preview = np.zeros(score.shape, dtype=np.uint8)
    preview[valid] = np.rint(np.clip(score[valid], 0, 1) * 254 + 1).astype(np.uint8)
    Image.fromarray(preview).save(path, format="PNG", compress_level=9, optimize=False)


def _write_overlay(
    path: Path,
    after_normalized: npt.NDArray[np.float32],
    valid: npt.NDArray[np.bool_],
    candidate_mask: npt.NDArray[np.bool_],
) -> None:
    grayscale = np.zeros(after_normalized.shape, dtype=np.uint8)
    grayscale[valid] = np.rint(after_normalized[valid] * 255).astype(np.uint8)
    overlay = np.repeat(grayscale[:, :, np.newaxis], 3, axis=2)
    overlay[candidate_mask, 0] = 255
    overlay[candidate_mask, 1] = np.rint(grayscale[candidate_mask] * 0.35).astype(np.uint8)
    overlay[candidate_mask, 2] = np.rint(grayscale[candidate_mask] * 0.35).astype(np.uint8)
    Image.fromarray(overlay).save(path, format="PNG", compress_level=9, optimize=False)


def _artifact(
    kind: Literal[
        "change-score-raster",
        "change-score-preview",
        "candidate-mask-raster",
        "candidate-overlay",
        "candidate-geojson",
    ],
    path: Path,
    output_directory: Path,
) -> ChangeArtifactRecord:
    media_type = {
        "change-score-raster": "image/tiff",
        "change-score-preview": "image/png",
        "candidate-mask-raster": "image/tiff",
        "candidate-overlay": "image/png",
        "candidate-geojson": "application/geo+json",
    }[kind]
    return ChangeArtifactRecord(
        artifact_id=kind,
        kind=kind,
        relative_path=path.relative_to(output_directory).as_posix(),
        media_type=media_type,
        sha256=_sha256_file(path),
        size_bytes=path.stat().st_size,
    )


def _change_run_id(
    manifest: ProcessingRunManifest,
    source_manifest_sha: str,
    source_quality_sha: str,
    aligned_artifacts: tuple[ArtifactRecord, ArtifactRecord],
    parameters: ChangeParameters,
    software_commit: str,
) -> str:
    identity = {
        "source_processing_run_id": manifest.run_id,
        "source_processing_manifest_sha256": source_manifest_sha,
        "source_quality_report_sha256": source_quality_sha,
        "source_aligned_artifacts": {
            artifact.role: artifact.sha256 for artifact in aligned_artifacts
        },
        "parameters": parameters.model_dump(mode="json"),
        "software_commit": software_commit,
    }
    digest = hashlib.sha256(
        json.dumps(identity, separators=(",", ":"), sort_keys=True).encode()
    ).hexdigest()
    return f"change-{digest[:20]}"


def _warnings(parameters: ChangeParameters) -> tuple[str, ...]:
    return (
        "Outputs are machine-generated engineering candidates pending human review.",
        "The score uses independently stretched intensity values and is not calibrated "
        "backscatter or confidence.",
        f"A {parameters.registration_tolerance_pixels}-pixel neighborhood tolerance reduces "
        "simple registration-edge responses but cannot remove all geometry effects.",
        "Speckle, moisture, slope, layover, shadow, resampling, and acquisition geometry can "
        "produce candidate responses.",
        "Candidate geometry and measurements describe the thresholded raster response only; "
        "they do not establish cause, identity, impact, or operational status.",
    )


def _candidate_warnings() -> tuple[str, ...]:
    return (
        "Machine-generated engineering candidate pending human review.",
        "May reflect speckle, surface conditions, terrain geometry, resampling, or residual "
        "registration effects.",
        "Independent display normalization prevents calibrated magnitude interpretation.",
    )


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.write_text(f"{json.dumps(payload, indent=2, sort_keys=True)}\n", encoding="utf-8")


def _sha256_file(path: Path) -> str:
    checksum = hashlib.sha256()
    try:
        with path.open("rb") as handle:
            while payload := handle.read(1024 * 1024):
                checksum.update(payload)
    except OSError as error:
        raise ChangeInputError(f"required source file could not be read: {path}") from error
    return checksum.hexdigest()
