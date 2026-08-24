"""Public S3 ListObjectsV2 adapter for resolving empty STAC asset links."""

from __future__ import annotations

from urllib.parse import quote, urlencode
from xml.etree import ElementTree

from echoatlas.processor.catalog.http import CatalogAccessError, MetadataClient
from echoatlas.processor.catalog.models import Acquisition, CatalogAsset, CatalogWarning


class PublicS3ObjectResolver:
    """List task-scoped public objects without downloading their payloads."""

    def __init__(self, client: MetadataClient, bucket_url: str) -> None:
        self._client = client
        self._bucket_url = bucket_url.rstrip("/")

    def resolve(
        self, acquisition: Acquisition, *, max_pages: int = 10
    ) -> tuple[tuple[CatalogAsset, ...], tuple[CatalogWarning, ...], int]:
        task_id = acquisition.provider_task_id
        if task_id is None:
            warning = CatalogWarning(
                code="missing_task_id",
                source_url=acquisition.source_url,
                message="cannot resolve public S3 objects without umbra:task_id",
            )
            return (), (warning,), 0

        prefix = f"sar-data/task-data/{task_id}/"
        continuation_token: str | None = None
        objects: list[CatalogAsset] = []
        warnings: list[CatalogWarning] = []
        pages = 0

        while pages < max_pages:
            query: dict[str, str | int] = {"list-type": "2", "prefix": prefix, "max-keys": 1000}
            if continuation_token is not None:
                query["continuation-token"] = continuation_token
            listing_url = f"{self._bucket_url}/?{urlencode(query)}"
            payload = self._client.get_bytes(listing_url)
            pages += 1
            try:
                root = ElementTree.fromstring(payload)
            except ElementTree.ParseError as error:
                raise CatalogAccessError(
                    f"invalid S3 listing XML at {listing_url}: {error}"
                ) from error

            namespace = {"s3": "http://s3.amazonaws.com/doc/2006-03-01/"}
            for entry in root.findall("s3:Contents", namespace):
                key = entry.findtext("s3:Key", namespaces=namespace)
                if not key:
                    warnings.append(
                        CatalogWarning(
                            code="malformed_s3_object",
                            source_url=listing_url,
                            message="S3 listing entry has no key",
                        )
                    )
                    continue
                size_text = entry.findtext("s3:Size", namespaces=namespace)
                etag = entry.findtext("s3:ETag", namespaces=namespace)
                objects.append(
                    CatalogAsset(
                        name=key.rsplit("/", 1)[-1],
                        href=f"{self._bucket_url}/{quote(key, safe='/')}",
                        origin="public-s3",
                        media_type=self._media_type(key),
                        roles=("data",),
                        object_key=key,
                        size_bytes=int(size_text) if size_text and size_text.isdigit() else None,
                        etag=etag.strip('"') if etag else None,
                    )
                )

            truncated = root.findtext("s3:IsTruncated", default="false", namespaces=namespace)
            if truncated.lower() != "true":
                break
            continuation_token = root.findtext("s3:NextContinuationToken", namespaces=namespace)
            if not continuation_token:
                raise CatalogAccessError(
                    f"truncated S3 listing has no continuation token: {listing_url}"
                )
        else:
            warnings.append(
                CatalogWarning(
                    code="s3_page_limit_reached",
                    source_url=acquisition.source_url,
                    message=f"stopped public S3 resolution after {max_pages} pages",
                )
            )

        if not objects:
            warnings.append(
                CatalogWarning(
                    code="s3_objects_not_found",
                    source_url=acquisition.source_url,
                    message=f"no public objects found under task prefix {prefix}",
                )
            )
        return tuple(objects), tuple(warnings), pages

    @staticmethod
    def _media_type(key: str) -> str | None:
        suffix = key.lower().rsplit(".", 1)[-1]
        return {
            "json": "application/json",
            "tif": "image/tiff; application=geotiff",
            "tiff": "image/tiff; application=geotiff",
            "xml": "application/xml",
            "nitf": "application/vnd.nitf",
            "zip": "application/zip",
        }.get(suffix)
