from __future__ import annotations

import json
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

import pytest
from pydantic import ValidationError

from echoatlas.processor.catalog.http import CatalogAccessError, SafeMetadataClient
from echoatlas.processor.catalog.providers import (
    Sentinel1CatalogSearchAdapter,
    UmbraCatalogSearchAdapter,
)
from echoatlas.processor.catalog.search import CatalogSearchError, CatalogSearchService
from echoatlas.processor.catalog.search_models import (
    CatalogLicense,
    CatalogSearchItem,
    CatalogSearchRequest,
    CatalogSearchWarning,
    CatalogSourceIdentity,
    GeoJsonPolygon,
    ProviderSearchPage,
    SearchAoi,
)
from echoatlas.processor.catalog.stac import StacCatalogAdapter

FIXTURES = Path(__file__).parent / "fixtures" / "catalog"
NOW = datetime(2026, 8, 25, 12, tzinfo=UTC)


class FixtureClient:
    def __init__(self) -> None:
        self.requested: list[str] = []

    def get_bytes(self, url: str) -> bytes:
        return json.dumps(self.get_json(url)).encode()

    def get_json(self, url: str) -> Mapping[str, Any]:
        self.requested.append(url)
        filename = "sentinel-page-2.json" if "token=page-2" in url else "sentinel-page-1.json"
        value = json.loads((FIXTURES / filename).read_text())
        assert isinstance(value, dict)
        return value


class UmbraFixtureClient:
    def __init__(self) -> None:
        self.requested: list[str] = []

    def get_bytes(self, url: str) -> bytes:
        return json.dumps(self.get_json(url)).encode()

    def get_json(self, url: str) -> Mapping[str, Any]:
        self.requested.append(url)
        name = url.rsplit("/", 1)[-1]
        if name == "catalog.json" and "/day/" not in url:
            name = "root.json"
        elif name == "catalog.json":
            name = "day.json"
        if name == "network-failure.json":
            raise CatalogAccessError("simulated timeout")
        value = json.loads((FIXTURES / name).read_text())
        assert isinstance(value, dict)
        if name == "valid.json":
            coordinates = value["geometry"]["coordinates"][0]
            value["geometry"]["coordinates"][0] = [
                [longitude, latitude, 12.5] for longitude, latitude in coordinates
            ]
        return value


class FakeHttpResponse:
    def __init__(
        self,
        payload: bytes,
        *,
        final_url: str,
        content_length: str | None = None,
    ) -> None:
        self.payload = payload
        self.final_url = final_url
        self.headers = {} if content_length is None else {"Content-Length": content_length}

    def __enter__(self) -> FakeHttpResponse:
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def geturl(self) -> str:
        return self.final_url

    def read(self, limit: int) -> bytes:
        return self.payload[:limit]


class FakeAdapter:
    def __init__(
        self,
        provider: Literal["umbra", "sentinel-1"],
        page: ProviderSearchPage | Exception,
    ) -> None:
        self.provider = provider
        self.page = page
        self.calls = 0

    def search(self, request: CatalogSearchRequest, *, limit: int) -> ProviderSearchPage:
        self.calls += 1
        assert limit == 300
        if isinstance(self.page, Exception):
            raise self.page
        return self.page


def request(**changes: Any) -> CatalogSearchRequest:
    values: dict[str, Any] = {
        "aoi": SearchAoi(
            bbox=(-112.2, 40.45, -112.05, 40.6),
            geometry=GeoJsonPolygon(
                coordinates=(
                    (
                        (-112.2, 40.45),
                        (-112.05, 40.45),
                        (-112.05, 40.6),
                        (-112.2, 40.6),
                        (-112.2, 40.45),
                    ),
                )
            ),
        ),
        "start_at": datetime(2025, 6, 1, tzinfo=UTC),
        "end_at": datetime(2025, 8, 1, tzinfo=UTC),
        "providers": ("sentinel-1",),
        "page_size": 1,
    }
    values.update(changes)
    return CatalogSearchRequest(**values)


