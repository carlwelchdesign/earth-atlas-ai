# Safe acquisition cache

EAT-004 adds a local-only acquisition boundary for the exact objects in the approved selection manifest. It downloads source imagery but does not parse pixels, crop the AOI, produce derivatives, or authorize public release.

## Run the approved acquisition

From the repository root:

```sh
uv run echoatlas-acquire \
  --manifest fixtures/demo/selection-manifest.v1.json \
  --data-root data
```

The pinned pair declares 524,289,889 bytes in total. The command's default per-object ceiling is 1 GB and can be reduced with `--max-object-bytes`. It never follows a manifest URL outside `https://umbra-open-data-catalog.s3.us-west-2.amazonaws.com`.

## Local layout

```text
data/
  cache/acquisitions/    complete checksum-verified TIFF source objects
  working/acquisitions/  resumable `.part` files; safe to remove and retry
  provenance/            offline source manifest and attribution record
  raw/                   reserved for later raster work
```

The entire `data` workspace is Git-ignored. Root-level `raw`, `cache`, and `working` directories are also ignored as a guard against accidental local layouts. Never move source TIFFs into `fixtures` or commit them.

## Safety and integrity contract

- The manifest must be version `1.0.0`, have status `approved`, contain exactly `before` and `after` GEC acquisitions, and pin a relative object key, HTTPS URL, byte size, ETag, and full-object CRC64NVME checksum.
- Only `.tif` or `.tiff` objects on the allowlisted Umbra host are accepted. Credentials, redirects, query strings, fragments, encoded traversal, unsafe path segments, and unexpected response media types are rejected.
- Declared object size is checked before a request. `Content-Length`, `Content-Range`, and streamed bytes are checked during transfer, and the final file must exactly match the pinned size and a recognized classic-TIFF or BigTIFF header.
- Interrupted transfers remain in `data/working` and resume only from a matching HTTP `206` range response. Invalid range metadata cannot be appended.
- The complete file's CRC64NVME value is computed locally with the AWS Common Runtime and compared with the manifest. An ETag is checked when the server returns one, but it is not treated as a whole-file checksum because these source objects use multipart ETags.
- A verified working file is promoted with an atomic same-filesystem link. Existing cache entries are never overwritten and must pass the same size and checksum checks before reuse.
- A successful pair fetch writes `data/provenance/source-manifest.json` and `data/provenance/attribution.json`, preserving source identities, URLs, keys, access date, provider, license, ETags, sizes, and checksums for offline use.

AWS documents CRC64NVME as a full-object checksum and recommends stored checksums for validating downloaded object integrity: [Checking object integrity in Amazon S3](https://docs.aws.amazon.com/AmazonS3/latest/userguide/checking-object-integrity.html). The native checksum API is documented in [AWS CRT for Python](https://awslabs.github.io/aws-crt-python/api/checksums.html).

## Failure recovery

- Network interruption: rerun the same command; a valid partial transfer resumes.
- Missing object, wrong media type, unsafe URL, or invalid range: correct or re-pin the source manifest rather than bypassing the check.
- Size or checksum mismatch: the object is not promoted. A complete corrupt partial is removed; investigate source drift before retrying.
- Corrupt immutable cache entry: remove that one explicit cache file after investigating. The downloader will not silently replace it.
