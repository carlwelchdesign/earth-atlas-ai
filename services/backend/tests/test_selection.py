from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest

from echoatlas.processor.catalog.models import Acquisition
from echoatlas.processor.selection import compare_pair

MANIFEST_PATH = Path(__file__).parents[3] / "fixtures" / "demo" / "selection-manifest.v1.json"


def acquisition(
    item_id: str,
    acquired_at: datetime,
    geometry: dict[str, Any],
    *,
    observation_direction: str = "left",
    orbit_state: str = "ascending",
    incidence_angle_deg: float = 40,
) -> Acquisition:
    return Acquisition(
        item_id=item_id,
        acquired_at=acquired_at,
        bbox=(0, 0, 2, 2),
        geometry=geometry,
        product_type="GEC",
        polarizations=("VV",),
        resolution_range_m=0.5,
        resolution_azimuth_m=0.5,
        platform="Umbra-test",
        observation_direction=observation_direction,
        orbit_state=orbit_state,
        incidence_angle_deg=incidence_angle_deg,
        grazing_angle_deg=90 - incidence_angle_deg,
        license="CC-BY-4.0",
        source_url=f"https://example.test/{item_id}.json",
        provider_task_id=f"task-{item_id}",
        assets=(),
        source_document={},
    )


def polygon(west: float, south: float, east: float, north: float) -> dict[str, Any]:
    return {
        "type": "Polygon",
        "coordinates": [
            [[west, south], [east, south], [east, north], [west, north], [west, south]]
        ],
    }


def test_compare_pair_reports_common_footprint_and_compatibility() -> None:
    before = acquisition("before", datetime(2025, 1, 1, tzinfo=UTC), polygon(0, 0, 2, 2))
    after = acquisition("after", datetime(2025, 1, 26, tzinfo=UTC), polygon(1, 0, 3, 2))

    result = compare_pair(before, after)

    assert result.temporal_separation.days == 25
    assert result.common_bbox == pytest.approx((1, 0, 2, 2))
    assert result.before_overlap_percent == 50
    assert result.after_overlap_percent == 50
    assert result.same_product is True
    assert result.shared_polarizations == ("VV",)
    assert result.warnings == ()


def test_compare_pair_surfaces_geometry_differences() -> None:
    before = acquisition("before", datetime(2025, 1, 1, tzinfo=UTC), polygon(0, 0, 2, 2))
    after = acquisition(
        "after",
        datetime(2025, 1, 10, tzinfo=UTC),
        polygon(0, 0, 2, 2),
        observation_direction="right",
        orbit_state="descending",
        incidence_angle_deg=50,
    )

    result = compare_pair(before, after)

    assert set(result.warnings) == {
        "incidence angle differs by more than 5 degrees",
        "observation directions differ",
        "orbit states differ",
    }


def test_compare_pair_rejects_reversed_time_and_non_overlap() -> None:
    first = acquisition("first", datetime(2025, 1, 2, tzinfo=UTC), polygon(0, 0, 1, 1))
    second = acquisition("second", datetime(2025, 1, 1, tzinfo=UTC), polygon(2, 2, 3, 3))

    with pytest.raises(ValueError, match="must precede"):
        compare_pair(first, second)
    with pytest.raises(ValueError, match="do not have"):
        compare_pair(second, first)


def test_proposed_manifest_pins_access_and_sensitivity_evidence() -> None:
    manifest = json.loads(MANIFEST_PATH.read_text())
    geometry = manifest["processing_aoi"]["geometry"]
    canonical_geometry = json.dumps(geometry, separators=(",", ":"), sort_keys=True).encode()

    assert manifest["manifest_version"] == "1.0.0"
    assert manifest["status"] == "awaiting_owner_approval"
    assert manifest["approval"]["approved_by"] is None
    assert (
        manifest["processing_aoi"]["geometry_sha256"]
        == hashlib.sha256(canonical_geometry).hexdigest()
    )
    assert manifest["comparability"]["before_overlap_percent"] > 99
    assert manifest["comparability"]["after_overlap_percent"] > 99
    assert manifest["comparability"]["warnings"] == []
    assert len(manifest["sensitivity_controls"]) >= 4

    total_size = 0
    for role in ("before", "after"):
        acquisition = manifest["acquisitions"][role]
        pinned_object = acquisition["object"]
        assert acquisition["product_type"] == "GEC"
        assert acquisition["polarizations"] == ["VV"]
        assert pinned_object["url"].startswith("https://umbra-open-data-catalog.")
        assert pinned_object["checksum"]["algorithm"] == "CRC64NVME"
        assert "HTTP 206" in pinned_object["access_verification"]
        total_size += pinned_object["size_bytes"]
    assert total_size == 524_289_889