def item(
    identifier: str,
    *,
    acquired_at: datetime,
    bbox: tuple[float, float, float, float] = (-112.3, 39.3, -108.9, 41.3),
) -> CatalogSearchItem:
    west, south, east, north = bbox
    return CatalogSearchItem(
        provider="sentinel-1",
        acquired_at=acquired_at,
        bbox=bbox,
        footprint=GeoJsonPolygon(
            coordinates=(
                (
                    (west, south),
                    (east, south),
                    (east, north),
                    (west, north),
                    (west, south),
                ),
            )
        ),
        product_type="IW_GRDH_1S_C",
        polarizations=("VV", "VH"),
        resolution_range_m=10,
        resolution_azimuth_m=10,
        platform="sentinel-1c",
        observation_direction="right",
        orbit_state="ascending",
        incidence_angle_deg=39.1,
        license=CatalogLicense(label="Copernicus notice", url="https://example.test/license"),
        source=CatalogSourceIdentity(
            item_id=identifier,
            collection="sentinel-1-grd",
            href=f"https://example.test/items/{identifier}",
        ),
    )


def test_contract_rejects_unbounded_aoi_time_and_naive_timestamps() -> None:
    with pytest.raises(ValidationError, match="five-degree"):
        SearchAoi(
            bbox=(-20.0, 0.0, 20.0, 10.0),
            geometry=GeoJsonPolygon(
                coordinates=(((-20.0, 0.0), (20.0, 0.0), (20.0, 10.0), (-20.0, 0.0)),)
            ),
        )
    with pytest.raises(ValidationError, match="366 days"):
        request(end_at=datetime(2027, 8, 2, tzinfo=UTC))
    with pytest.raises(ValidationError, match="timezone"):
        request(start_at=datetime(2025, 6, 1))


def test_safe_metadata_client_enforces_host_redirect_size_and_timeout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = SafeMetadataClient(
        allowed_hosts=frozenset({"allowed.test"}),
        max_response_bytes=10,
        timeout_seconds=1,
    )
    with pytest.raises(CatalogAccessError, match="not allowlisted"):
        client.get_bytes("https://blocked.test/catalog.json")

    monkeypatch.setattr(
        "echoatlas.processor.catalog.http.urlopen",
        lambda *args, **kwargs: FakeHttpResponse(
            b"{}", final_url="https://blocked.test/redirected.json"
        ),
    )
    with pytest.raises(CatalogAccessError, match="redirect left"):
        client.get_bytes("https://allowed.test/catalog.json")

    monkeypatch.setattr(
        "echoatlas.processor.catalog.http.urlopen",
        lambda *args, **kwargs: FakeHttpResponse(
            b"{}", final_url="https://allowed.test/catalog.json", content_length="11"
        ),
    )
    with pytest.raises(CatalogAccessError, match="exceeds size limit"):
        client.get_bytes("https://allowed.test/catalog.json")

    def timeout(*args: object, **kwargs: object) -> FakeHttpResponse:
        raise TimeoutError("simulated timeout")

    monkeypatch.setattr("echoatlas.processor.catalog.http.urlopen", timeout)
    with pytest.raises(CatalogAccessError, match="metadata request failed"):
        client.get_bytes("https://allowed.test/catalog.json")


def test_service_paginates_binds_cursor_and_reuses_bounded_cache() -> None:
    adapter = FakeAdapter(
        "sentinel-1",
        ProviderSearchPage(
            items=(
                item("older", acquired_at=datetime(2025, 7, 1, tzinfo=UTC)),
                item("newer", acquired_at=datetime(2025, 7, 2, tzinfo=UTC)),
            )
        ),
    )
    service = CatalogSearchService({"sentinel-1": adapter}, clock=lambda: NOW)

    first = service.search(request())
    assert first.cache == "miss"
    assert first.status == "complete"
    assert first.sampled_result_count == 2
    assert [result.source.item_id for result in first.results] == ["newer"]
    assert first.next_cursor is not None

    second = service.search(request(cursor=first.next_cursor))
    assert second.cache == "hit"
    assert [result.source.item_id for result in second.results] == ["older"]
    assert second.next_cursor is None
    assert adapter.calls == 1

    with pytest.raises(CatalogSearchError, match="does not match"):
        service.search(request(cursor=first.next_cursor, page_size=2))


def test_service_bounds_cache_entries_and_response_size() -> None:
    adapter = FakeAdapter(
        "sentinel-1",
        ProviderSearchPage(
            items=(item("available", acquired_at=datetime(2025, 7, 2, tzinfo=UTC)),)
        ),
    )
    service = CatalogSearchService(
        {"sentinel-1": adapter},
        clock=lambda: NOW,
        max_cache_entries=1,
    )

    service.search(request(page_size=1))
    service.search(request(page_size=2))
    service.search(request(page_size=1))

    assert adapter.calls == 3

    limited = CatalogSearchService(
        {"sentinel-1": adapter},
        clock=lambda: NOW,
        max_response_bytes=100,
    )
    with pytest.raises(CatalogSearchError, match="two-megabyte"):
        limited.search(request(page_size=1))


