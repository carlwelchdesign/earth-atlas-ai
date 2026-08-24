"""Catalog indexing orchestration and feasibility reporting."""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Callable
from datetime import UTC, datetime

from echoatlas.processor.catalog.models import (
    Acquisition,
    CandidateAoi,
    CatalogIndex,
    CatalogWarning,
    FeasibilityReport,
)
from echoatlas.processor.catalog.s3 import PublicS3ObjectResolver
from echoatlas.processor.catalog.stac import StacCatalogAdapter


class CatalogIndexer:
    """Combine provider-specific metadata adapters into a provider-neutral index."""

    def __init__(
        self,
        stac: StacCatalogAdapter,
        s3: PublicS3ObjectResolver,
        *,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._stac = stac
        self._s3 = s3
        self._clock = clock or (lambda: datetime.now(UTC))

    def build(
        self,
        root_url: str,
        *,
        max_catalogs: int = 250,
        max_items: int = 250,
        max_s3_pages: int = 10,
    ) -> CatalogIndex:
        traversal = self._stac.traverse(root_url, max_catalogs=max_catalogs, max_items=max_items)
        warnings = list(traversal.warnings)
        acquisitions: list[Acquisition] = []
        listing_pages = 0

        for acquisition in traversal.acquisitions:
            try:
                objects, object_warnings, pages = self._s3.resolve(
                    acquisition, max_pages=max_s3_pages
                )
            except RuntimeError as error:
                objects = ()
                object_warnings = (
                    CatalogWarning(
                        code="s3_resolution_failed",
                        source_url=acquisition.source_url,
                        message=str(error),
                    ),
                )
                pages = 0
            listing_pages += pages
            warnings.extend(object_warnings)
            acquisitions.append(
                acquisition.model_copy(update={"assets": acquisition.assets + objects})
            )

        resolved_objects = [
            asset
            for acquisition in acquisitions
            for asset in acquisition.assets
            if asset.origin == "public-s3"
        ]
        counts = Counter(warning.code for warning in warnings)
        report = FeasibilityReport(
            accessed_at=self._clock(),
            catalog_coverage=traversal.coverage,
            acquisition_count=len(acquisitions),
            resolved_object_count=len(resolved_objects),
            resolved_object_bytes_declared=sum(asset.size_bytes or 0 for asset in resolved_objects),
            s3_listing_pages=listing_pages,
            warning_counts=dict(sorted(counts.items())),
            warning_samples=self._warning_samples(warnings),
            candidate_time_series_aois=self._candidate_aois(acquisitions),
        )
        return CatalogIndex(report=report, acquisitions=tuple(acquisitions))

    @staticmethod
    def _warning_samples(warnings: list[CatalogWarning]) -> tuple[CatalogWarning, ...]:
        """Keep every warning class visible before filling the bounded sample."""
        selected_indices: list[int] = []
        selected_codes: set[str] = set()
        for index, warning in enumerate(warnings):
            if warning.code not in selected_codes:
                selected_indices.append(index)
                selected_codes.add(warning.code)
        for index in range(len(warnings)):
            if len(selected_indices) >= 50:
                break
            if index not in selected_indices:
                selected_indices.append(index)
        return tuple(warnings[index] for index in selected_indices[:50])

    @staticmethod
    def _candidate_aois(acquisitions: list[Acquisition]) -> tuple[CandidateAoi, ...]:
        grouped: dict[str, list[Acquisition]] = defaultdict(list)
        for acquisition in acquisitions:
            west, south, east, north = acquisition.bbox
            center_lon = (west + east) / 2
            center_lat = (south + north) / 2
            grid_key = f"{round(center_lat * 4) / 4:.2f},{round(center_lon * 4) / 4:.2f}"
            grouped[grid_key].append(acquisition)

        candidates: list[CandidateAoi] = []
        for grid_key, group in grouped.items():
            if len(group) < 2:
                continue
            ordered = sorted(group, key=lambda item: item.acquired_at)
            candidates.append(
                CandidateAoi(
                    grid_key=grid_key,
                    bbox=(
                        min(item.bbox[0] for item in group),
                        min(item.bbox[1] for item in group),
                        max(item.bbox[2] for item in group),
                        max(item.bbox[3] for item in group),
                    ),
                    acquisition_count=len(group),
                    first_acquired_at=ordered[0].acquired_at,
                    last_acquired_at=ordered[-1].acquired_at,
                    item_ids=tuple(item.item_id for item in ordered[:20]),
                    products=tuple(
                        sorted({item.product_type for item in group if item.product_type})
                    ),
                    polarizations=tuple(
                        sorted({value for item in group for value in item.polarizations})
                    ),
                )
            )
        return tuple(
            sorted(candidates, key=lambda item: (-item.acquisition_count, item.grid_key))[:25]
        )
