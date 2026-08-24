"""Resumable, bounded source download with verified immutable cache promotion."""

from __future__ import annotations

import hashlib
import json
import os
import re
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Protocol, Self, cast
from urllib.error import HTTPError, URLError
from urllib.parse import unquote, urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener
from uuid import uuid4

from echoatlas.processor.acquisition.checksum import crc64nvme_file
from echoatlas.processor.acquisition.models import (
    ManifestValidationError,
    PinnedObject,
    SelectionManifest,
    parse_selection_manifest,
)

_CONTENT_RANGE = re.compile(r"^bytes (\d+)-(\d+)/(\d+)$")
_ALLOWED_MEDIA_TYPES = frozenset({"image/tiff", "image/geotiff", "application/octet-stream"})
_TIFF_MAGIC = frozenset({b"II*\x00", b"MM\x00*", b"II+\x00", b"MM\x00+"})


class AcquisitionError(RuntimeError):
    """Base class for safe acquisition failures."""


class AcquisitionPolicyError(AcquisitionError):
    """A pinned source violates the configured download policy."""


class AcquisitionAccessError(AcquisitionError):
    """The remote source could not be read completely."""


class AcquisitionNotFoundError(AcquisitionAccessError):
    """The pinned source object no longer exists."""


class SizeLimitError(AcquisitionError):
    """A declared or received object exceeds a safe bound."""


class IntegrityError(AcquisitionError):
    """A downloaded or cached object does not match its pinned identity."""


class DownloadResponse(Protocol):
    status: int
    headers: object

    def read(self, amount: int = -1) -> bytes: ...

    def __enter__(self) -> Self: ...

    def __exit__(self, exc_type: object, exc_value: object, traceback: object) -> None: ...


class UrlOpener(Protocol):
    def __call__(self, request: Request, *, timeout: float) -> DownloadResponse: ...


class _RejectRedirects(HTTPRedirectHandler):
    def redirect_request(
        self,
        req: Request,
        fp: object,
        code: int,
        msg: str,
        headers: object,
        newurl: str,
    ) -> None:
        del req, fp, code, msg, headers, newurl
        return None


@dataclass(frozen=True)
class DownloadResult:
    role: str
    item_id: str
    cache_path: Path
    size_bytes: int
    checksum_crc64nvme: str
    from_cache: bool


