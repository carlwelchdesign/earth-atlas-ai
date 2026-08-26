from __future__ import annotations

import json
from collections.abc import Iterator
from urllib.request import Request

import pytest

from echoatlas.places import (
    NominatimPlace,
    NominatimPlaceProvider,
    PlaceSearchError,
    PlaceSearchService,
)


class FakeProvider:
    def __init__(self, result: NominatimPlace | None) -> None:
        self.result = result
        self.queries: list[str] = []

    def search(self, query: str) -> NominatimPlace | None:
        self.queries.append(query)
        return self.result


class FakeResponse:
    def __init__(self, payload: bytes, final_url: str) -> None:
        self.payload = payload
        self.final_url = final_url
        self.headers: dict[str, str] = {}

    def __enter__(self) -> FakeResponse:
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def geturl(self) -> str:
        return self.final_url

    def read(self, limit: int) -> bytes:
        return self.payload[:limit]


def test_nominatim_provider_identifies_app_and_normalizes_first_result() -> None:
    requests: list[Request] = []

    def opener(request: Request, *, timeout: float) -> FakeResponse:
        requests.append(request)
        assert timeout == 10
        payload = json.dumps(
            [
                {
                    "display_name": "Sacramento, California, United States",
                    "lat": "38.5810606",
                    "lon": "-121.493895",
                }
            ]
        ).encode()
        return FakeResponse(payload, request.full_url)

    result = NominatimPlaceProvider(opener=opener).search("Sacramento, California")

    assert result == NominatimPlace(
        label="Sacramento, California, United States",
        latitude=38.5810606,
        longitude=-121.493895,
    )
    assert "q=Sacramento%2C+California" in requests[0].full_url
    assert requests[0].get_header("User-agent").startswith("EchoAtlas/0.1")


def test_nominatim_provider_rejects_non_allowlisted_configuration() -> None:
    with pytest.raises(ValueError, match="allowlisted"):
        NominatimPlaceProvider(search_url="https://example.test/search")


def test_place_service_bounds_aoi_rate_limits_and_caches() -> None:
    provider = FakeProvider(
        NominatimPlace(label="Near the dateline", latitude=89.98, longitude=179.98)
    )
    readings: Iterator[float] = iter((0.0, 0.0, 0.5, 1.6))
    sleeps: list[float] = []
    service = PlaceSearchService(
        provider,
        monotonic=lambda: next(readings),
        sleep=sleeps.append,
    )

    first = service.resolve("  Near   the dateline ")
    second = service.resolve("Another place")
    cached = service.resolve("near the dateline")

    assert first.bbox == pytest.approx((179.905, 89.905, 180.0, 90.0))
    assert second.label == "Near the dateline"
    assert cached is first
    assert provider.queries == ["Near the dateline", "Another place"]
    assert sleeps == pytest.approx([0.6])


@pytest.mark.parametrize("query", ["x", "x" * 121])
def test_place_service_rejects_unbounded_query_lengths(query: str) -> None:
    provider = FakeProvider(None)
    with pytest.raises(PlaceSearchError, match="2 and 120"):
        PlaceSearchService(provider).resolve(query)
    assert provider.queries == []


def test_place_service_distinguishes_no_match() -> None:
    with pytest.raises(PlaceSearchError, match="No place match"):
        PlaceSearchService(FakeProvider(None)).resolve("Imaginary place")
