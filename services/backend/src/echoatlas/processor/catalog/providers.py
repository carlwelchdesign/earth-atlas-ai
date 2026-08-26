"""Provider adapters for bounded global catalog discovery."""

from __future__ import annotations

from collections.abc import Mapping
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Any
from urllib.parse import urlencode, urlparse

from pydantic import ValidationError

from echoatlas.processor.catalog.http import CatalogAccessError, MetadataClient, SafeMetadataClient
from echoatlas.processor.catalog.models import Acquisition, CatalogWarning, TraversalResult
from echoatlas.processor.catalog.search import (
    CatalogProviderAdapter,
    CatalogSearchService,
    matches_search_request,
)
from echoatlas.processor.catalog.search_models import (
    CatalogLicense,
    CatalogSearchItem,
    CatalogSearchRequest,
    CatalogSearchWarning,
    CatalogSourceIdentity,
    GeoJsonPolygon,
    ProviderId,
    ProviderSearchPage,
)
from echoatlas.processor.catalog.stac import StacCatalogAdapter

UMBRA_ROOT_URL = "https://umbra-open-data-catalog.s3.us-west-2.amazonaws.com/stac/catalog.json"
SENTINEL_1_SEARCH_URL = "https://stac.dataspace.copernicus.eu/v1/search"


class UmbraCatalogSearchAdapter:
    """Search a bounded static STAC traversal using provider-reported footprints."""

    provider: ProviderId = "umbra"

    def __init__(
        self,
        stac: StacCatalogAdapter,
        *,
        root_url: str = UMBRA_ROOT_URL,
        max_catalogs: int = 500,
        max_items: int = 500,
    ) -> None:
        self._stac = stac
        self._root_url = root_url
        self._max_catalogs = max_catalogs
        self._max_items = max_items

    def search(self, request: CatalogSearchRequest, *, limit: int) -> ProviderSearchPage:
        roots = self._search_roots(request)
        acquisitions: dict[str, Acquisition] = {}
        warnings: tuple[CatalogSearchWarning, ...] = ()
        item_budgets = _distribute_budget(min(self._max_items, limit), len(roots))
        catalog_budgets = _distribute_budget(self._max_catalogs, len(roots))
        arguments = tuple(zip(roots, catalog_budgets, item_budgets, strict=True))
        with ThreadPoolExecutor(
            max_workers=min(4, len(arguments)), thread_name_prefix="echoatlas-umbra"
        ) as executor:
            traversals = tuple(executor.map(self._traverse_root, arguments))
        has_more = False
        for traversal in traversals:
            warnings += tuple(self._warning(warning) for warning in traversal.warnings)
            acquisitions.update(
                (acquisition.item_id, acquisition) for acquisition in traversal.acquisitions
            )
            has_more = has_more or traversal.coverage.catalog_limit_reached
            has_more = has_more or traversal.coverage.item_limit_reached
        if has_more:
            warnings += (
                CatalogSearchWarning(
                    code="umbra_sample_limit_reached",
                    provider="umbra",
                    retryable=False,
                    message=(
                        "Umbra uses a static public STAC hierarchy. The bounded traversal "
                        "stopped at its configured catalog or item limit, so these results "
                        "are a provider-reported sample rather than exhaustive coverage."
                    ),
                ),
            )
        items: list[CatalogSearchItem] = []
        for acquisition in acquisitions.values():
            item = self._item(acquisition)
            if matches_search_request(request, item):
                items.append(item)
        return ProviderSearchPage(items=tuple(items), warnings=warnings, has_more=has_more)

    def _traverse_root(self, arguments: tuple[str, int, int]) -> TraversalResult:
        root, max_catalogs, max_items = arguments
        return self._stac.traverse(
            root,
            max_catalogs=max_catalogs,
            max_items=max_items,
            include_assets=False,
        )

    def _search_roots(self, request: CatalogSearchRequest) -> tuple[str, ...]:
        if self._root_url != UMBRA_ROOT_URL:
            return (self._root_url,)
        months: list[str] = []
        cursor = datetime(request.start_at.year, request.start_at.month, 1)
        end = datetime(request.end_at.year, request.end_at.month, 1)
        while cursor <= end:
            months.append(
                "https://umbra-open-data-catalog.s3.us-west-2.amazonaws.com/"
                f"stac/{cursor.year:04d}/{cursor.year:04d}-{cursor.month:02d}/catalog.json"
            )
            cursor = datetime(
                cursor.year + (1 if cursor.month == 12 else 0),
                1 if cursor.month == 12 else cursor.month + 1,
                1,
            )
        return tuple(months)

    @staticmethod
    def _item(acquisition: Acquisition) -> CatalogSearchItem:
        return _search_item(
            provider="umbra",
            collection="umbra-open-data",
            acquisition=acquisition,
            license=CatalogLicense(
                label="CC-BY-4.0",
                url="https://creativecommons.org/licenses/by/4.0/",
            ),
        )

    @staticmethod
    def _warning(warning: CatalogWarning) -> CatalogSearchWarning:
        return CatalogSearchWarning(
            code=warning.code,
            provider="umbra",
            retryable=warning.code in {"catalog_access_failed", "item_invalid"},
            message=warning.message,
        )