def test_service_preserves_success_when_another_provider_fails() -> None:
    sentinel = FakeAdapter(
        "sentinel-1",
        ProviderSearchPage(
            items=(item("available", acquired_at=datetime(2025, 7, 2, tzinfo=UTC)),),
            warnings=(
                CatalogSearchWarning(
                    code="provider_notice",
                    provider="sentinel-1",
                    message="fixture notice",
                ),
            ),
        ),
    )
    umbra = FakeAdapter("umbra", CatalogAccessError("simulated timeout"))
    service = CatalogSearchService({"sentinel-1": sentinel, "umbra": umbra}, clock=lambda: NOW)

    response = service.search(request(providers=("umbra", "sentinel-1"), page_size=10))

    assert response.status == "partial"
    assert [result.source.item_id for result in response.results] == ["available"]
    assert [(report.provider, report.status) for report in response.providers] == [
        ("umbra", "failed"),
        ("sentinel-1", "partial"),
    ]
    assert {warning.code for warning in response.warnings} == {
        "provider_request_failed",
        "provider_notice",
    }


def test_sentinel_adapter_uses_bounded_query_and_normalizes_fixture_pages() -> None:
    client = FixtureClient()
    adapter = Sentinel1CatalogSearchAdapter(client, max_pages=2, page_size=1)

    page = adapter.search(request(page_size=10), limit=10)

    assert len(client.requested) == 2
    assert "bbox=-112.2%2C40.45%2C-112.05%2C40.6" in client.requested[0]
    assert "collections=sentinel-1-grd" in client.requested[0]
    assert [result.source.item_id for result in page.items] == [
        "S1C-IW-GRD-001",
        "S1A-IW-GRD-002",
    ]
    assert page.items[0].product_type == "IW_GRDH_1S_C"
    assert page.items[0].resolution_range_m == 10
    assert page.items[0].license.label == "Copernicus Sentinel Data Legal Notice"
    assert "properties" not in page.items[0].model_dump()
    assert page.has_more is False


def test_umbra_adapter_spatially_filters_static_catalog_fixture() -> None:
    client = UmbraFixtureClient()
    adapter = UmbraCatalogSearchAdapter(
        StacCatalogAdapter(client),
        root_url="https://example.test/stac/catalog.json",
        max_catalogs=10,
        max_items=10,
    )

    page = adapter.search(request(providers=("umbra",), page_size=10), limit=10)

    assert [result.source.item_id for result in page.items] == ["item-1"]
    assert page.items[0].provider == "umbra"
    assert page.items[0].license.label == "CC-BY-4.0"
    assert len(page.items[0].footprint.coordinates[0][0]) == 2
    assert "source_document" not in page.items[0].model_dump()

    outside = request(
        providers=("umbra",),
        aoi=SearchAoi(
            bbox=(10.0, 10.0, 10.1, 10.1),
            geometry=GeoJsonPolygon(
                coordinates=(((10.0, 10.0), (10.1, 10.0), (10.1, 10.1), (10.0, 10.0)),)
            ),
        ),
    )
    assert adapter.search(outside, limit=10).items == ()


def test_umbra_adapter_targets_only_requested_month_catalogs() -> None:
    adapter = UmbraCatalogSearchAdapter(StacCatalogAdapter(UmbraFixtureClient()))
    search = request(
        providers=("umbra",),
        start_at=datetime(2025, 6, 10, tzinfo=UTC),
        end_at=datetime(2025, 8, 1, tzinfo=UTC),
    )

    assert adapter._search_roots(search) == (
        "https://umbra-open-data-catalog.s3.us-west-2.amazonaws.com/stac/2025/2025-06/catalog.json",
        "https://umbra-open-data-catalog.s3.us-west-2.amazonaws.com/stac/2025/2025-07/catalog.json",
        "https://umbra-open-data-catalog.s3.us-west-2.amazonaws.com/stac/2025/2025-08/catalog.json",
    )


def test_sentinel_adapter_reports_bounded_page_limit() -> None:
    page = Sentinel1CatalogSearchAdapter(FixtureClient(), max_pages=1, page_size=1).search(
        request(), limit=10
    )

    assert page.has_more is True
    assert {warning.code for warning in page.warnings} == {"sentinel_page_limit_reached"}
