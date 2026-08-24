"""Validated subset of the approved selection manifest used for acquisition."""

from __future__ import annotations

import base64
import hashlib
import json
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Literal
from urllib.parse import unquote, urlparse

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator


class ManifestValidationError(ValueError):
    """The source selection manifest is missing or unsafe."""


class IntegrityChecksum(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    algorithm: Literal["CRC64NVME"]
    encoding: Literal["base64"]
    value: str
    type: Literal["FULL_OBJECT"]

    @field_validator("value")
    @classmethod
    def validate_checksum_value(cls, value: str) -> str:
        try:
            decoded = base64.b64decode(value, validate=True)
        except ValueError as error:
            raise ValueError("checksum value must be valid base64") from error
        if len(decoded) != 8:
            raise ValueError("CRC64NVME checksum must encode exactly 8 bytes")
        return value


class PinnedObject(BaseModel):
    model_config = ConfigDict(frozen=True, extra="ignore")

    key: str
    url: str
    size_bytes: int = Field(gt=0)
    etag: str
    checksum: IntegrityChecksum

    @model_validator(mode="after")
    def validate_object_identity(self) -> PinnedObject:
        url_path = PurePosixPath(unquote(urlparse(self.url).path))
        key_path = PurePosixPath(self.key)
        if key_path.is_absolute():
            raise ValueError("object key must be relative")
        if url_path.name != key_path.name:
            raise ValueError("object URL and key must name the same file")
        if url_path.suffix.lower() not in {".tif", ".tiff"}:
            raise ValueError("pinned acquisition object must be a TIFF")
        if any(part in {"", ".", ".."} for part in key_path.parts):
            raise ValueError("object key contains an unsafe path segment")
        return self


class PinnedAcquisition(BaseModel):
    model_config = ConfigDict(frozen=True, extra="ignore")

    item_id: str = Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
    acquired_at: datetime
    product_type: Literal["GEC"]
    polarizations: tuple[str, ...]
    object: PinnedObject


class SourceLicense(BaseModel):
    model_config = ConfigDict(frozen=True, extra="ignore")

    spdx: str = Field(min_length=1)
    provider: str = Field(min_length=1)


class ProcessingAoi(BaseModel):
    model_config = ConfigDict(frozen=True, extra="ignore")

    id: str = Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
    bbox: tuple[float, float, float, float]
    geometry: dict[str, object]
    geometry_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    boundary: str = Field(min_length=1)

    @model_validator(mode="after")
    def validate_geometry_contract(self) -> ProcessingAoi:
        west, south, east, north = self.bbox
        if not (-180 <= west < east <= 180 and -90 <= south < north <= 90):
            raise ValueError("processing AOI bbox must be an ordered WGS84 extent")
        if self.geometry.get("type") != "Polygon":
            raise ValueError("processing AOI geometry must be a Polygon")
        coordinates = self.geometry.get("coordinates")
        if not isinstance(coordinates, list) or not coordinates:
            raise ValueError("processing AOI geometry requires coordinates")
        canonical = json.dumps(self.geometry, separators=(",", ":"), sort_keys=True).encode()
        if hashlib.sha256(canonical).hexdigest() != self.geometry_sha256:
            raise ValueError("processing AOI geometry checksum does not match")
        return self


class SelectionManifest(BaseModel):
    model_config = ConfigDict(frozen=True, extra="ignore")

    manifest_version: Literal["1.0.0"]
    selection_id: str = Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
    status: Literal["approved"]
    accessed_at: datetime
    license: SourceLicense
    processing_aoi: ProcessingAoi
    acquisitions: dict[str, PinnedAcquisition]
    interpretation_limits: tuple[str, ...] = ()
    sensitivity_controls: tuple[str, ...] = ()

    @field_validator("acquisitions")
    @classmethod
    def validate_acquisition_roles(
        cls, value: dict[str, PinnedAcquisition]
    ) -> dict[str, PinnedAcquisition]:
        if set(value) != {"before", "after"}:
            raise ValueError("approved manifest must contain exactly before and after acquisitions")
        return value


def load_selection_manifest(path: Path) -> SelectionManifest:
    try:
        return parse_selection_manifest(path.read_bytes())
    except OSError as error:
        raise ManifestValidationError(f"selection manifest could not be read: {error}") from error


def parse_selection_manifest(payload: bytes) -> SelectionManifest:
    try:
        document = json.loads(payload)
        if not isinstance(document, dict):
            raise ManifestValidationError("selection manifest root must be an object")
        return SelectionManifest.model_validate(document)
    except json.JSONDecodeError as error:
        raise ManifestValidationError(f"selection manifest is invalid JSON: {error}") from error
    except ValidationError as error:
        raise ManifestValidationError(f"selection manifest failed validation: {error}") from error