class Sentinel1CatalogSearchAdapter:
    """Query the official Copernicus Data Space Sentinel-1 GRD STAC collection."""

    provider: ProviderId = "sentinel-1"

    def __init__(
        self,
        client: MetadataClient,
        *,
        search_url: str = SENTINEL_1_SEARCH_URL,
        collection: str = "sentinel-1-grd",
        max_pages: int = 3,
        page_size: int = 100,
    ) -> None:
        self._client = client
        self._search_url = search_url
        self._collection = collection
        self._max_pages = max_pages
        self._page_size = page_size
        self._normalizer = StacCatalogAdapter(client)

    def search(self, request: CatalogSearchRequest, *, limit: int) -> ProviderSearchPage:
        next_url: str | None = self._initial_url(request, min(limit, self._page_size))
        items: list[CatalogSearchItem] = []
        warnings: list[CatalogSearchWarning] = []
        pages = 0
        while next_url is not None and pages < self._max_pages and len(items) < limit:
            document = self._client.get_json(next_url)
            pages += 1
            raw_features = document.get("features")
            if not isinstance(raw_features, list):
                raise CatalogAccessError("Sentinel-1 STAC response has no features array")
            for raw_feature in raw_features:
                if len(items) >= limit:
                    break
                if not isinstance(raw_feature, dict):
                    warnings.append(
                        CatalogSearchWarning(
                            code="sentinel_item_invalid",
                            provider="sentinel-1",
                            retryable=False,
                            message="Sentinel-1 STAC returned a non-object feature.",
                        )
                    )
                    continue
                try:
                    source_url = self._self_url(raw_feature)
                    acquisition, item_warnings = self._normalizer.normalize_item(
                        source_url, raw_feature, include_assets=False
                    )
                except (ValidationError, ValueError, TypeError) as error:
                    warnings.append(
                        CatalogSearchWarning(
                            code="sentinel_item_invalid",
                            provider="sentinel-1",
                            retryable=False,
                            message=f"Sentinel-1 STAC item was rejected: {error}",
                        )
                    )
                    continue
                items.append(
                    _search_item(
                        provider="sentinel-1",
                        collection=self._collection,
                        acquisition=acquisition,
                        license=CatalogLicense(
                            label="Copernicus Sentinel Data Legal Notice",
                            url=(
                                "https://sentinel.esa.int/documents/247904/690755/"
                                "Sentinel_Data_Legal_Notice"
                            ),
                        ),
                    )
                )
                warnings.extend(
                    CatalogSearchWarning(
                        code=warning.code,
                        provider="sentinel-1",
                        retryable=False,
                        message=warning.message,
                    )
                    for warning in item_warnings
                )
            next_url = self._next_url(document)

        has_more = next_url is not None
        if has_more:
            warnings.append(
                CatalogSearchWarning(
                    code="sentinel_page_limit_reached",
                    provider="sentinel-1",
                    retryable=False,
                    message=(
                        "Sentinel-1 returned more matching acquisitions than the bounded "
                        f"{self._max_pages}-page sample. Refine the AOI or time range."
                    ),
                )
            )
        return ProviderSearchPage(items=tuple(items), warnings=tuple(warnings), has_more=has_more)

    def _initial_url(self, request: CatalogSearchRequest, limit: int) -> str:
        bbox = ",".join(str(value) for value in request.aoi.bbox)
        interval = (
            f"{request.start_at.isoformat().replace('+00:00', 'Z')}/"
            f"{request.end_at.isoformat().replace('+00:00', 'Z')}"
        )
        query = urlencode(
            {
                "bbox": bbox,
                "datetime": interval,
                "collections": self._collection,
                "limit": limit,
            }
        )
        return f"{self._search_url}?{query}"

    @staticmethod
    def _self_url(feature: Mapping[str, Any]) -> str:
        links = feature.get("links")
        if isinstance(links, list):
            for link in links:
                if isinstance(link, dict) and link.get("rel") == "self":
                    href = link.get("href")
                    if isinstance(href, str) and _is_https_url(href):
                        return href
        raise ValueError("Sentinel-1 STAC item has no valid self link")

    @staticmethod
    def _next_url(document: Mapping[str, Any]) -> str | None:
        links = document.get("links")
        if not isinstance(links, list):
            return None
        for link in links:
            if not isinstance(link, dict) or link.get("rel") != "next":
                continue
            href = link.get("href")
            if isinstance(href, str) and _is_https_url(href):
                return href
            raise CatalogAccessError("Sentinel-1 STAC next link is invalid")
        return None


