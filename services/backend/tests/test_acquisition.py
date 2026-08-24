from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Self
from urllib.error import HTTPError
from urllib.request import Request

import pytest

from echoatlas.processor.acquisition.cache import (
    AcquisitionAccessError,
    AcquisitionNotFoundError,
    AcquisitionPolicyError,
    IntegrityError,
    SafeAcquisitionCache,
    SizeLimitError,
)
from echoatlas.processor.acquisition.checksum import Crc64Nvme
from echoatlas.processor.acquisition.models import (
    ManifestValidationError,
    PinnedObject,
    SelectionManifest,
    load_selection_manifest,
)

ALLOWED_HOST = "data.example.test"


class FakeResponse:
    def __init__(
        self,
        *,
        status: int,
        headers: Mapping[str, str],
        reads: list[bytes | Exception],
    ) -> None:
        self.status = status
        self.headers = headers
        self._reads = reads

    def read(self, amount: int = -1) -> bytes:
        del amount
        if not self._reads:
            return b""
        value = self._reads.pop(0)
        if isinstance(value, Exception):
            raise value
        return value

    def __enter__(self) -> Self:
        return self

    def __exit__(self, exc_type: object, exc_value: object, traceback: object) -> None:
        return None


class FakeOpener:
    def __init__(self, responses: list[FakeResponse | Exception]) -> None:
        self.responses = responses
        self.requests: list[Request] = []

    def __call__(self, request: Request, *, timeout: float) -> FakeResponse:
        assert timeout > 0
        self.requests.append(request)
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


def checksum(payload: bytes) -> str:
    value = Crc64Nvme()
    value.update(payload)
    return value.base64digest()


def tiff(payload: bytes) -> bytes:
    return b"II*\x00" + payload


def pinned_object(
    payload: bytes, *, url: str | None = None, expected: str | None = None
) -> PinnedObject:
    object_url = url or f"https://{ALLOWED_HOST}/objects/source.tif"
    return PinnedObject.model_validate(
        {
            "key": "objects/source.tif",
            "url": object_url,
            "size_bytes": len(payload),
            "etag": "source-etag",
            "checksum": {
                "algorithm": "CRC64NVME",
                "encoding": "base64",
                "value": expected or checksum(payload),
                "type": "FULL_OBJECT",
            },
        }
    )


def response(
    payload: bytes, *, status: int = 200, extra_headers: Mapping[str, str] | None = None
) -> FakeResponse:
    headers = {"Content-Type": "image/tiff", "Content-Length": str(len(payload))}
    headers.update(extra_headers or {})
    return FakeResponse(status=status, headers=headers, reads=[payload])


def cache(
    tmp_path: Path, opener: FakeOpener, *, max_object_bytes: int = 100
) -> SafeAcquisitionCache:
    return SafeAcquisitionCache(
        data_root=tmp_path / "data",
        allowed_hosts=frozenset({ALLOWED_HOST}),
        max_object_bytes=max_object_bytes,
        chunk_size=3,
        opener=opener,
    )


def manifest_document(before: bytes, after: bytes) -> dict[str, object]:
    def acquisition(item_id: str, payload: bytes, name: str) -> dict[str, object]:
        return {
            "item_id": item_id,
            "acquired_at": "2025-01-01T00:00:00Z",
            "product_type": "GEC",
            "polarizations": ["VV"],
            "object": {
                "key": f"objects/{name}.tif",
                "url": f"https://{ALLOWED_HOST}/objects/{name}.tif",
                "size_bytes": len(payload),
                "etag": f"{name}-etag",
                "checksum": {
                    "algorithm": "CRC64NVME",
                    "encoding": "base64",
                    "value": checksum(payload),
                    "type": "FULL_OBJECT",
                },
            },
        }

    return {
        "manifest_version": "1.0.0",
        "selection_id": "test-selection-v1",
        "status": "approved",
        "accessed_at": "2026-08-24T00:00:00Z",
        "license": {"spdx": "CC-BY-4.0", "provider": "Test Provider"},
        "acquisitions": {
            "before": acquisition("before-item", before, "before"),
            "after": acquisition("after-item", after, "after"),
        },
    }