class SafeAcquisitionCache:
    """Fetch only approved pinned objects and promote complete verified files."""

    def __init__(
        self,
        *,
        data_root: Path,
        allowed_hosts: frozenset[str],
        max_object_bytes: int = 1_000_000_000,
        timeout_seconds: float = 60,
        chunk_size: int = 1024 * 1024,
        opener: UrlOpener | None = None,
    ) -> None:
        if max_object_bytes <= 0 or chunk_size <= 0:
            raise ValueError("download size limits must be positive")
        self._data_root = data_root
        self._allowed_hosts = allowed_hosts
        self._max_object_bytes = max_object_bytes
        self._timeout_seconds = timeout_seconds
        self._chunk_size = chunk_size
        self._opener = opener or cast(UrlOpener, build_opener(_RejectRedirects()).open)

    def fetch_manifest(
        self, manifest: SelectionManifest, *, source_manifest_path: Path
    ) -> tuple[DownloadResult, ...]:
        try:
            manifest_bytes = source_manifest_path.read_bytes()
            current_manifest = parse_selection_manifest(manifest_bytes)
        except (OSError, ManifestValidationError) as error:
            raise AcquisitionPolicyError(
                f"source manifest is no longer readable: {error}"
            ) from error
        if current_manifest != manifest:
            raise IntegrityError("source manifest changed after it was validated")

        results = tuple(
            self.fetch(
                role, manifest.acquisitions[role].item_id, manifest.acquisitions[role].object
            )
            for role in ("before", "after")
        )
        self._write_provenance(manifest, manifest_bytes)
        return results

    def fetch(self, role: str, item_id: str, source: PinnedObject) -> DownloadResult:
        self._validate_source(source)
        cache_path, partial_path = self._paths(item_id, source)
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        partial_path.parent.mkdir(parents=True, exist_ok=True)

        if cache_path.exists():
            self._verify_file(cache_path, source)
            return self._result(role, item_id, cache_path, source, from_cache=True)

        if partial_path.exists() and partial_path.stat().st_size > source.size_bytes:
            partial_path.unlink()
            raise SizeLimitError(f"partial file exceeds pinned size for {item_id}")

        offset = partial_path.stat().st_size if partial_path.exists() else 0
        if offset < source.size_bytes:
            try:
                self._download(source, partial_path, offset)
            except SizeLimitError:
                partial_path.unlink(missing_ok=True)
                raise

        try:
            self._verify_file(partial_path, source)
        except (AcquisitionPolicyError, IntegrityError):
            partial_path.unlink(missing_ok=True)
            raise

        try:
            os.link(partial_path, cache_path)
        except FileExistsError:
            self._verify_file(cache_path, source)
        partial_path.unlink(missing_ok=True)
        return self._result(role, item_id, cache_path, source, from_cache=False)

    def _download(self, source: PinnedObject, partial_path: Path, offset: int) -> None:
        headers = {
            "Accept": "image/tiff, image/geotiff, application/octet-stream",
            "User-Agent": "EchoAtlas/0.1 acquisition-cache",
        }
        if offset:
            headers["Range"] = f"bytes={offset}-"
        request = Request(source.url, headers=headers)
        try:
            with self._opener(request, timeout=self._timeout_seconds) as response:
                self._validate_response(response, source, offset)
                mode = "ab" if offset else "wb"
                with partial_path.open(mode) as handle:
                    while payload := response.read(self._chunk_size):
                        handle.write(payload)
                        if handle.tell() > source.size_bytes:
                            raise SizeLimitError(f"response exceeds pinned size for {source.url}")
                    handle.flush()
                    os.fsync(handle.fileno())
        except HTTPError as error:
            if error.code == 404:
                raise AcquisitionNotFoundError(
                    f"pinned object was not found: {source.url}"
                ) from error
            raise AcquisitionAccessError(
                f"object request failed with HTTP {error.code}: {source.url}"
            ) from error
        except (URLError, TimeoutError, OSError) as error:
            raise AcquisitionAccessError(
                f"object request failed for {source.url}: {error}"
            ) from error

    def _validate_response(
        self, response: DownloadResponse, source: PinnedObject, offset: int
    ) -> None:
        headers = response.headers
        get_header = getattr(headers, "get", None)
        if not callable(get_header):
            raise AcquisitionAccessError("download response has no readable headers")

        expected_status = 206 if offset else (200, 206)
        if isinstance(expected_status, tuple):
            valid_status = response.status in expected_status
        else:
            valid_status = response.status == expected_status
        if not valid_status:
            raise AcquisitionAccessError(
                f"unexpected HTTP status {response.status} for {source.url}"
            )

        media_type = str(get_header("Content-Type") or "").split(";", 1)[0].strip().lower()
        if media_type not in _ALLOWED_MEDIA_TYPES:
            raise AcquisitionPolicyError(
                f"unexpected media type {media_type or '<missing>'} for {source.url}"
            )

        content_length = get_header("Content-Length")
        if content_length is not None:
            try:
                response_bytes = int(content_length)
            except ValueError as error:
                raise AcquisitionAccessError("response Content-Length is invalid") from error
            if response_bytes < 0 or offset + response_bytes > source.size_bytes:
                raise SizeLimitError(f"response exceeds pinned size for {source.url}")

        if response.status == 206:
            content_range = str(get_header("Content-Range") or "")
            match = _CONTENT_RANGE.fullmatch(content_range)
            if not match:
                raise AcquisitionAccessError("partial response has invalid Content-Range")
            start, end, total = (int(value) for value in match.groups())
            if (
                start != offset
                or end != total - 1
                or total != source.size_bytes
                or (content_length is not None and int(content_length) != end - start + 1)
            ):
                raise AcquisitionAccessError("partial response does not match the pinned object")

        response_etag = get_header("ETag")
        if response_etag and _normalize_etag(str(response_etag)) != _normalize_etag(source.etag):
            raise IntegrityError(f"response ETag does not match the pinned object: {source.url}")

    def _validate_source(self, source: PinnedObject) -> None:
        parsed = urlparse(source.url)
        path = unquote(parsed.path)
        if (
            parsed.scheme != "https"
            or parsed.hostname not in self._allowed_hosts
            or parsed.username is not None
            or parsed.password is not None
            or parsed.query
            or parsed.fragment
            or "\\" in path
        ):
            raise AcquisitionPolicyError(f"remote URL is not allowlisted: {source.url}")
        if any(part in {"", ".", ".."} for part in path.split("/")[1:]):
            raise AcquisitionPolicyError(f"remote URL contains an unsafe path: {source.url}")
        if source.size_bytes > self._max_object_bytes:
            raise SizeLimitError(f"pinned object exceeds configured size limit: {source.url}")

    def _verify_file(self, path: Path, source: PinnedObject) -> None:
        if path.stat().st_size != source.size_bytes:
            raise IntegrityError(f"file size does not match pinned object: {path}")
        with path.open("rb") as handle:
            if handle.read(4) not in _TIFF_MAGIC:
                raise AcquisitionPolicyError(f"file does not have a recognized TIFF header: {path}")
        actual_checksum = crc64nvme_file(path, chunk_size=self._chunk_size)
        if actual_checksum != source.checksum.value:
            raise IntegrityError(f"CRC64NVME checksum mismatch for {path}")

    def _paths(self, item_id: str, source: PinnedObject) -> tuple[Path, Path]:
        source_name = PurePosixPath(unquote(urlparse(source.url).path)).name
        file_name = f"{item_id}-{source_name}"
        cache_path = self._data_root / "cache" / "acquisitions" / file_name
        partial_path = self._data_root / "working" / "acquisitions" / f"{file_name}.part"
        return cache_path, partial_path

    def _result(
        self,
        role: str,
        item_id: str,
        cache_path: Path,
        source: PinnedObject,
        *,
        from_cache: bool,
    ) -> DownloadResult:
        return DownloadResult(
            role=role,
            item_id=item_id,
            cache_path=cache_path,
            size_bytes=source.size_bytes,
            checksum_crc64nvme=source.checksum.value,
            from_cache=from_cache,
        )

    def _write_provenance(self, manifest: SelectionManifest, manifest_bytes: bytes) -> None:
        provenance_dir = self._data_root / "provenance"
        provenance_dir.mkdir(parents=True, exist_ok=True)
        _write_immutable(provenance_dir / "source-manifest.json", manifest_bytes)
        record = {
            "selection_id": manifest.selection_id,
            "manifest_version": manifest.manifest_version,
            "manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
            "accessed_at": manifest.accessed_at.isoformat(),
            "license": manifest.license.model_dump(mode="json"),
            "source_manifest": "source-manifest.json",
            "objects": [
                {
                    "role": role,
                    "item_id": acquisition.item_id,
                    "url": acquisition.object.url,
                    "key": acquisition.object.key,
                    "size_bytes": acquisition.object.size_bytes,
                    "etag": acquisition.object.etag,
                    "checksum": acquisition.object.checksum.model_dump(mode="json"),
                }
                for role in ("before", "after")
                for acquisition in (manifest.acquisitions[role],)
            ],
        }
        payload = f"{json.dumps(record, indent=2, sort_keys=True)}\n".encode()
        _write_immutable(provenance_dir / "attribution.json", payload)


def _write_immutable(destination: Path, payload: bytes) -> None:
    if destination.exists():
        if destination.read_bytes() != payload:
            raise IntegrityError(f"immutable provenance record differs: {destination}")
        return

    temporary = destination.with_suffix(f"{destination.suffix}.{uuid4().hex}.tmp")
    try:
        with temporary.open("xb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        try:
            os.link(temporary, destination)
        except FileExistsError as error:
            if destination.read_bytes() != payload:
                raise IntegrityError(
                    f"immutable provenance record differs: {destination}"
                ) from error
    finally:
        temporary.unlink(missing_ok=True)


def _normalize_etag(value: str) -> str:
    return value.removeprefix("W/").strip('"')
