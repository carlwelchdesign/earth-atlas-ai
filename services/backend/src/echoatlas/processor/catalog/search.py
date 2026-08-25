"""Bounded multi-provider catalog-search orchestration."""

from __future__ import annotations

import base64
import hashlib
import json
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Literal, Protocol

from echoatlas.processor.catalog.search_models import (
    CatalogSearchItem,
    CatalogSearchRequest,
    CatalogSearchResponse,
    CatalogSearchWarning,
    ProviderId,
    ProviderSearchPage,
    ProviderSearchReport,
    bbox_intersects,
)


class CatalogSearchError(RuntimeError):
    """A safe catalog-search contract error suitable for an API response."""


class CatalogProviderAdapter(Protocol):
    provider: ProviderId

    def search(self, request: CatalogSearchRequest, *, limit: int) -> ProviderSearchPage: ...


@dataclass(frozen=True)
class _CachedSearch:
    expires_at: datetime
    generated_at: datetime
    items: tuple[CatalogSearchItem, ...]
    providers: tuple[ProviderSearchReport, ...]
    warnings: tuple[CatalogSearchWarning, ...]


class CatalogSearchService:
    """Aggregate provider adapters while preserving partial failures and bounds."""

    def __init__(
        self,
        adapters: Mapping[ProviderId, CatalogProviderAdapter],
        *,
        clock: Callable[[], datetime] | None = None,
        cache_ttl: timedelta = timedelta(minutes=5),
        max_cache_entries: int = 128,
        max_results_per_provider: int = 300,
        max_response_bytes: int = 2_000_000,
    ) -> None:
        self._adapters = dict(adapters)
        self._clock = clock or (lambda: datetime.now(UTC))
        self._cache_ttl = cache_ttl
        self._max_cache_entries = max_cache_entries
        self._max_results_per_provider = max_results_per_provider
        self._max_response_bytes = max_response_bytes
        self._cache: dict[str, _CachedSearch] = {}

    def search(self, request: CatalogSearchRequest) -> CatalogSearchResponse:
        fingerprint = self._fingerprint(request)
        offset = self._decode_cursor(request.cursor, fingerprint)
        now = self._clock()
        self._prune_cache(now)
        cached = self._cache.get(fingerprint)
        cache_status: Literal["hit", "miss"] = "hit"
        if cached is None or cached.expires_at <= now:
            cached = self._run_providers(request, now)
            if len(self._cache) >= self._max_cache_entries:
                oldest = min(self._cache, key=lambda key: self._cache[key].expires_at)
                self._cache.pop(oldest)
            self._cache[fingerprint] = cached
            cache_status = "miss"

        if offset > len(cached.items):
            raise CatalogSearchError("catalog search cursor is outside the sampled result set")
        page = cached.items[offset : offset + request.page_size]
        next_offset = offset + len(page)
        next_cursor = (
            self._encode_cursor(next_offset, fingerprint)
            if next_offset < len(cached.items)
            else None
        )
        failed_or_partial = any(report.status != "complete" for report in cached.providers)
        status: Literal["complete", "empty", "partial"]
        if failed_or_partial:
            status = "partial"
        elif cached.items:
            status = "complete"
        else:
            status = "empty"
        response = CatalogSearchResponse(
            query_id=fingerprint[:16],
            status=status,
            generated_at=cached.generated_at,
            cache=cache_status,
            results=page,
            providers=cached.providers,
            warnings=cached.warnings,
            next_cursor=next_cursor,
            sampled_result_count=len(cached.items),
        )
        if len(response.model_dump_json().encode()) > self._max_response_bytes:
            raise CatalogSearchError("catalog search response exceeds the two-megabyte limit")
        return response

    def _prune_cache(self, now: datetime) -> None:
        expired = tuple(
            fingerprint for fingerprint, entry in self._cache.items() if entry.expires_at <= now
        )
        for fingerprint in expired:
            self._cache.pop(fingerprint)

    def _run_providers(self, request: CatalogSearchRequest, now: datetime) -> _CachedSearch:
        items: list[CatalogSearchItem] = []
        warnings: list[CatalogSearchWarning] = []
        reports: list[ProviderSearchReport] = []
        for provider in request.providers:
            adapter = self._adapters.get(provider)
            if adapter is None:
                warning = CatalogSearchWarning(
                    code="provider_unavailable",
                    provider=provider,
                    retryable=False,
                    message=f"The {provider} catalog adapter is not configured.",
                )
                warnings.append(warning)
                reports.append(
                    ProviderSearchReport(
                        provider=provider,
                        status="failed",
                        result_count=0,
                        has_more=False,
                        warning_count=1,
                    )
                )
                continue
            try:
                provider_page = adapter.search(request, limit=self._max_results_per_provider)
            except (RuntimeError, TypeError, ValueError) as error:
                warning = CatalogSearchWarning(
                    code="provider_request_failed",
                    provider=provider,
                    retryable=True,
                    message=f"The {provider} catalog did not complete: {error}",
                )
                warnings.append(warning)
                reports.append(
                    ProviderSearchReport(
                        provider=provider,
                        status="failed",
                        result_count=0,
                        has_more=False,
                        warning_count=1,
                    )
                )
                continue

            filtered = tuple(
                item for item in provider_page.items if matches_search_request(request, item)
            )
            items.extend(filtered)
            warnings.extend(provider_page.warnings)
            reports.append(
                ProviderSearchReport(
                    provider=provider,
                    status=(
                        "partial"
                        if provider_page.has_more or provider_page.warnings
                        else "complete"
                    ),
                    result_count=len(filtered),
                    has_more=provider_page.has_more,
                    warning_count=len(provider_page.warnings),
                )
            )

        deduplicated = {(item.provider, item.source.item_id): item for item in items}
        ordered = tuple(
            sorted(
                deduplicated.values(),
                key=lambda item: (
                    -item.acquired_at.timestamp(),
                    item.provider,
                    item.source.item_id,
                ),
            )
        )
        return _CachedSearch(
            expires_at=now + self._cache_ttl,
            generated_at=now,
            items=ordered,
            providers=tuple(reports),
            warnings=tuple(warnings),
        )

    @staticmethod
    def _fingerprint(request: CatalogSearchRequest) -> str:
        payload = request.model_dump(mode="json", exclude={"cursor"})
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        return hashlib.sha256(encoded).hexdigest()

    @staticmethod
    def _encode_cursor(offset: int, fingerprint: str) -> str:
        payload = json.dumps(
            {"offset": offset, "query": fingerprint}, separators=(",", ":")
        ).encode()
        return base64.urlsafe_b64encode(payload).decode().rstrip("=")

    @staticmethod
    def _decode_cursor(cursor: str | None, fingerprint: str) -> int:
        if cursor is None:
            return 0
        try:
            padding = "=" * (-len(cursor) % 4)
            value = json.loads(base64.urlsafe_b64decode(f"{cursor}{padding}"))
            offset = value["offset"]
            query = value["query"]
        except (ValueError, TypeError, KeyError, json.JSONDecodeError) as error:
            raise CatalogSearchError("catalog search cursor is malformed") from error
        if not isinstance(offset, int) or offset < 0 or query != fingerprint:
            raise CatalogSearchError("catalog search cursor does not match this query")
        return offset


def matches_search_request(request: CatalogSearchRequest, item: CatalogSearchItem) -> bool:
    """Apply the provider-neutral filters defensively at adapter and service boundaries."""

    if not bbox_intersects(request.aoi.bbox, item.bbox):
        return False
    if not (request.start_at <= item.acquired_at <= request.end_at):
        return False
    if request.product_types and item.product_type not in request.product_types:
        return False
    if request.polarizations and not set(request.polarizations).issubset(item.polarizations):
        return False
    if request.max_resolution_m is not None:
        available = tuple(
            value
            for value in (item.resolution_range_m, item.resolution_azimuth_m)
            if value is not None
        )
        if not available or max(available) > request.max_resolution_m:
            return False
    return True
