"""Bounded HTTPS metadata client used by catalog adapters."""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any, Protocol, cast
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


class CatalogAccessError(RuntimeError):
    """Remote catalog metadata could not be safely retrieved."""


class MetadataClient(Protocol):
    def get_bytes(self, url: str) -> bytes: ...

    def get_json(self, url: str) -> Mapping[str, Any]: ...


class SafeMetadataClient:
    """Fetch small metadata documents from explicitly allowed HTTPS hosts."""

    def __init__(
        self,
        *,
        allowed_hosts: frozenset[str],
        max_response_bytes: int = 5_000_000,
        timeout_seconds: float = 20,
    ) -> None:
        self._allowed_hosts = allowed_hosts
        self._max_response_bytes = max_response_bytes
        self._timeout_seconds = timeout_seconds

    def get_bytes(self, url: str) -> bytes:
        parsed = urlparse(url)
        if parsed.scheme != "https" or parsed.hostname not in self._allowed_hosts:
            raise CatalogAccessError(f"remote URL is not allowlisted: {url}")

        request = Request(
            url,
            headers={
                "Accept": "application/json, application/geo+json, application/xml, text/xml",
                "User-Agent": "EchoAtlas/0.1 catalog-metadata-indexer",
            },
        )
        try:
            with urlopen(request, timeout=self._timeout_seconds) as response:  # noqa: S310
                length = response.headers.get("Content-Length")
                if length is not None and int(length) > self._max_response_bytes:
                    raise CatalogAccessError(f"metadata response exceeds size limit: {url}")
                payload = cast(bytes, response.read(self._max_response_bytes + 1))
        except (HTTPError, URLError, TimeoutError, ValueError) as error:
            raise CatalogAccessError(f"metadata request failed for {url}: {error}") from error

        if len(payload) > self._max_response_bytes:
            raise CatalogAccessError(f"metadata response exceeds size limit: {url}")
        return payload

    def get_json(self, url: str) -> Mapping[str, Any]:
        try:
            document = json.loads(self.get_bytes(url))
        except (json.JSONDecodeError, UnicodeDecodeError) as error:
            raise CatalogAccessError(f"invalid JSON metadata at {url}: {error}") from error
        if not isinstance(document, dict):
            raise CatalogAccessError(f"JSON metadata is not an object: {url}")
        return cast(Mapping[str, Any], document)
