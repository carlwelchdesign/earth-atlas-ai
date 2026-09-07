from datetime import date
from typing import Any

import pytest

from echoatlas.nepal_imagery import NepalImageryError, NepalImageryService

ITEM_ID = "S2B_45RUM_20260827_0_L2A"


def item(identifier: str = ITEM_ID) -> dict[str, Any]:
    return {
        "id": identifier,
        "properties": {
            "datetime": "2026-08-27T05:10:45.885000Z",
            "s2:product_uri": "S2B_MSIL2A_20260827T045659_TEST.SAFE",
            "proj:epsg": 32645,
            "eo:cloud_cover": 78.47,
            "s2:cloud_shadow_percentage": 0.47,
            "s2:nodata_pixel_percentage": 8.59,
        },
        "assets": {
            "visual": {
                "href": (
                    "https://sentinel-cogs.s3.us-west-2.amazonaws.com/"
                    "sentinel-s2-l2a-cogs/45/R/UM/2026/8/item/TCI.tif"
                ),
                "gsd": 10,
            }
        },
    }


class FakeMetadata:
    def __init__(self, feature: dict[str, Any] | None = None) -> None:
        self.feature = feature or item()
        self.urls: list[str] = []

    def get_json(self, url: str) -> dict[str, Any]:
        self.urls.append(url)
        if "/search?" in url:
            return {"type": "FeatureCollection", "features": [self.feature]}
        return self.feature


def test_nepal_acquisition_search_is_bounded_to_sixty_days() -> None:
    service = NepalImageryService(FakeMetadata())

    result = service.list_acquisitions(date(2026, 7, 27), date(2026, 9, 24))

    assert result.maximum_range_days == 60
    assert result.acquisitions[0].item_id == ITEM_ID
    assert result.acquisitions[0].image_url.endswith(f"/{ITEM_ID}.png")

    with pytest.raises(NepalImageryError, match="cannot exceed 60 days"):
        service.list_acquisitions(date(2026, 7, 27), date(2026, 9, 25))


def test_nepal_acquisition_search_rejects_reversed_and_out_of_case_ranges() -> None:
    service = NepalImageryService(FakeMetadata())

    with pytest.raises(NepalImageryError, match="must precede"):
        service.list_acquisitions(date(2026, 8, 27), date(2026, 8, 27))
    with pytest.raises(NepalImageryError, match="bounded"):
        service.list_acquisitions(date(2026, 7, 26), date(2026, 8, 1))


def test_nepal_acquisition_rejects_items_outside_the_pinned_grid() -> None:
    service = NepalImageryService(FakeMetadata(item("S2B_44RUM_20260827_0_L2A")))

    with pytest.raises(NepalImageryError, match="outside the Nepal case grid"):
        service.list_acquisitions(date(2026, 8, 1), date(2026, 9, 1))


def test_render_uses_only_the_catalog_validated_visual_asset(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    metadata = FakeMetadata()
    service = NepalImageryService(metadata)
    rendered: list[str] = []

    def fake_render(url: str) -> bytes:
        rendered.append(url)
        return b"png"

    monkeypatch.setattr("echoatlas.nepal_imagery._render_aoi_png", fake_render)

    assert service.render_png(ITEM_ID) == b"png"
    assert service.render_png(ITEM_ID) == b"png"
    assert rendered == [item()["assets"]["visual"]["href"]]