def write_manifest(tmp_path: Path, before: bytes, after: bytes) -> tuple[Path, SelectionManifest]:
    path = tmp_path / "selection.json"
    path.write_text(json.dumps(manifest_document(before, after)), encoding="utf-8")
    return path, load_selection_manifest(path)


def test_crc64nvme_matches_standard_check_value() -> None:
    assert checksum(b"123456789") == "rosUhgp5mIg="


def test_manifest_must_be_approved_and_pin_both_roles(tmp_path: Path) -> None:
    document = manifest_document(b"before", b"after")
    document["status"] = "awaiting_owner_approval"
    path = tmp_path / "selection.json"
    path.write_text(json.dumps(document), encoding="utf-8")

    with pytest.raises(ManifestValidationError, match="failed validation"):
        load_selection_manifest(path)


def test_fetch_manifest_promotes_verified_files_and_preserves_provenance(
    tmp_path: Path,
) -> None:
    before = tiff(b"before")
    after = tiff(b"after")
    manifest_path, manifest = write_manifest(tmp_path, before, after)
    opener = FakeOpener([response(before), response(after)])
    acquisition_cache = cache(tmp_path, opener)

    results = acquisition_cache.fetch_manifest(manifest, source_manifest_path=manifest_path)

    assert [result.role for result in results] == ["before", "after"]
    assert [result.cache_path.read_bytes() for result in results] == [before, after]
    assert not list((tmp_path / "data" / "working").rglob("*.part"))
    provenance = tmp_path / "data" / "provenance"
    assert (provenance / "source-manifest.json").read_bytes() == manifest_path.read_bytes()
    attribution = json.loads((provenance / "attribution.json").read_text())
    assert attribution["license"] == {"provider": "Test Provider", "spdx": "CC-BY-4.0"}
    assert [source["role"] for source in attribution["objects"]] == ["before", "after"]

    cached = acquisition_cache.fetch_manifest(manifest, source_manifest_path=manifest_path)
    assert all(result.from_cache for result in cached)
    assert opener.responses == []

    manifest_path.write_text(f"{manifest_path.read_text()}\n", encoding="utf-8")
    with pytest.raises(IntegrityError, match="immutable provenance"):
        acquisition_cache.fetch_manifest(manifest, source_manifest_path=manifest_path)

    changed = json.loads(manifest_path.read_text())
    changed["selection_id"] = "different-selection"
    manifest_path.write_text(json.dumps(changed), encoding="utf-8")
    with pytest.raises(IntegrityError, match="source manifest changed"):
        acquisition_cache.fetch_manifest(manifest, source_manifest_path=manifest_path)


def test_interrupted_download_preserves_partial_file_and_resumes(tmp_path: Path) -> None:
    payload = tiff(b"ab")
    opener = FakeOpener(
        [
            FakeResponse(
                status=200,
                headers={"Content-Type": "image/tiff", "Content-Length": "6"},
                reads=[payload[:3], TimeoutError("interrupted")],
            ),
            response(
                payload[3:],
                status=206,
                extra_headers={"Content-Range": "bytes 3-5/6"},
            ),
        ]
    )
    acquisition_cache = cache(tmp_path, opener)
    source = pinned_object(payload)

    with pytest.raises(AcquisitionAccessError, match="interrupted"):
        acquisition_cache.fetch("before", "item-1", source)

    partial = next((tmp_path / "data" / "working").rglob("*.part"))
    assert partial.read_bytes() == payload[:3]

    result = acquisition_cache.fetch("before", "item-1", source)
    assert result.cache_path.read_bytes() == payload
    assert opener.requests[1].get_header("Range") == "bytes=3-"


def test_resume_rejects_inconsistent_content_range(tmp_path: Path) -> None:
    payload = tiff(b"ab")
    source = pinned_object(payload)
    partial = tmp_path / "data" / "working" / "acquisitions" / "item-1-source.tif.part"
    partial.parent.mkdir(parents=True)
    partial.write_bytes(payload[:3])
    opener = FakeOpener(
        [response(payload[3:], status=206, extra_headers={"Content-Range": "bytes 3-4/6"})]
    )

    with pytest.raises(AcquisitionAccessError, match="does not match"):
        cache(tmp_path, opener).fetch("before", "item-1", source)

    assert partial.read_bytes() == payload[:3]


