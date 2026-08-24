from __future__ import annotations

import json
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest

from echoatlas.processor.catalog.http import CatalogAccessError
from echoatlas.processor.catalog.indexer import CatalogIndexer
from echoatlas.processor.catalog.models import Acquisition
from echoatlas.processor.catalog.s3 import PublicS3ObjectResolver
from echoatlas.processor.catalog.stac import StacCatalogAdapter

FIXTURES = Path(__file__).parent / "fixtures" / "catalog"
BASE_URL = "https://example.test/stac/"
BUCKET_URL = "https://example.test"


class FakeMetadataClient:
    def __init__(self, responses: Mapping[str, Mapping[str, Any] | bytes | Exception]) -> None:
        self.responses = responses
        self.requested: list[str] = []

    def get_bytes(self, url: str) -> bytes:
        response = self._response(url)
        if isinstance(response, bytes):
            return response
        return json.dumps(response).encode()

    def get_json(self, url: str) -> Mapping[str, Any]:
        response = self._response(url)
        if isinstance(response, bytes):
            value = json.loads(response)
            assert isinstance(value, dict)
            return value
        return response

    def _response(self, url: str) -> Mapping[str, Any] | bytes:
        self.requested.append(url)
        response = self.responses.get(url, CatalogAccessError(f"unexpected URL: {url}"))
        if isinstance(response, Exception):
            raise response
        return response


def load_json(name: str) -> Mapping[str, Any]:
    value = json.loads((FIXTURES / name).read_text())
    assert isinstance(value, dict)
    return value


def load_bytes(name: str) -> bytes:
    return (FIXTURES / name).read_bytes()


def stac_responses() -> dict[str, Mapping[str, Any] | bytes | Exception]:
    return {
        f"{BASE_URL}catalog.json": load_json("root.json"),
        f"{BASE_URL}day/catalog.json": load_json("day.json"),
        f"{BASE_URL}day/valid.json": load_json("valid.json"),
        f"{BASE_URL}day/missing-geometry.json": load_json("missing-geometry.json"),
        f"{BASE_URL}day/network-failure.json": CatalogAccessError("simulated timeout"),
    }


def first_acquisition() -> Acquisition:
    result = StacCatalogAdapter(FakeMetadataClient(stac_responses())).traverse(
        f"{BASE_URL}catalog.json"
    )
    assert len(result.acquisitions) == 1
    return result.acquisitions[0]


def test_stac_traversal_normalizes_items_and_surfaces_irregularities() -> None:
    result = StacCatalogAdapter(FakeMetadataClient(stac_responses())).traverse(
        f"{BASE_URL}catalog.json"
    )

    assert result.coverage.catalogs_visited == 2
    assert result.coverage.item_links_seen == 3
    assert result.coverage.items_indexed == 1
    assert result.coverage.items_skipped == 2
    assert result.acquisitions[0].product_type == "GEC"
    assert result.acquisitions[0].polarizations == ("VV",)
    assert result.acquisitions[0].assets[0].href is None
    assert result.acquisitions[0].source_document["id"] == "item-1"
    assert {warning.code for warning in result.warnings} == {
        "empty_asset_href",
        "item_invalid",
        "malformed_link",
    }


def test_stac_traversal_reports_bounds() -> None:
    result = StacCatalogAdapter(FakeMetadataClient(stac_responses())).traverse(
        f"{BASE_URL}catalog.json", max_catalogs=1, max_items=1
    )

    assert result.coverage.catalog_limit_reached is True
    assert result.coverage.items_indexed == 0


def test_s3_resolver_follows_continuation_tokens_without_downloading_objects() -> None:
    first_url = f"{BUCKET_URL}/?list-type=2&prefix=sar-data%2Ftask-data%2Ftask-1%2F&max-keys=1000"
    second_url = f"{first_url}&continuation-token=next-page"
    client = FakeMetadataClient(
        {
            first_url: load_bytes("s3-page-1.xml"),
            second_url: load_bytes("s3-page-2.xml"),
        }
    )

    objects, warnings, pages = PublicS3ObjectResolver(client, BUCKET_URL).resolve(
        first_acquisition()
    )

    assert pages == 2
    assert warnings == ()
    assert [asset.size_bytes for asset in objects] == [1024, 512]
    assert all(asset.origin == "public-s3" for asset in objects)
    assert client.requested == [first_url, second_url]
    assert all("collect_GEC.tif" not in url for url in client.requested)


def test_s3_resolver_rejects_unpageable_truncated_listing() -> None:
    listing_url = f"{BUCKET_URL}/?list-type=2&prefix=sar-data%2Ftask-data%2Ftask-1%2F&max-keys=1000"
    client = FakeMetadataClient({listing_url: load_bytes("s3-truncated-without-token.xml")})

    with pytest.raises(CatalogAccessError, match="no continuation token"):
        PublicS3ObjectResolver(client, BUCKET_URL).resolve(first_acquisition())


def test_indexer_builds_report_and_candidate_time_series() -> None:
    responses = stac_responses()
    day = dict(load_json("day.json"))
    day["links"] = [
        {"rel": "item", "href": "./valid.json"},
        {"rel": "item", "href": "./second.json"},
    ]
    second = dict(load_json("valid.json"))
    second["id"] = "item-2"
    second["properties"] = dict(second["properties"])
    second["properties"]["datetime"] = "2025-08-15T05:36:24Z"
    responses[f"{BASE_URL}day/catalog.json"] = day
    responses[f"{BASE_URL}day/second.json"] = second
    listing_url = f"{BUCKET_URL}/?list-type=2&prefix=sar-data%2Ftask-data%2Ftask-1%2F&max-keys=1000"
    responses[listing_url] = load_bytes("s3-page-2.xml")
    client = FakeMetadataClient(responses)

    index = CatalogIndexer(
        StacCatalogAdapter(client),
        PublicS3ObjectResolver(client, BUCKET_URL),
        clock=lambda: datetime(2026, 8, 24, tzinfo=UTC),
    ).build(f"{BASE_URL}catalog.json")

    assert index.report.acquisition_count == 2
    assert index.report.resolved_object_count == 2
    assert index.report.large_imagery_downloaded is False
    assert index.report.metadata_only is True
    assert index.report.candidate_time_series_aois[0].item_ids == ("item-1", "item-2")
    assert len(index.acquisitions) == 2


def test_indexer_keeps_network_failures_as_warnings() -> None:
    client = FakeMetadataClient(stac_responses())
    index = CatalogIndexer(
        StacCatalogAdapter(client), PublicS3ObjectResolver(client, BUCKET_URL)
    ).build(f"{BASE_URL}catalog.json")

    assert index.report.acquisition_count == 1
    assert index.report.warning_counts["s3_resolution_failed"] == 1
    assert set(index.report.warning_counts) <= {
        warning.code for warning in index.report.warning_samples
    }
