"""Validated parameters and records for baseline change candidates."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ChangeParameters(BaseModel):
    model_config = ConfigDict(frozen=True)

    score_method: Literal["symmetric_neighborhood_normalized_absolute_difference"] = (
        "symmetric_neighborhood_normalized_absolute_difference"
    )
    score_threshold: float = Field(default=0.5, gt=0, le=1)
    registration_tolerance_pixels: int = Field(default=1, ge=0, le=3)
    morphology_kernel_size: Literal[3] = 3
    opening_iterations: int = Field(default=1, ge=0, le=3)
    closing_iterations: int = Field(default=1, ge=0, le=3)
    connectivity: Literal[4, 8] = 8
    minimum_component_pixels: int = Field(default=512, ge=1)
    maximum_candidate_count: int = Field(default=500, ge=1, le=10_000)


class CandidateMeasurements(BaseModel):
    model_config = ConfigDict(frozen=True)

    pixel_count: int = Field(gt=0)
    area_square_meters: float = Field(gt=0)
    projected_bbox: tuple[float, float, float, float]
    wgs84_bbox: tuple[float, float, float, float]


class CandidateScoreComponents(BaseModel):
    model_config = ConfigDict(frozen=True)

    mean_change_score: float = Field(ge=0, le=1)
    p95_change_score: float = Field(ge=0, le=1)
    max_change_score: float = Field(ge=0, le=1)
    mean_signed_normalized_delta: float = Field(ge=-1, le=1)
    brightening_pixel_fraction: float = Field(ge=0, le=1)
    darkening_pixel_fraction: float = Field(ge=0, le=1)


class CandidateProperties(BaseModel):
    model_config = ConfigDict(frozen=True)

    candidate_id: str
    display_label: Literal["Change candidate"] = "Change candidate"
    status: Literal["pending"] = "pending"
    change_run_id: str
    source_processing_run_id: str
    measurements: CandidateMeasurements
    score_components: CandidateScoreComponents
    warnings: tuple[str, ...]


class CandidateFeature(BaseModel):
    model_config = ConfigDict(frozen=True)

    type: Literal["Feature"] = "Feature"
    id: str
    geometry: dict[str, object]
    properties: CandidateProperties


class CandidateFeatureCollection(BaseModel):
    model_config = ConfigDict(frozen=True)

    type: Literal["FeatureCollection"] = "FeatureCollection"
    change_run_id: str
    source_processing_run_id: str
    display_label: Literal["Change candidates"] = "Change candidates"
    warnings: tuple[str, ...]
    features: tuple[CandidateFeature, ...]


class ChangeArtifactRecord(BaseModel):
    model_config = ConfigDict(frozen=True)

    artifact_id: str
    kind: Literal[
        "change-score-raster",
        "change-score-preview",
        "candidate-mask-raster",
        "candidate-overlay",
        "candidate-geojson",
    ]
    relative_path: str
    media_type: str
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    size_bytes: int = Field(gt=0)


class ChangeRunManifest(BaseModel):
    model_config = ConfigDict(frozen=True)

    change_manifest_version: Literal["1.0.0"] = "1.0.0"
    change_run_id: str
    status: Literal["succeeded"] = "succeeded"
    display_label: Literal["Change candidates"] = "Change candidates"
    source_processing_run_id: str
    source_processing_manifest_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    source_quality_report_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    source_aligned_artifacts: tuple[dict[str, object], dict[str, object]]
    software: dict[str, str]
    parameters: ChangeParameters
    common_valid_pixel_count: int = Field(gt=0)
    threshold_pixel_count: int = Field(ge=0)
    cleaned_pixel_count: int = Field(ge=0)
    candidate_pixel_count: int = Field(ge=0)
    candidate_count: int = Field(ge=0)
    artifacts: tuple[ChangeArtifactRecord, ...]
    warnings: tuple[str, ...]


class ChangeProcessingResult(BaseModel):
    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)

    change_run_id: str
    output_directory: Path
    manifest_path: Path
    candidates_path: Path
    artifacts: tuple[ChangeArtifactRecord, ...]
