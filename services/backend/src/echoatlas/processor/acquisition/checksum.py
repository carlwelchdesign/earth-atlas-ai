"""Streaming checksum support for pinned source objects."""

from __future__ import annotations

import base64
from pathlib import Path

from awscrt import checksums  # type: ignore[import-untyped]


class Crc64Nvme:
    """Incremental CRC-64/NVME backed by the AWS Common Runtime."""

    def __init__(self) -> None:
        self._value = 0

    def update(self, payload: bytes) -> None:
        self._value = checksums.crc64nvme(payload, self._value)

    def digest(self) -> bytes:
        return self._value.to_bytes(8, byteorder="big")

    def base64digest(self) -> str:
        return base64.b64encode(self.digest()).decode("ascii")


def crc64nvme_file(path: Path, *, chunk_size: int = 1024 * 1024) -> str:
    checksum = Crc64Nvme()
    with path.open("rb") as handle:
        while chunk := handle.read(chunk_size):
            checksum.update(chunk)
    return checksum.base64digest()
