"""Bounded Sentinel-2 discovery and rendering for the prepared Nepal case."""

from __future__ import annotations

import io
import re
from collections.abc import Mapping
from datetime import date, datetime, timedelta
from typing import Any
from urllib.parse import urlencode, urlparse

import numpy as np
import rasterio  # type: ignore[import-untyped]
from PIL import Image
from pydantic import BaseModel, ConfigDict
from rasterio.transform import from_bounds  # type: ignore[import-untyped]
from rasterio.warp import Resampling, reproject, transform  # type: ignore[import-untyped]

from echoatlas.processor.catalog.http import (
    CatalogAccessError,
    MetadataClient,
    SafeMetadataClient,
)

NEPAL_AOI = (85.3, 28.08, 85.42, 28.28)
NEPAL_EVENT_DATE = date(2026, 8, 26)
NEPAL_WINDOW_START = date(2026, 7, 27)
NEPAL_WINDOW_END = date(2026, 9, 24)
MAX_DATE_RANGE_DAYS = 60
EARTH_SEARCH_HOST = "earth-search.aws.element84.com"
SENTINEL_COG_HOST = "sentinel-cogs.s3.us-west-2.amazonaws.com"
SENTINEL_COLLECTION = "sentinel-2-l2a"
ITEM_ID = re.compile(r"^S2[ABC]_45RUM_2026(?:07|08|09)\d{2}_[0-9]+_L2A$")


class NepalImageryError(RuntimeError):
    """The bounded Nepal imagery request could not be completed safely."""


class NepalAcquisition(BaseModel):
    model_config = ConfigDict(frozen=True)

    item_id: str
    product_id: str
    acquired_at: datetime
    source_url: str
    image_url: str
    cloud_cover_percent: float
    cloud_shadow_percent: float
    nodata_percent: float
    crs: str
    resolution_metres: float


class NepalAcquisitionList(BaseModel):
    model_config = ConfigDict(frozen=True)

    start_date: date
    end_date: date
    maximum_range_days: int = MAX_DATE_RANGE_DAYS
    acquisitions: tuple[NepalAcquisition, ...]


def validate_date_range(start_date: date, end_date: date) -> None:
    if start_date >= end_date:
        raise NepalImageryError("The imagery start date must precede the end date.")
    if end_date - start_date >= timedelta(days=MAX_DATE_RANGE_DAYS):
        raise NepalImageryError("The imagery date range cannot exceed 60 days.")
    if start_date < NEPAL_WINDOW_START or end_date > NEPAL_WINDOW_END:
        raise NepalImageryError("The Nepal case is bounded to 27 July through 24 September 2026.")


