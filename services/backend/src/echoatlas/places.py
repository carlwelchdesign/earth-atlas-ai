"""Bounded place search for user-initiated Explore queries."""

from __future__ import annotations

import json
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Protocol, cast
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen

from pydantic import BaseModel, ConfigDict, Field

NOMINATIM_SEARCH_URL = "https://nominatim.openstreetmap.org/search"
NOMINATIM_HOST = "nominatim.openstreetmap.org"
DEFAULT_AOI_OFFSET_DEGREES = 0.075


class PlaceSearchError(RuntimeError):
    """A place query was invalid, unavailable, or returned no match."""


class PlaceSearchResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    label: str = Field(min_length=1, max_length=300)
    bbox: tuple[float, float, float, float]
    provider: str = "OpenStreetMap Nominatim"
    attribution_url: str = "https://www.openstreetmap.org/copyright"


class PlaceSearchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query: str = Field(min_length=2, max_length=120)


@dataclass(frozen=True)
class NominatimPlace:
    label: str
    latitude: float
    longitude: float


class PlaceProvider(Protocol):
    def search(self, query: str) -> NominatimPlace | None: ...


class NominatimPlaceProvider:
    """Small, allowlisted Nominatim client for explicit end-user searches."""

    def __init__(
        self,
        *,
        search_url: str = NOMINATIM_SEARCH_URL,
        timeout_seconds: float = 10,
        max_response_bytes: int = 256_000,
        opener: Callable[..., Any] = urlopen,
    ) -> None:
        parsed = urlparse(search_url)
        if parsed.scheme != "https" or parsed.hostname != NOMINATIM_HOST:
            raise ValueError("Nominatim search URL must use the allowlisted HTTPS host")
        self._search_url = search_url
        self._timeout_seconds = timeout_seconds
        self._max_response_bytes = max_response_bytes
        self._opener = opener

    def search(self, query: str) -> NominatimPlace | None:
        url = f"{self._search_url}?{urlencode({'q': query, 'format': 'jsonv2', 'limit': 1})}"
        request = Request(
            url,
            headers={
                "Accept": "application/json",
                "User-Agent": (
                    "EchoAtlas/0.1 place-search "
                    "(+https://github.com/carlwelchdesign/earth-atlas-ai)"
                ),
            },
        )
        try:
            with self._opener(request, timeout=self._timeout_seconds) as response:
                final_url = response.geturl()
                if urlparse(final_url).hostname != NOMINATIM_HOST:
                    raise PlaceSearchError("Place-search redirect left the host allowlist.")
                length = response.headers.get("Content-Length")
                if length is not None and int(length) > self._max_response_bytes:
                    raise PlaceSearchError("Place-search response exceeded the size limit.")
                payload = cast(bytes, response.read(self._max_response_bytes + 1))
        except PlaceSearchError:
            raise
        except (HTTPError, URLError, OSError, TimeoutError, ValueError) as error:
            raise PlaceSearchError("The configured place-search service is unavailable.") from error
        if len(payload) > self._max_response_bytes:
            raise PlaceSearchError("Place-search response exceeded the size limit.")
        try:
            document: Any = json.loads(payload)
        except (json.JSONDecodeError, UnicodeDecodeError) as error:
            raise PlaceSearchError("The place-search service returned invalid data.") from error
        if not isinstance(document, list):
            raise PlaceSearchError("The place-search service returned invalid data.")
        if not document:
            return None
        first = document[0]
        if not isinstance(first, dict):
            raise PlaceSearchError("The place-search service returned invalid data.")
        try:
            label = first["display_name"]
            latitude = float(first["lat"])
            longitude = float(first["lon"])
        except (KeyError, TypeError, ValueError) as error:
            raise PlaceSearchError("The place-search service returned invalid data.") from error
        if not isinstance(label, str) or not label.strip():
            raise PlaceSearchError("The place-search service returned invalid data.")
        if not -90 <= latitude <= 90 or not -180 <= longitude <= 180:
            raise PlaceSearchError("The place-search service returned invalid coordinates.")
        return NominatimPlace(label=label.strip(), latitude=latitude, longitude=longitude)


class PlaceSearchService:
    """Rate-limited, bounded, in-memory-cached place resolver."""

    def __init__(
        self,
        provider: PlaceProvider,
        *,
        minimum_interval_seconds: float = 1.1,
        max_cache_entries: int = 128,
        monotonic: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self._provider = provider
        self._minimum_interval_seconds = minimum_interval_seconds
        self._max_cache_entries = max_cache_entries
        self._monotonic = monotonic
        self._sleep = sleep
        self._lock = threading.Lock()
        self._last_request_at: float | None = None
        self._cache: dict[str, PlaceSearchResponse] = {}

    def resolve(self, query: str) -> PlaceSearchResponse:
        normalized = " ".join(query.split())
        if len(normalized) < 2 or len(normalized) > 120:
            raise PlaceSearchError("Enter a place name between 2 and 120 characters.")
        cache_key = normalized.casefold()
        with self._lock:
            cached = self._cache.get(cache_key)
            if cached is not None:
                return cached
            now = self._monotonic()
            if self._last_request_at is not None:
                remaining = self._minimum_interval_seconds - (now - self._last_request_at)
                if remaining > 0:
                    self._sleep(remaining)
            place = self._provider.search(normalized)
            self._last_request_at = self._monotonic()
            if place is None:
                raise PlaceSearchError("No place match was found. Try a more specific name.")
            response = PlaceSearchResponse(
                label=place.label,
                bbox=_bounded_aoi(place.latitude, place.longitude),
            )
            if len(self._cache) >= self._max_cache_entries:
                self._cache.pop(next(iter(self._cache)))
            self._cache[cache_key] = response
            return response


def _bounded_aoi(latitude: float, longitude: float) -> tuple[float, float, float, float]:
    offset = DEFAULT_AOI_OFFSET_DEGREES
    return (
        round(max(-180.0, longitude - offset), 6),
        round(max(-90.0, latitude - offset), 6),
        round(min(180.0, longitude + offset), 6),
        round(min(90.0, latitude + offset), 6),
    )


def build_default_place_search_service() -> PlaceSearchService:
    return PlaceSearchService(NominatimPlaceProvider())
