"""Versioned provider-neutral contracts for bounded imagery catalog search."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

CATALOG_SEARCH_CONTRACT_VERSION: Literal["1.0.0"] = "1.0.0"
ProviderId = Literal["umbra", "sentinel-1"]
BBox = tuple[float, float, float, float]


class GeoJsonPolygon(BaseModel):
    """A bounded WGS84 polygon accepted from the future Explore client."""

    model_config = ConfigDict(frozen=True)

    type: Literal["Polygon"] = "Polygon"
    coordinates: tuple[tuple[tuple[float, float], ...], ...]

    @field_validator("coordinates")
    @classmethod
    def validate_coordinates(
        cls, value: tuple[tuple[tuple[float, float], ...], ...]
    ) -> tuple[tuple[tuple[float, float], ...], ...]:
        if not value or len(value) > 5:
            raise ValueError("AOI polygon requires one to five rings")
        point_count = 0
        for ring in value:
            if len(ring) < 4 or ring[0] != ring[-1]:
                raise ValueError("AOI polygon rings must be closed and contain four points")
            point_count += len(ring)
            for longitude, latitude in ring:
                if not (-180 <= longitude <= 180 and -90 <= latitude <= 90):
                    raise ValueError("AOI polygon coordinates must be valid WGS84 positions")
        if point_count > 100:
            raise ValueError("AOI polygon exceeds the 100-point limit")
        return value


class SearchAoi(BaseModel):
    """A small AOI with both its exact polygon and query envelope."""

    model_config = ConfigDict(frozen=True)

    bbox: BBox
    geometry: GeoJsonPolygon

    @model_validator(mode="after")
    def validate_bounds(self) -> SearchAoi:
        west, south, east, north = self.bbox
        if not (-180 <= west < east <= 180 and -90 <= south < north <= 90):
            raise ValueError("AOI bbox must be an ordered WGS84 extent")
        if east - west > 5 or north - south > 5 or (east - west) * (north - south) > 25:
            raise ValueError("AOI must fit within a five-degree by five-degree envelope")
        for ring in self.geometry.coordinates:
            for longitude, latitude in ring:
                if not (west <= longitude <= east and south <= latitude <= north):
                    raise ValueError("AOI polygon must remain inside its declared bbox")
        return self


class CatalogSearchRequest(BaseModel):
    """The stable request boundary consumed by every provider adapter."""

    model_config = ConfigDict(frozen=True)

    contract_version: Literal["1.0.0"] = CATALOG_SEARCH_CONTRACT_VERSION
    aoi: SearchAoi
    start_at: datetime
    end_at: datetime
    providers: tuple[ProviderId, ...] = ("umbra", "sentinel-1")
    product_types: tuple[str, ...] = ()
    polarizations: tuple[str, ...] = ()
    max_resolution_m: float | None = Field(default=None, gt=0, le=10_000)
    page_size: int = Field(default=25, ge=1, le=50)
    cursor: str | None = Field(default=None, max_length=512)

    @field_validator("start_at", "end_at")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("catalog search timestamps must include a timezone")
        return value

    @field_validator("providers")
    @classmethod
    def validate_providers(cls, value: tuple[ProviderId, ...]) -> tuple[ProviderId, ...]:
        if not value or len(value) != len(set(value)):
            raise ValueError("providers must be a non-empty unique list")
        return value

    @field_validator("product_types")
    @classmethod
    def validate_products(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        normalized = tuple(item.strip() for item in value if item.strip())
        if len(normalized) != len(value) or len(normalized) > 10:
            raise ValueError("product_types must contain at most ten non-empty values")
        return normalized

    @field_validator("polarizations")
    @classmethod
    def validate_polarizations(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        normalized = tuple(item.strip().upper() for item in value if item.strip())
        if len(normalized) != len(value) or len(normalized) > 4:
            raise ValueError("polarizations must contain at most four non-empty values")
        return normalized

    @model_validator(mode="after")
    def validate_time_range(self) -> CatalogSearchRequest:
        if self.start_at >= self.end_at:
            raise ValueError("catalog search start_at must precede end_at")
        if self.end_at - self.start_at > timedelta(days=366):
            raise ValueError("catalog search time range cannot exceed 366 days")
        return self


class CatalogLicense(BaseModel):
    model_config = ConfigDict(frozen=True)

    label: str
    url: str | None = None


class CatalogSourceIdentity(BaseModel):
    model_config = ConfigDict(frozen=True)

    item_id: str
    collection: str
    href: str


class CatalogSearchItem(BaseModel):
    """Normalized metadata only; raw provider payloads never cross this boundary."""

    model_config = ConfigDict(frozen=True)

    provider: ProviderId
    acquired_at: datetime
    bbox: BBox
    footprint: GeoJsonPolygon
    product_type: str | None
    polarizations: tuple[str, ...]
    resolution_range_m: float | None = Field(default=None, gt=0)
    resolution_azimuth_m: float | None = Field(default=None, gt=0)
    platform: str | None
    observation_direction: str | None
    orbit_state: str | None
    incidence_angle_deg: float | None
    license: CatalogLicense
    source: CatalogSourceIdentity


class CatalogSearchWarning(BaseModel):
    model_config = ConfigDict(frozen=True)

    code: str
    message: str
    provider: ProviderId | None = None
    retryable: bool = False


class ProviderSearchReport(BaseModel):
    model_config = ConfigDict(frozen=True)

    provider: ProviderId
    status: Literal["complete", "partial", "failed"]
    result_count: int = Field(ge=0)
    has_more: bool
    warning_count: int = Field(ge=0)


class ProviderSearchPage(BaseModel):
    """Internal normalized return type implemented by provider adapters."""

    model_config = ConfigDict(frozen=True)

    items: tuple[CatalogSearchItem, ...]
    warnings: tuple[CatalogSearchWarning, ...] = ()
    has_more: bool = False


class CatalogSearchResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    contract_version: Literal["1.0.0"] = CATALOG_SEARCH_CONTRACT_VERSION
    query_id: str
    status: Literal["complete", "empty", "partial"]
    generated_at: datetime
    cache: Literal["hit", "miss"]
    results: tuple[CatalogSearchItem, ...]
    providers: tuple[ProviderSearchReport, ...]
    warnings: tuple[CatalogSearchWarning, ...]
    next_cursor: str | None
    sampled_result_count: int = Field(ge=0)


def bbox_intersects(left: BBox, right: BBox) -> bool:
    """Return whether two non-antimeridian WGS84 envelopes overlap."""

    return not (
        left[2] < right[0] or left[0] > right[2] or left[3] < right[1] or left[1] > right[3]
    )