def test_wrong_media_type_is_rejected(tmp_path: Path) -> None:
    payload = tiff(b"ab")
    opener = FakeOpener(
        [FakeResponse(status=200, headers={"Content-Type": "text/html"}, reads=[payload])]
    )

    with pytest.raises(AcquisitionPolicyError, match="media type"):
        cache(tmp_path, opener).fetch("before", "item-1", pinned_object(payload))


def test_umbra_binary_octet_stream_is_accepted_with_valid_tiff(tmp_path: Path) -> None:
    payload = tiff(b"ab")
    opener = FakeOpener(
        [
            FakeResponse(
                status=200,
                headers={
                    "Content-Type": "binary/octet-stream",
                    "Content-Length": str(len(payload)),
                },
                reads=[payload],
            )
        ]
    )

    result = cache(tmp_path, opener).fetch("before", "item-1", pinned_object(payload))

    assert result.cache_path.read_bytes() == payload


def test_declared_and_response_sizes_are_bounded(tmp_path: Path) -> None:
    payload = tiff(b"ab")
    source = pinned_object(payload)
    unopened = FakeOpener([])
    with pytest.raises(SizeLimitError, match="configured size"):
        cache(tmp_path, unopened, max_object_bytes=5).fetch("before", "item-1", source)
    assert unopened.requests == []

    oversized = FakeOpener(
        [
            FakeResponse(
                status=200, headers={"Content-Type": "image/tiff", "Content-Length": "7"}, reads=[]
            )
        ]
    )
    with pytest.raises(SizeLimitError, match="pinned size"):
        cache(tmp_path, oversized).fetch("before", "item-1", source)

    streamed_oversize = FakeOpener(
        [FakeResponse(status=200, headers={"Content-Type": "image/tiff"}, reads=[payload + b"x"])]
    )
    with pytest.raises(SizeLimitError, match="pinned size"):
        cache(tmp_path, streamed_oversize).fetch("before", "item-1", source)
    assert not list((tmp_path / "data" / "working").rglob("*.part"))


def test_checksum_mismatch_is_not_promoted_or_reused(tmp_path: Path) -> None:
    payload = tiff(b"ab")
    opener = FakeOpener([response(payload)])
    source = pinned_object(payload, expected=checksum(tiff(b"xx")))

    with pytest.raises(IntegrityError, match="checksum mismatch"):
        cache(tmp_path, opener).fetch("before", "item-1", source)

    assert not list((tmp_path / "data" / "cache").rglob("*.tif"))
    assert not list((tmp_path / "data" / "working").rglob("*.part"))


def test_missing_object_has_actionable_error_and_no_partial_file(tmp_path: Path) -> None:
    source = pinned_object(tiff(b"ab"))
    error = HTTPError(source.url, 404, "Not Found", hdrs=None, fp=None)

    with pytest.raises(AcquisitionNotFoundError, match="not found"):
        cache(tmp_path, FakeOpener([error])).fetch("before", "item-1", source)

    assert not list((tmp_path / "data" / "working").rglob("*.part"))


def test_non_allowlisted_url_is_rejected_before_network_access(tmp_path: Path) -> None:
    source = pinned_object(tiff(b"ab"), url="https://evil.example/objects/source.tif")
    opener = FakeOpener([])

    with pytest.raises(AcquisitionPolicyError, match="not allowlisted"):
        cache(tmp_path, opener).fetch("before", "item-1", source)
    assert opener.requests == []


def test_tiff_content_type_with_wrong_file_magic_is_rejected(tmp_path: Path) -> None:
    payload = b"notiff"
    opener = FakeOpener([response(payload)])

    with pytest.raises(AcquisitionPolicyError, match="TIFF header"):
        cache(tmp_path, opener).fetch("before", "item-1", pinned_object(payload))

    assert not list((tmp_path / "data" / "cache").rglob("*.tif"))
    assert not list((tmp_path / "data" / "working").rglob("*.part"))
