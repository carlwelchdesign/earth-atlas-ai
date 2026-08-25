"""Validate candidate-hidden labeling exports without promoting provisional labels."""

from __future__ import annotations

import hashlib
from datetime import datetime
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from echoatlas.evaluation.review import LabelingPacket, LabelingTile

Point = tuple[float, float]
TileDecision = Literal["", "regions-drawn", "reviewed-no-reference-region", "unresolved"]

MAX_LABELING_FILE_BYTES = 10 * 1024 * 1024
POINT_TOLERANCE = 0.001


class LabelingValidationError(ValueError):
    """Raised when a labeling packet or export violates its deterministic contract."""


class LabelingReviewer(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=200)
    role: str = Field(min_length=1, max_length=200)


class LabelingCoverage(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    status: Literal["partial", "complete"]
    reviewed_tiles: int = Field(ge=0, le=4096)
    total_tiles: int = Field(gt=0, le=4096)


class LabelingTileReview(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    tile_id: str = Field(pattern=r"^T-[0-9]{3,4}$")
    decision: TileDecision
    note: str = Field(max_length=1000)
    saved_at: datetime | None

    @model_validator(mode="after")
    def require_timestamp_for_saved_decision(self) -> LabelingTileReview:
        if self.decision and self.saved_at is None:
            raise ValueError("reviewed tiles require saved_at")
        if not self.decision and self.saved_at is not None:
            raise ValueError("pending tiles cannot have saved_at")
        return self


class LabelingPolygon(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    type: Literal["Polygon"]
    coordinates: tuple[tuple[Point, ...], ...] = Field(min_length=1, max_length=1)


class ProvisionalReferenceRegion(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    region_id: str = Field(pattern=r"^T-[0-9]{3,4}-R-[0-9]{2,4}$")
    tile_id: str = Field(pattern=r"^T-[0-9]{3,4}$")
    points: tuple[Point, ...] = Field(min_length=3, max_length=10_000)
    created_at: datetime | None
    review_status: Literal["provisional-candidate-hidden"]
    geometry_crs: str = Field(min_length=1, max_length=100)
    geometry: LabelingPolygon
    projected_points: tuple[Point, ...] = Field(min_length=3, max_length=10_000)
    pixel_points: tuple[Point, ...] = Field(min_length=3, max_length=10_000)
    boundary: str = Field(min_length=1, max_length=1000)


class IncompleteLabelingDraft(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    tile_id: str = Field(pattern=r"^T-[0-9]{3,4}$")
    points: tuple[Point, ...] = Field(min_length=1, max_length=10_000)
    updated_at: datetime | None


class LabelingExport(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    labeling_export_version: Literal["1.0.0"] = "1.0.0"
    packet_id: str = Field(pattern=r"^labeling-[a-f0-9]{20}$")
    processing_run_id: str = Field(min_length=1, max_length=200)
    source_processing_manifest_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    reviewer: LabelingReviewer
    exported_at: datetime
    coverage: LabelingCoverage
    tile_reviews: tuple[LabelingTileReview, ...] = Field(min_length=1, max_length=4096)
    reference_regions: tuple[ProvisionalReferenceRegion, ...] = Field(max_length=10_000)
    incomplete_drafts: tuple[IncompleteLabelingDraft, ...] = Field(max_length=4096)
    boundary: str = Field(min_length=1, max_length=2000)


class LabelingReadinessReport(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    labeling_readiness_report_version: Literal["1.0.0"] = "1.0.0"
    packet_id: str
    processing_run_id: str
    source_packet_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    source_export_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    ready_for_adjudication: bool
    ready_for_evaluation: Literal[False] = False
    reviewed_tile_count: int = Field(ge=0)
    total_tile_count: int = Field(gt=0)
    provisional_region_count: int = Field(ge=0)
    incomplete_draft_count: int = Field(ge=0)
    blocking_issues: tuple[str, ...]
    required_next_actions: tuple[str, ...]
    limitations: tuple[str, ...]


def validate_labeling_export(
    packet_path: Path,
    export_path: Path,
) -> LabelingReadinessReport:
    """Validate labeling provenance and geometry, then report adjudication readiness."""

    packet = _read_model(packet_path, LabelingPacket, "labeling packet")
    labeling_export = _read_model(export_path, LabelingExport, "labeling export")
    _validate_packet(packet)
    _validate_identity(packet, labeling_export)
    tile_by_id = {tile.tile_id: tile for tile in packet.tiles}
    reviews = _validate_tile_reviews(packet, labeling_export, tile_by_id)
    regions_by_tile = _validate_regions(packet, labeling_export, tile_by_id)
    _validate_drafts(packet, labeling_export, tile_by_id)
    _validate_review_region_consistency(reviews, regions_by_tile)

    reviewed_tiles = sum(bool(review.decision) for review in reviews.values())
    blocking_issues = []
    if reviewed_tiles != len(packet.tiles):
        blocking_issues.append(
            f"tile coverage is incomplete: {reviewed_tiles}/{len(packet.tiles)} reviewed"
        )
    if labeling_export.incomplete_drafts:
        blocking_issues.append(
            f"{len(labeling_export.incomplete_drafts)} incomplete labeling drafts remain"
        )

    return LabelingReadinessReport(
        packet_id=packet.packet_id,
        processing_run_id=packet.processing_run_id,
        source_packet_sha256=_sha256(packet_path),
        source_export_sha256=_sha256(export_path),
        ready_for_adjudication=not blocking_issues,
        reviewed_tile_count=reviewed_tiles,
        total_tile_count=len(packet.tiles),
        provisional_region_count=len(labeling_export.reference_regions),
        incomplete_draft_count=len(labeling_export.incomplete_drafts),
        blocking_issues=tuple(blocking_issues),
        required_next_actions=(
            "Verify reviewer identity, SAR qualification, and independence outside this file.",
            "Deduplicate regions that describe the same area across overlapping tiles.",
            "Record independent adjudication before creating domain-reviewed labels.",
            "Confirm evaluation fixtures did not influence pipeline tuning parameters.",
        ),
        limitations=(
            "This validator checks structure, provenance, coverage, and coordinate consistency.",
            "It cannot verify reviewer expertise, interpretation quality, or label correctness.",
            "It never promotes provisional regions or authorizes pipeline metric claims.",
        ),
    )


def _validate_packet(packet: LabelingPacket) -> None:
    grid = packet.grid
    width = grid.get("width")
    height = grid.get("height")
    crs = grid.get("crs")
    bounds = grid.get("bounds")
    resolution = grid.get("resolution")
    if not isinstance(width, int) or width <= 0 or not isinstance(height, int) or height <= 0:
        raise LabelingValidationError("labeling packet grid dimensions are unusable")
    if not isinstance(crs, str) or not crs:
        raise LabelingValidationError("labeling packet grid CRS is unusable")
    if (
        not isinstance(bounds, list | tuple)
        or len(bounds) != 4
        or any(not isinstance(value, int | float) for value in bounds)
    ):
        raise LabelingValidationError("labeling packet grid bounds are unusable")
    if not isinstance(resolution, int | float) or resolution <= 0:
        raise LabelingValidationError("labeling packet grid resolution is unusable")
    if len(packet.artifacts) != 2 or {artifact.role for artifact in packet.artifacts} != {
        "before",
        "after",
    }:
        raise LabelingValidationError("labeling packet requires one before and one after artifact")
    if any(artifact.width != width or artifact.height != height for artifact in packet.artifacts):
        raise LabelingValidationError("labeling packet artifact dimensions do not match its grid")
    if not packet.tiles:
        raise LabelingValidationError("labeling packet requires at least one tile")
    tile_ids = [tile.tile_id for tile in packet.tiles]
    if len(tile_ids) != len(set(tile_ids)):
        raise LabelingValidationError("labeling packet contains duplicate tile IDs")
    for tile in packet.tiles:
        x, y, tile_width, tile_height = tile.source_box
        if (
            x < 0
            or y < 0
            or tile_width <= 0
            or tile_height <= 0
            or x + tile_width > width
            or y + tile_height > height
        ):
            raise LabelingValidationError(f"labeling packet tile {tile.tile_id} is out of bounds")


def _validate_identity(packet: LabelingPacket, labeling_export: LabelingExport) -> None:
    if labeling_export.packet_id != packet.packet_id:
        raise LabelingValidationError("labeling export does not match the packet ID")
    if labeling_export.processing_run_id != packet.processing_run_id:
        raise LabelingValidationError("labeling export does not match the processing run")
    if (
        labeling_export.source_processing_manifest_sha256
        != packet.source_processing_manifest_sha256
    ):
        raise LabelingValidationError(
            "labeling export does not match the processing manifest checksum"
        )


def _validate_tile_reviews(
    packet: LabelingPacket,
    labeling_export: LabelingExport,
    tile_by_id: dict[str, LabelingTile],
) -> dict[str, LabelingTileReview]:
    reviews = {review.tile_id: review for review in labeling_export.tile_reviews}
    if len(reviews) != len(labeling_export.tile_reviews):
        raise LabelingValidationError("labeling export contains duplicate tile reviews")
    expected = set(tile_by_id)
    actual = set(reviews)
    if missing := sorted(expected - actual):
        raise LabelingValidationError(f"labeling export is missing tile reviews: {missing}")
    if unknown := sorted(actual - expected):
        raise LabelingValidationError(f"labeling export has unknown tile reviews: {unknown}")
    reviewed_count = sum(bool(review.decision) for review in reviews.values())
    expected_status = "complete" if reviewed_count == len(packet.tiles) else "partial"
    if labeling_export.coverage.total_tiles != len(packet.tiles):
        raise LabelingValidationError("labeling export total tile count is inconsistent")
    if labeling_export.coverage.reviewed_tiles != reviewed_count:
        raise LabelingValidationError("labeling export reviewed tile count is inconsistent")
    if labeling_export.coverage.status != expected_status:
        raise LabelingValidationError("labeling export coverage status is inconsistent")
    return reviews


def _validate_regions(
    packet: LabelingPacket,
    labeling_export: LabelingExport,
    tile_by_id: dict[str, LabelingTile],
) -> dict[str, list[ProvisionalReferenceRegion]]:
    region_ids: set[str] = set()
    regions_by_tile: dict[str, list[ProvisionalReferenceRegion]] = {
        tile_id: [] for tile_id in tile_by_id
    }
    for region in labeling_export.reference_regions:
        if region.region_id in region_ids:
            raise LabelingValidationError("labeling export contains duplicate region IDs")
        region_ids.add(region.region_id)
        tile = tile_by_id.get(region.tile_id)
        if tile is None:
            raise LabelingValidationError(f"region {region.region_id} references an unknown tile")
        if region.geometry_crs != packet.grid["crs"]:
            raise LabelingValidationError(
                f"region {region.region_id} does not use the packet grid CRS"
            )
        if region.points != region.projected_points:
            raise LabelingValidationError(
                f"region {region.region_id} projected points are inconsistent"
            )
        ring = region.geometry.coordinates[0]
        expected_ring = (*region.points, region.points[0])
        if ring != expected_ring:
            raise LabelingValidationError(f"region {region.region_id} polygon ring is inconsistent")
        if len(region.pixel_points) != len(region.points):
            raise LabelingValidationError(
                f"region {region.region_id} pixel point count is inconsistent"
            )
        if _polygon_area(region.points) < 0.5:
            raise LabelingValidationError(
                f"region {region.region_id} has no measurable projected area"
            )
        for projected, pixel in zip(region.points, region.pixel_points, strict=True):
            expected_pixel = _projected_to_pixel(packet, projected)
            if not _points_close(pixel, expected_pixel):
                raise LabelingValidationError(
                    f"region {region.region_id} pixel coordinates are inconsistent"
                )
            if not _pixel_inside_tile(pixel, tile):
                raise LabelingValidationError(
                    f"region {region.region_id} falls outside its declared tile"
                )
        regions_by_tile[region.tile_id].append(region)
    return regions_by_tile


def _validate_drafts(
    packet: LabelingPacket,
    labeling_export: LabelingExport,
    tile_by_id: dict[str, LabelingTile],
) -> None:
    tile_ids: set[str] = set()
    for draft in labeling_export.incomplete_drafts:
        if draft.tile_id in tile_ids:
            raise LabelingValidationError("labeling export contains duplicate tile drafts")
        tile_ids.add(draft.tile_id)
        tile = tile_by_id.get(draft.tile_id)
        if tile is None:
            raise LabelingValidationError("labeling export contains a draft for an unknown tile")
        for point in draft.points:
            if not _pixel_inside_tile(_projected_to_pixel(packet, point), tile):
                raise LabelingValidationError(
                    f"draft for {draft.tile_id} falls outside its declared tile"
                )


def _validate_review_region_consistency(
    reviews: dict[str, LabelingTileReview],
    regions_by_tile: dict[str, list[ProvisionalReferenceRegion]],
) -> None:
    for tile_id, review in reviews.items():
        region_count = len(regions_by_tile[tile_id])
        if review.decision == "regions-drawn" and region_count == 0:
            raise LabelingValidationError(
                f"tile {tile_id} is marked regions drawn but has no saved region"
            )
        if review.decision == "reviewed-no-reference-region" and region_count:
            raise LabelingValidationError(
                f"tile {tile_id} is marked no region but has saved regions"
            )


def _projected_to_pixel(packet: LabelingPacket, point: Point) -> Point:
    bounds = packet.grid["bounds"]
    resolution = packet.grid["resolution"]
    if not isinstance(bounds, list | tuple) or len(bounds) != 4:
        raise LabelingValidationError("labeling packet grid bounds are unusable")
    if not isinstance(resolution, int | float) or resolution <= 0:
        raise LabelingValidationError("labeling packet grid resolution is unusable")
    min_x, _, _, max_y = bounds
    if not isinstance(min_x, int | float) or not isinstance(max_y, int | float):
        raise LabelingValidationError("labeling packet grid bounds are unusable")
    return ((point[0] - min_x) / resolution, (max_y - point[1]) / resolution)


def _pixel_inside_tile(point: Point, tile: LabelingTile) -> bool:
    x, y, width, height = tile.source_box
    return x <= point[0] <= x + width and y <= point[1] <= y + height


def _points_close(left: Point, right: Point) -> bool:
    return all(abs(a - b) <= POINT_TOLERANCE for a, b in zip(left, right, strict=True))


def _polygon_area(points: tuple[Point, ...]) -> float:
    twice_area = sum(
        x1 * y2 - x2 * y1
        for (x1, y1), (x2, y2) in zip(points, (*points[1:], points[0]), strict=True)
    )
    return abs(twice_area) / 2


def _read_model[T: BaseModel](path: Path, model: type[T], label: str) -> T:
    try:
        size = path.stat().st_size
        if size > MAX_LABELING_FILE_BYTES:
            raise LabelingValidationError(f"{label} exceeds the 10 MiB input limit")
        return model.model_validate_json(path.read_text())
    except OSError as error:
        raise LabelingValidationError(f"{label} could not be read: {path}") from error
    except ValidationError as error:
        raise LabelingValidationError(f"{label} failed validation: {error}") from error


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()
