"""Validated processing parameters and output records."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ProcessingParameters(BaseModel):
    model_config = ConfigDict(frozen=True)

    target_crs: str = Field(default="EPSG:32612", min_length=1)
    target_resolution: float = Field(default=1.0, gt=0)
    resampling: Literal["bilinear"] = "bilinear"
    normalization: Literal["independent_percentile_stretch"] = "independent_percentile_stretch"
    lower_percentile: float = Field(default=2.0, ge=0, le=100)
    upper_percentile: float = Field(default=98.0, ge=0, le=100)
    filter: Literal["none"] = "none"
    thumbnail_max_size: int = Field(default=512, ge=64, le=2048)
    min_valid_fraction: float = Field(default=0.99, gt=0, le=1)

    @model_validator(mode="after")
    def validate_percentiles(self) -> ProcessingParameters:
        if self.lower_percentile >= self.upper_percentile:
            raise ValueError("lower percentile must be less than upper percentile")
        return self


class GridRecord(BaseModel):
    model_config = ConfigDict(frozen=True)

    crs: str
    resolution: float
    width: int = Field(gt=0)
    height: int = Field(gt=0)
    bounds: tuple[float, float, float, float]
    transform: tuple[float, float, float, float, float, float, float, float, float]
    aoi_pixel_count: int = Field(gt=0)


class RasterSourceRecord(BaseModel):
    model_config = ConfigDict(frozen=True)

    role: Literal["before", "after"]
    item_id: str
    file_name: str
    driver: str
    crs: str
    dtype: str
    width: int = Field(gt=0)
    height: int = Field(gt=0)
    count: Literal[1]
    transform: tuple[float, float, float, float, float, float, float, float, float]
    resolution: tuple[float, float]
    bounds: tuple[float, float, float, float]
    wgs84_bounds: tuple[float, float, float, float]
    nodata: float
    color_interpretation: str
    rotated_transform: bool


class RoleQualityRecord(BaseModel):
    model_config = ConfigDict(frozen=True)

    role: Literal["before", "after"]
    valid_pixel_count: int = Field(gt=0)
    aoi_pixel_count: int = Field(gt=0)
    valid_fraction: float = Field(ge=0, le=1)
    value_min: float
    value_max: float
    normalization_low: float
    normalization_high: float
    output_nodata: Literal["NaN"] = "NaN"


class ArtifactRecord(BaseModel):
    model_config = ConfigDict(frozen=True)

    artifact_id: str
    role: Literal["before", "after"]
    kind: Literal["aligned-raster", "preview", "thumbnail"]
    relative_path: str
    media_type: str
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    size_bytes: int = Field(gt=0)
    width: int = Field(gt=0)
    height: int = Field(gt=0)


class QualityReport(BaseModel):
    model_config = ConfigDict(frozen=True)

    quality_report_version: Literal["1.0.0"] = "1.0.0"
    run_id: str
    selection_id: str
    grid: GridRecord
    sources: tuple[RasterSourceRecord, RasterSourceRecord]
    roles: tuple[RoleQualityRecord, RoleQualityRecord]
    common_valid_pixel_count: int = Field(gt=0)
    common_valid_fraction: float = Field(ge=0, le=1)
    warnings: tuple[str, ...]


class ProcessingRunManifest(BaseModel):
    model_config = ConfigDict(frozen=True)

    processing_manifest_version: Literal["1.0.0"] = "1.0.0"
    run_id: str
    status: Literal["succeeded"] = "succeeded"
    selection_id: str
    processing_aoi_id: str
    processing_aoi_geometry_sha256: str
    source_license: dict[str, str]
    inputs: tuple[dict[str, object], dict[str, object]]
    parameters: ProcessingParameters
    grid: GridRecord
    software: dict[str, str]
    artifacts: tuple[ArtifactRecord, ...]
    quality_report: dict[str, object]
    interpretation_limits: tuple[str, ...]
    sensitivity_controls: tuple[str, ...]


class ProcessingResult(BaseModel):
    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)

    run_id: str
    output_directory: Path
    manifest_path: Path
    quality_report_path: Path
    artifacts: tuple[ArtifactRecord, ...]
