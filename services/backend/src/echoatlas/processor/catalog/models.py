"""Validated provider-neutral catalog records."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class CatalogWarning(BaseModel):
    """A recoverable catalog irregularity that remains visible to operators."""

    model_config = ConfigDict(frozen=True)

    code: str
    source_url: str
    message: str


class CatalogAsset(BaseModel):
    """A declared STAC asset or an object found through the public bucket."""

    model_config = ConfigDict(frozen=True)

    name: str
    href: str | None
    origin: Literal["stac", "public-s3"]
    media_type: str | None = None
    title: str | None = None
    roles: tuple[str, ...] = ()
    object_key: str | None = None
    size_bytes: int | None = Field(default=None, ge=0)
    etag: str | None = None


class Acquisition(BaseModel):
    """Normalized acquisition metadata consumed outside provider adapters."""

    model_config = ConfigDict(frozen=True)

    item_id: str
    acquired_at: datetime
    bbox: tuple[float, float, float, float]
    geometry: dict[str, Any]
    product_type: str | None
    polarizations: tuple[str, ...]
    resolution_range_m: float | None = Field(default=None, gt=0)
    resolution_azimuth_m: float | None = Field(default=None, gt=0)
    platform: str | None
    observation_direction: str | None
    orbit_state: str | None
    incidence_angle_deg: float | None
    grazing_angle_deg: float | None
    license: str
    source_url: str
    provider_task_id: str | None
    assets: tuple[CatalogAsset, ...]
    source_document: dict[str, Any]

    @field_validator("bbox")
    @classmethod
    def validate_bbox(
        cls, value: tuple[float, float, float, float]
    ) -> tuple[float, float, float, float]:
        west, south, east, north = value
        if not (-180 <= west < east <= 180 and -90 <= south < north <= 90):
            raise ValueError("bbox must be an ordered WGS84 extent")
        return value

    @field_validator("geometry")
    @classmethod
    def validate_geometry(cls, value: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(value.get("type"), str) or not value.get("coordinates"):
            raise ValueError("geometry requires a type and non-empty coordinates")
        return value


class CatalogCoverage(BaseModel):
    model_config = ConfigDict(frozen=True)

    root_url: str
    catalogs_visited: int = Field(ge=0)
    item_links_seen: int = Field(ge=0)
    items_indexed: int = Field(ge=0)
    items_skipped: int = Field(ge=0)
    catalog_limit_reached: bool
    item_limit_reached: bool


class TraversalResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    acquisitions: tuple[Acquisition, ...]
    warnings: tuple[CatalogWarning, ...]
    coverage: CatalogCoverage


class CandidateAoi(BaseModel):
    model_config = ConfigDict(frozen=True)

    grid_key: str
    bbox: tuple[float, float, float, float]
    acquisition_count: int = Field(ge=2)
    first_acquired_at: datetime
    last_acquired_at: datetime
    item_ids: tuple[str, ...]
    products: tuple[str, ...]
    polarizations: tuple[str, ...]

    @model_validator(mode="after")
    def validate_time_span(self) -> CandidateAoi:
        if self.first_acquired_at > self.last_acquired_at:
            raise ValueError("candidate AOI time span is reversed")
        return self


class FeasibilityReport(BaseModel):
    model_config = ConfigDict(frozen=True)

    accessed_at: datetime
    catalog_coverage: CatalogCoverage
    acquisition_count: int = Field(ge=0)
    resolved_object_count: int = Field(ge=0)
    resolved_object_bytes_declared: int = Field(ge=0)
    s3_listing_pages: int = Field(ge=0)
    warning_counts: dict[str, int]
    warning_samples: tuple[CatalogWarning, ...]
    candidate_time_series_aois: tuple[CandidateAoi, ...]
    metadata_only: Literal[True] = True
    large_imagery_downloaded: Literal[False] = False


class CatalogIndex(BaseModel):
    model_config = ConfigDict(frozen=True)

    report: FeasibilityReport
    acquisitions: tuple[Acquisition, ...]
