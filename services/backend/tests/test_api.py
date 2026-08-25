from datetime import UTC, datetime
from typing import Literal

from fastapi.testclient import TestClient

from echoatlas import __version__
from echoatlas.api.app import create_app
from echoatlas.processor.catalog.search import CatalogSearchService
from echoatlas.processor.catalog.search_models import (
    CatalogLicense,
    CatalogSearchItem,
    CatalogSearchRequest,
    CatalogSourceIdentity,
    GeoJsonPolygon,
    ProviderSearchPage,
    SearchAoi,
)

NOW = datetime(2025, 7, 2, tzinfo=UTC)


class ApiAdapter:
    provider: Literal["sentinel-1"] = "sentinel-1"

    def search(self, request: CatalogSearchRequest, *, limit: int) -> ProviderSearchPage:
        return ProviderSearchPage(items=(_api_item(),))


def _api_request() -> CatalogSearchRequest:
    return CatalogSearchRequest(
        aoi=SearchAoi(
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
        start_at=datetime(2025, 6, 1, tzinfo=UTC),
        end_at=datetime(2025, 8, 1, tzinfo=UTC),
        providers=("sentinel-1",),
        page_size=10,
    )


def _api_item() -> CatalogSearchItem:
    return CatalogSearchItem(
        provider="sentinel-1",
        acquired_at=NOW,
        bbox=(-112.3, 39.3, -108.9, 41.3),
        footprint=GeoJsonPolygon(
            coordinates=(
                (
                    (-112.3, 39.3),
                    (-108.9, 39.3),
                    (-108.9, 41.3),
                    (-112.3, 41.3),
                    (-112.3, 39.3),
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
        license=CatalogLicense(label="Copernicus notice"),
        source=CatalogSourceIdentity(
            item_id="api-item",
            collection="sentinel-1-grd",
            href="https://example.test/items/api-item",
        ),
    )


def test_health_reports_service_identity_and_version() -> None:
    response = TestClient(create_app()).get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "echoatlas-api",
        "version": __version__,
    }


def test_openapi_describes_health_and_versioned_catalog_search() -> None:
    response = TestClient(create_app()).get("/openapi.json")

    assert response.status_code == 200
    assert response.json()["info"]["title"] == "EchoAtlas API"
    assert set(response.json()["paths"]) == {"/health", "/v1/catalog/search"}


def test_catalog_search_endpoint_returns_normalized_provider_results() -> None:
    adapter = ApiAdapter()
    service = CatalogSearchService({"sentinel-1": adapter}, clock=lambda: NOW)

    response = TestClient(create_app(service)).post(
        "/v1/catalog/search",
        json=_api_request().model_dump(mode="json"),
    )

    assert response.status_code == 200
    assert response.json()["contract_version"] == "1.0.0"
    assert response.json()["results"][0]["source"]["item_id"] == "api-item"
    assert "source_document" not in response.text
