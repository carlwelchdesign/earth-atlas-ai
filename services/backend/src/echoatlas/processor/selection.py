"""Deterministic acquisition-pair comparability calculations."""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from echoatlas.processor.catalog.models import Acquisition

Point = tuple[float, float]


class PairComparability(BaseModel):
    """Geometry and metadata evidence for a proposed acquisition pair."""

    model_config = ConfigDict(frozen=True)

    before_item_id: str
    after_item_id: str
    temporal_separation: timedelta
    common_footprint: dict[str, Any]
    common_bbox: tuple[float, float, float, float]
    before_overlap_percent: float = Field(ge=0, le=100)
    after_overlap_percent: float = Field(ge=0, le=100)
    same_product: bool
    shared_polarizations: tuple[str, ...]
    range_resolution_delta_percent: float = Field(ge=0)
    azimuth_resolution_delta_percent: float = Field(ge=0)
    same_observation_direction: bool
    same_orbit_state: bool
    incidence_angle_delta_deg: float | None = Field(default=None, ge=0)
    grazing_angle_delta_deg: float | None = Field(default=None, ge=0)
    warnings: tuple[str, ...]


def compare_pair(before: Acquisition, after: Acquisition) -> PairComparability:
    """Compare two convex Polygon footprints and relevant SAR metadata."""
    if before.acquired_at >= after.acquired_at:
        raise ValueError("before acquisition must precede after acquisition")

    before_ring = _outer_ring(before.geometry)
    after_ring = _outer_ring(after.geometry)
    intersection = _convex_intersection(before_ring, after_ring)
    if len(intersection) < 3:
        raise ValueError("acquisition footprints do not have a polygonal intersection")

    intersection_area = _polygon_area(intersection)
    before_area = _polygon_area(before_ring)
    after_area = _polygon_area(after_ring)
    common_bbox = (
        min(point[0] for point in intersection),
        min(point[1] for point in intersection),
        max(point[0] for point in intersection),
        max(point[1] for point in intersection),
    )
    shared_polarizations = tuple(sorted(set(before.polarizations) & set(after.polarizations)))
    warnings: list[str] = []
    if before.product_type != after.product_type:
        warnings.append("product types differ")
    if not shared_polarizations:
        warnings.append("no shared polarization")
    if before.observation_direction != after.observation_direction:
        warnings.append("observation directions differ")
    if before.orbit_state != after.orbit_state:
        warnings.append("orbit states differ")

    incidence_delta = _optional_delta(before.incidence_angle_deg, after.incidence_angle_deg)
    grazing_delta = _optional_delta(before.grazing_angle_deg, after.grazing_angle_deg)
    range_delta = _resolution_delta(before.resolution_range_m, after.resolution_range_m)
    azimuth_delta = _resolution_delta(before.resolution_azimuth_m, after.resolution_azimuth_m)
    if incidence_delta is not None and incidence_delta > 5:
        warnings.append("incidence angle differs by more than 5 degrees")
    if range_delta > 10 or azimuth_delta > 10:
        warnings.append("spatial resolution differs by more than 10 percent")

    closed_intersection = intersection + [intersection[0]]
    return PairComparability(
        before_item_id=before.item_id,
        after_item_id=after.item_id,
        temporal_separation=after.acquired_at - before.acquired_at,
        common_footprint={
            "type": "Polygon",
            "coordinates": [[[longitude, latitude] for longitude, latitude in closed_intersection]],
        },
        common_bbox=common_bbox,
        before_overlap_percent=round(100 * intersection_area / before_area, 6),
        after_overlap_percent=round(100 * intersection_area / after_area, 6),
        same_product=before.product_type == after.product_type,
        shared_polarizations=shared_polarizations,
        range_resolution_delta_percent=round(range_delta, 6),
        azimuth_resolution_delta_percent=round(azimuth_delta, 6),
        same_observation_direction=(before.observation_direction == after.observation_direction),
        same_orbit_state=before.orbit_state == after.orbit_state,
        incidence_angle_delta_deg=incidence_delta,
        grazing_angle_delta_deg=grazing_delta,
        warnings=tuple(warnings),
    )


def _outer_ring(geometry: dict[str, Any]) -> list[Point]:
    if geometry.get("type") != "Polygon":
        raise ValueError("only Polygon acquisition footprints are supported")
    coordinates = geometry.get("coordinates")
    if not isinstance(coordinates, list) or not coordinates or not isinstance(coordinates[0], list):
        raise ValueError("Polygon geometry has no outer ring")
    ring: list[Point] = []
    for coordinate in coordinates[0]:
        if not isinstance(coordinate, list) or len(coordinate) < 2:
            raise ValueError("Polygon outer ring contains an invalid coordinate")
        ring.append((float(coordinate[0]), float(coordinate[1])))
    if len(ring) > 1 and ring[0] == ring[-1]:
        ring.pop()
    if len(ring) < 3 or _polygon_area(ring) == 0:
        raise ValueError("Polygon outer ring is degenerate")
    return ring


def _convex_intersection(subject: list[Point], clip: list[Point]) -> list[Point]:
    output = subject
    orientation = 1 if _signed_area(clip) > 0 else -1
    for index, clip_end in enumerate(clip):
        clip_start = clip[index - 1]
        input_points = output
        output = []
        if not input_points:
            break
        subject_start = input_points[-1]
        for subject_end in input_points:
            end_inside = _inside(subject_end, clip_start, clip_end, orientation)
            start_inside = _inside(subject_start, clip_start, clip_end, orientation)
            if end_inside:
                if not start_inside:
                    output.append(
                        _line_intersection(subject_start, subject_end, clip_start, clip_end)
                    )
                output.append(subject_end)
            elif start_inside:
                output.append(_line_intersection(subject_start, subject_end, clip_start, clip_end))
            subject_start = subject_end
    return output


def _inside(point: Point, edge_start: Point, edge_end: Point, orientation: int) -> bool:
    cross = (edge_end[0] - edge_start[0]) * (point[1] - edge_start[1]) - (
        edge_end[1] - edge_start[1]
    ) * (point[0] - edge_start[0])
    return orientation * cross >= -1e-12


def _line_intersection(
    first_start: Point, first_end: Point, second_start: Point, second_end: Point
) -> Point:
    first_dx = first_end[0] - first_start[0]
    first_dy = first_end[1] - first_start[1]
    second_dx = second_end[0] - second_start[0]
    second_dy = second_end[1] - second_start[1]
    denominator = first_dx * second_dy - first_dy * second_dx
    if abs(denominator) < 1e-15:
        return first_end
    offset_x = second_start[0] - first_start[0]
    offset_y = second_start[1] - first_start[1]
    position = (offset_x * second_dy - offset_y * second_dx) / denominator
    return first_start[0] + position * first_dx, first_start[1] + position * first_dy


def _signed_area(ring: list[Point]) -> float:
    return (
        sum(
            ring[index - 1][0] * point[1] - point[0] * ring[index - 1][1]
            for index, point in enumerate(ring)
        )
        / 2
    )


def _polygon_area(ring: list[Point]) -> float:
    return abs(_signed_area(ring))


def _optional_delta(before: float | None, after: float | None) -> float | None:
    if before is None or after is None:
        return None
    return round(abs(before - after), 6)


def _resolution_delta(before: float | None, after: float | None) -> float:
    if before is None or after is None:
        return 100
    return 100 * abs(before - after) / min(before, after)
