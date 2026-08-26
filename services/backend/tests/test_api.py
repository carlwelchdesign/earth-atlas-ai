import threading
import time
from datetime import UTC, datetime, timedelta
from typing import Literal

import pytest
from fastapi.testclient import TestClient

from echoatlas import __version__
from echoatlas.analysis_jobs import AnalysisJobService, AnalysisSelectionManifest
from echoatlas.api.app import create_app
from echoatlas.places import PlaceMatch, PlaceSearchService
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


class PlaceAdapter:
    def search(self, query: str) -> PlaceMatch | None:
        assert query == "Sacramento"
        return PlaceMatch(
            label="Sacramento, California, United States",
            latitude=38.5810606,
            longitude=-121.493895,
            provider="Test geocoder",
            attribution_url="https://example.test/terms",
        )


class AnalysisRunner:
    def run(
        self, manifest: AnalysisSelectionManifest, cancelled: threading.Event
    ) -> dict[str, object]:
        return {
            "contractVersion": "1.0.0",
            "bundleId": "api-bundle",
            "acquisitions": [
                {"role": "before", "id": manifest.before.source.item_id},
                {"role": "after", "id": manifest.after.source.item_id},
            ],
        }


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
    assert set(response.json()["paths"]) == {
        "/health",
        "/v1/catalog/search",
        "/v1/places/resolve",
        "/v1/analysis/selections",
        "/v1/analysis/jobs",
        "/v1/analysis/jobs/{job_id}",
        "/v1/analysis/jobs/{job_id}/retry",
    }


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


def test_place_search_endpoint_returns_a_bounded_normalized_aoi() -> None:
    response = TestClient(create_app(place_search=PlaceSearchService(PlaceAdapter()))).post(
        "/v1/places/resolve", json={"query": "Sacramento"}
    )

    assert response.status_code == 200
    body = response.json()
    assert body | {"bbox": None} == {
        "label": "Sacramento, California, United States",
        "bbox": None,
        "provider": "Test geocoder",
        "attribution_url": "https://example.test/terms",
    }
    assert body["bbox"] == pytest.approx([-121.568895, 38.5060606, -121.418895, 38.6560606])


def test_analysis_endpoints_compare_before_queueing_and_return_job_states() -> None:
    before = _api_item().model_copy(
        update={
            "acquired_at": NOW,
            "source": CatalogSourceIdentity(
                item_id="sentinel-before",
                collection="sentinel-1-grd",
                href="https://stac.dataspace.copernicus.eu/items/sentinel-before",
            ),
        }
    )
    after = _api_item().model_copy(
        update={
            "acquired_at": NOW + timedelta(days=12),
            "source": CatalogSourceIdentity(
                item_id="sentinel-after",
                collection="sentinel-1-grd",
                href="https://stac.dataspace.copernicus.eu/items/sentinel-after",
            ),
        }
    )
    client = TestClient(create_app(analysis_jobs=AnalysisJobService(AnalysisRunner())))

    selection_response = client.post(
        "/v1/analysis/selections",
        json={
            "contract_version": "1.0.0",
            "aoi": _api_request().aoi.model_dump(mode="json"),
            "before": before.model_dump(mode="json"),
            "after": after.model_dump(mode="json"),
        },
    )

    assert selection_response.status_code == 200
    manifest = selection_response.json()
    assert manifest["comparability"]["scientific_validity"] == "not_determined"
    job_response = client.post("/v1/analysis/jobs", json={"manifest": manifest})
    assert job_response.status_code == 202
    job_id = job_response.json()["job_id"]
    deadline = time.monotonic() + 2
    while time.monotonic() < deadline:
        body = client.get(f"/v1/analysis/jobs/{job_id}").json()
        if body["status"] == "succeeded":
            break
        time.sleep(0.01)
    assert body["status"] == "succeeded"
    assert body["bundle"]["bundleId"] == "api-bundle"