def build_default_catalog_search_service(
    *,
    umbra_root_url: str = UMBRA_ROOT_URL,
    umbra_max_catalogs: int = 500,
    umbra_max_items: int = 500,
) -> CatalogSearchService:
    """Construct the production metadata-only search boundary."""

    client = SafeMetadataClient(
        allowed_hosts=frozenset(
            {
                "stac.dataspace.copernicus.eu",
                "umbra-open-data-catalog.s3.us-west-2.amazonaws.com",
            }
        ),
        max_response_bytes=5_000_000,
        timeout_seconds=20,
    )
    adapters: dict[ProviderId, CatalogProviderAdapter] = {
        "umbra": UmbraCatalogSearchAdapter(
            StacCatalogAdapter(client),
            root_url=umbra_root_url,
            max_catalogs=umbra_max_catalogs,
            max_items=umbra_max_items,
        ),
        "sentinel-1": Sentinel1CatalogSearchAdapter(client),
    }
    return CatalogSearchService(adapters)


def _search_item(
    *,
    provider: ProviderId,
    collection: str,
    acquisition: Acquisition,
    license: CatalogLicense,
) -> CatalogSearchItem:
    geometry = _two_dimensional_polygon(acquisition.geometry)
    return CatalogSearchItem(
        provider=provider,
        acquired_at=acquisition.acquired_at,
        bbox=acquisition.bbox,
        footprint=geometry,
        product_type=acquisition.product_type,
        polarizations=acquisition.polarizations,
        resolution_range_m=acquisition.resolution_range_m,
        resolution_azimuth_m=acquisition.resolution_azimuth_m,
        platform=acquisition.platform,
        observation_direction=acquisition.observation_direction,
        orbit_state=acquisition.orbit_state,
        incidence_angle_deg=acquisition.incidence_angle_deg,
        license=license,
        source=CatalogSourceIdentity(
            item_id=acquisition.item_id,
            collection=collection,
            href=acquisition.source_url,
        ),
    )


def _distribute_budget(total: int, buckets: int) -> tuple[int, ...]:
    quotient, remainder = divmod(total, buckets)
    return tuple(quotient + (1 if index < remainder else 0) for index in range(buckets))


def _is_https_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme == "https" and parsed.hostname is not None


def _two_dimensional_polygon(geometry: Mapping[str, Any]) -> GeoJsonPolygon:
    if geometry.get("type") != "Polygon":
        raise ValueError("catalog search currently supports Polygon footprints only")
    raw_rings = geometry.get("coordinates")
    if not isinstance(raw_rings, list):
        raise ValueError("catalog footprint has no polygon coordinates")
    rings: list[tuple[tuple[float, float], ...]] = []
    for raw_ring in raw_rings:
        if not isinstance(raw_ring, list):
            raise ValueError("catalog footprint ring is malformed")
        ring: list[tuple[float, float]] = []
        for raw_position in raw_ring:
            if not isinstance(raw_position, list) or len(raw_position) < 2:
                raise ValueError("catalog footprint position is malformed")
            longitude, latitude = raw_position[:2]
            if not isinstance(longitude, (int, float)) or not isinstance(latitude, (int, float)):
                raise ValueError("catalog footprint position must be numeric")
            ring.append((float(longitude), float(latitude)))
        rings.append(tuple(ring))
    return GeoJsonPolygon(coordinates=tuple(rings))
