"""STAC traversal adapter for Umbra acquisition metadata."""

from __future__ import annotations

from collections import deque
from collections.abc import Mapping
from datetime import datetime
from typing import Any
from urllib.parse import urljoin, urlparse

from pydantic import ValidationError

from echoatlas.processor.catalog.http import CatalogAccessError, MetadataClient
from echoatlas.processor.catalog.models import (
    Acquisition,
    CatalogAsset,
    CatalogCoverage,
    CatalogWarning,
    TraversalResult,
)


class StacCatalogAdapter:
    """Traverse bounded STAC links without reading any linked raster asset."""

    def __init__(self, client: MetadataClient) -> None:
        self._client = client

    def traverse(
        self,
        root_url: str,
        *,
        max_catalogs: int = 250,
        max_items: int = 250,
        include_assets: bool = True,
    ) -> TraversalResult:
        catalog_queue = deque([root_url])
        item_queue: deque[str] = deque()
        visited_catalogs: set[str] = set()
        visited_items: set[str] = set()
        acquisitions: list[Acquisition] = []
        warnings: list[CatalogWarning] = []
        item_links_seen = 0
        items_skipped = 0

        while catalog_queue and len(visited_catalogs) < max_catalogs:
            catalog_url = catalog_queue.popleft()
            if catalog_url in visited_catalogs:
                continue
            try:
                catalog = self._client.get_json(catalog_url)
            except CatalogAccessError as error:
                warnings.append(self._warning("catalog_access_failed", catalog_url, str(error)))
                continue
            visited_catalogs.add(catalog_url)
            links = catalog.get("links")
            if not isinstance(links, list):
                warnings.append(
                    self._warning("missing_links", catalog_url, "STAC catalog has no links array")
                )
                continue
            for link in links:
                if not isinstance(link, dict) or link.get("rel") not in {"child", "item"}:
                    continue
                resolved = self._resolve_link(catalog_url, link.get("href"))
                if resolved is None:
                    warnings.append(
                        self._warning(
                            "malformed_link", catalog_url, "child or item link has an invalid href"
                        )
                    )
                    continue
                if link["rel"] == "child":
                    if resolved not in visited_catalogs:
                        catalog_queue.append(resolved)
                else:
                    item_links_seen += 1
                    if resolved not in visited_items:
                        item_queue.append(resolved)

        while item_queue and len(acquisitions) < max_items:
            item_url = item_queue.popleft()
            if item_url in visited_items:
                continue
            visited_items.add(item_url)
            try:
                item = self._client.get_json(item_url)
                acquisition, item_warnings = self.normalize_item(
                    item_url, item, include_assets=include_assets
                )
            except (CatalogAccessError, ValidationError, ValueError, TypeError) as error:
                items_skipped += 1
                warnings.append(self._warning("item_invalid", item_url, str(error)))
                continue
            acquisitions.append(acquisition)
            warnings.extend(item_warnings)

        return TraversalResult(
            acquisitions=tuple(acquisitions),
            warnings=tuple(warnings),
            coverage=CatalogCoverage(
                root_url=root_url,
                catalogs_visited=len(visited_catalogs),
                item_links_seen=item_links_seen,
                items_indexed=len(acquisitions),
                items_skipped=items_skipped,
                catalog_limit_reached=bool(catalog_queue),
                item_limit_reached=bool(item_queue),
            ),
        )

    def normalize_item(
        self,
        item_url: str,
        item: Mapping[str, Any],
        *,
        include_assets: bool = True,
    ) -> tuple[Acquisition, list[CatalogWarning]]:
        warnings: list[CatalogWarning] = []
        properties = self._required_mapping(item, "properties")
        geometry = self._required_mapping(item, "geometry")
        raw_bbox = item.get("bbox")
        if not isinstance(raw_bbox, list) or len(raw_bbox) < 4:
            raise ValueError("item bbox is missing or malformed")
        bbox = (
            float(raw_bbox[0]),
            float(raw_bbox[1]),
            float(raw_bbox[2]),
            float(raw_bbox[3]),
        )
        item_id = item.get("id")
        if not isinstance(item_id, str) or not item_id.strip():
            raise ValueError("item id is missing")
        acquired_at = properties.get("datetime") or properties.get("start_datetime")
        if not isinstance(acquired_at, str):
            raise ValueError("item acquisition time is missing")

        assets: list[CatalogAsset] = []
        raw_assets = item.get("assets", {})
        if not isinstance(raw_assets, dict):
            raise ValueError("item assets must be an object")
        if include_assets:
            for name, raw_asset in raw_assets.items():
                if not isinstance(name, str) or not isinstance(raw_asset, dict):
                    warnings.append(
                        self._warning("malformed_asset", item_url, "asset is malformed")
                    )
                    continue
                raw_href = raw_asset.get("href")
                href = self._resolve_link(item_url, raw_href) if raw_href else None
                if href is None:
                    warnings.append(
                        self._warning(
                            "empty_asset_href", item_url, f"asset {name!r} has no usable href"
                        )
                    )
                roles = raw_asset.get("roles")
                assets.append(
                    CatalogAsset(
                        name=name,
                        href=href,
                        origin="stac",
                        media_type=self._optional_string(raw_asset.get("type")),
                        title=self._optional_string(raw_asset.get("title")),
                        roles=tuple(role for role in roles if isinstance(role, str))
                        if isinstance(roles, list)
                        else (),
                    )
                )

        polarizations = properties.get("sar:polarizations")
        return (
            Acquisition(
                item_id=item_id,
                acquired_at=datetime.fromisoformat(acquired_at.replace("Z", "+00:00")),
                bbox=bbox,
                geometry=dict(geometry),
                product_type=self._optional_string(
                    properties.get("sar:product_type") or properties.get("product:type")
                ),
                polarizations=tuple(value for value in polarizations if isinstance(value, str))
                if isinstance(polarizations, list)
                else (),
                resolution_range_m=self._optional_float(
                    properties.get("sar:resolution_range")
                    or properties.get("sar:pixel_spacing_range")
                ),
                resolution_azimuth_m=self._optional_float(
                    properties.get("sar:resolution_azimuth")
                    or properties.get("sar:pixel_spacing_azimuth")
                ),
                platform=self._optional_string(properties.get("platform")),
                observation_direction=self._optional_string(
                    properties.get("sar:observation_direction")
                ),
                orbit_state=self._optional_string(properties.get("sat:orbit_state")),
                incidence_angle_deg=self._optional_float(properties.get("view:incidence_angle")),
                grazing_angle_deg=self._optional_float(
                    properties.get("umbra:grazing_angle_degrees")
                ),
                license=self._optional_string(properties.get("license")) or "unknown",
                source_url=item_url,
                provider_task_id=self._optional_string(properties.get("umbra:task_id")),
                assets=tuple(assets),
                source_document=dict(item),
            ),
            warnings,
        )

    @staticmethod
    def _resolve_link(base_url: str, href: object) -> str | None:
        if not isinstance(href, str) or not href.strip():
            return None
        resolved = urljoin(base_url, href.strip())
        parsed = urlparse(resolved)
        return resolved if parsed.scheme == "https" and parsed.hostname else None

    @staticmethod
    def _required_mapping(document: Mapping[str, Any], key: str) -> Mapping[str, Any]:
        value = document.get(key)
        if not isinstance(value, dict):
            raise ValueError(f"item {key} is missing or malformed")
        return value

    @staticmethod
    def _optional_string(value: object) -> str | None:
        return value if isinstance(value, str) and value else None

    @staticmethod
    def _optional_float(value: object) -> float | None:
        return float(value) if isinstance(value, (int, float)) else None

    @staticmethod
    def _warning(code: str, source_url: str, message: str) -> CatalogWarning:
        return CatalogWarning(code=code, source_url=source_url, message=message)