def _mapping(value: object, path: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise NepalImageryError(f"Earth Search returned invalid {path} metadata.")
    return value


def _number(value: object, path: str) -> float:
    if not isinstance(value, int | float):
        raise NepalImageryError(f"Earth Search omitted numeric {path} metadata.")
    return float(value)


def _text(value: object, path: str) -> str:
    if not isinstance(value, str) or not value:
        raise NepalImageryError(f"Earth Search omitted {path} metadata.")
    return value


class NepalImageryService:
    """Read one bounded public catalog and render its georeferenced visual COGs."""

    def __init__(self, metadata: MetadataClient | None = None) -> None:
        self._metadata = metadata or SafeMetadataClient(
            allowed_hosts=frozenset({EARTH_SEARCH_HOST}),
            max_response_bytes=5_000_000,
            timeout_seconds=20,
        )
        self._item_cache: dict[str, Mapping[str, Any]] = {}
        self._image_cache: dict[str, bytes] = {}

    def list_acquisitions(self, start_date: date, end_date: date) -> NepalAcquisitionList:
        validate_date_range(start_date, end_date)
        west, south, east, north = NEPAL_AOI
        query = urlencode(
            {
                "collections": SENTINEL_COLLECTION,
                "bbox": f"{west},{south},{east},{north}",
                "datetime": (
                    f"{start_date.isoformat()}T00:00:00Z/{end_date.isoformat()}T23:59:59Z"
                ),
                "limit": 100,
            }
        )
        try:
            document = self._metadata.get_json(f"https://{EARTH_SEARCH_HOST}/v1/search?{query}")
        except CatalogAccessError as error:
            raise NepalImageryError("Sentinel-2 acquisition metadata is unavailable.") from error
        features = document.get("features")
        if not isinstance(features, list):
            raise NepalImageryError("Earth Search returned an invalid feature collection.")
        acquisitions = tuple(
            sorted(
                (self._parse_acquisition(feature) for feature in features),
                key=lambda acquisition: acquisition.acquired_at,
            )
        )
        return NepalAcquisitionList(
            start_date=start_date,
            end_date=end_date,
            acquisitions=acquisitions,
        )

    def _parse_acquisition(self, feature: object) -> NepalAcquisition:
        item = _mapping(feature, "item")
        item_id = _text(item.get("id"), "item ID")
        if not ITEM_ID.fullmatch(item_id):
            raise NepalImageryError("Earth Search returned an item outside the Nepal case grid.")
        properties = _mapping(item.get("properties"), "properties")
        assets = _mapping(item.get("assets"), "assets")
        visual = _mapping(assets.get("visual"), "visual asset")
        visual_url = _text(visual.get("href"), "visual asset URL")
        parsed_visual = urlparse(visual_url)
        if parsed_visual.scheme != "https" or parsed_visual.hostname != SENTINEL_COG_HOST:
            raise NepalImageryError("The visual asset left the approved Sentinel-2 host.")
        acquired_at = datetime.fromisoformat(
            _text(properties.get("datetime"), "acquisition timestamp").replace("Z", "+00:00")
        )
        product_id = _text(properties.get("s2:product_uri"), "product identity")
        epsg = int(_number(properties.get("proj:epsg"), "source CRS"))
        return NepalAcquisition(
            item_id=item_id,
            product_id=product_id,
            acquired_at=acquired_at,
            source_url=(
                f"https://{EARTH_SEARCH_HOST}/v1/collections/{SENTINEL_COLLECTION}/items/{item_id}"
            ),
            image_url=f"/generated-nepal/acquisitions/{item_id}.png",
            cloud_cover_percent=_number(properties.get("eo:cloud_cover"), "cloud cover"),
            cloud_shadow_percent=_number(
                properties.get("s2:cloud_shadow_percentage"), "cloud shadow"
            ),
            nodata_percent=_number(properties.get("s2:nodata_pixel_percentage"), "nodata"),
            crs=f"EPSG:{epsg}",
            resolution_metres=_number(visual.get("gsd"), "visual resolution"),
        )

    def _item(self, item_id: str) -> Mapping[str, Any]:
        if not ITEM_ID.fullmatch(item_id):
            raise NepalImageryError("The Sentinel-2 item is outside the bounded Nepal case.")
        url = f"https://{EARTH_SEARCH_HOST}/v1/collections/{SENTINEL_COLLECTION}/items/{item_id}"
        cached = self._item_cache.get(item_id)
        if cached is not None:
            return cached
        try:
            item = self._metadata.get_json(url)
        except CatalogAccessError as error:
            raise NepalImageryError("The selected Sentinel-2 item is unavailable.") from error
        if len(self._item_cache) >= 50:
            self._item_cache.pop(next(iter(self._item_cache)))
        self._item_cache[item_id] = item
        return item

    def render_png(self, item_id: str) -> bytes:
        cached = self._image_cache.get(item_id)
        if cached is not None:
            return cached
        acquisition = self._parse_acquisition(self._item(item_id))
        item_date = acquisition.acquired_at.date()
        if item_date < NEPAL_WINDOW_START or item_date > NEPAL_WINDOW_END:
            raise NepalImageryError("The Sentinel-2 item is outside the 60-day Nepal window.")
        item = self._item(item_id)
        assets = _mapping(item.get("assets"), "assets")
        visual = _mapping(assets.get("visual"), "visual asset")
        visual_url = _text(visual.get("href"), "visual asset URL")
        rendered = _render_aoi_png(visual_url)
        if len(self._image_cache) >= 12:
            self._image_cache.pop(next(iter(self._image_cache)))
        self._image_cache[item_id] = rendered
        return rendered


def _render_aoi_png(source_url: str) -> bytes:
    width, height = 720, 960
    west, south, east, north = NEPAL_AOI
    left, bottom = transform("EPSG:4326", "EPSG:3857", [west], [south])
    right, top = transform("EPSG:4326", "EPSG:3857", [east], [north])
    destination_transform = from_bounds(left[0], bottom[0], right[0], top[0], width, height)
    rgb = np.zeros((3, height, width), dtype=np.uint8)
    try:
        with (
            rasterio.Env(
                GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR",
                GDAL_HTTP_MULTIRANGE="YES",
                GDAL_HTTP_MERGE_CONSECUTIVE_RANGES="YES",
            ),
            rasterio.open(source_url) as dataset,
        ):
            for band in range(1, 4):
                reproject(
                    source=rasterio.band(dataset, band),
                    destination=rgb[band - 1],
                    src_transform=dataset.transform,
                    src_crs=dataset.crs,
                    src_nodata=0,
                    dst_transform=destination_transform,
                    dst_crs="EPSG:3857",
                    dst_nodata=0,
                    resampling=Resampling.bilinear,
                )
    except rasterio.errors.RasterioError as error:
        raise NepalImageryError(
            "The selected georeferenced image could not be rendered."
        ) from error
    alpha = np.where(np.any(rgb != 0, axis=0), 255, 0).astype(np.uint8)
    image = Image.fromarray(np.dstack((rgb[0], rgb[1], rgb[2], alpha)), mode="RGBA")
    output = io.BytesIO()
    image.save(output, format="PNG", optimize=True)
    return output.getvalue()
