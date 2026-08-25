# Catalog search contract v1

EAT-017 adds a metadata-only search boundary for provider-reported Umbra and Sentinel-1 acquisitions. It supports the future Explore interface without coupling MapLibre, the workbench, or processing policy to provider payloads.

## Public boundary

`POST /v1/catalog/search` accepts contract version `1.0.0` with:

- a WGS84 Polygon and its ordered bbox;
- timezone-aware start and end timestamps;
- one or both provider IDs: `umbra` and `sentinel-1`;
- optional product, polarization, and maximum-resolution filters;
- a page size from 1 to 50 and an opaque query-bound cursor.

The response returns normalized provider, acquisition time, exact provider-reported footprint, product, polarization, resolution, platform/orbit metadata, license, and source identity. Raw STAC documents, asset payloads, download credentials, and provider-specific pagination never cross the API boundary.

The response status is:

- `complete` when every requested provider completed its bounded sample;
- `empty` when every provider completed and reported no matching acquisitions;
- `partial` when a provider failed, returned malformed metadata, or reached a configured page/traversal limit.

Every provider also has an attributable report. A failed provider does not erase successful results from another provider.

## Safety and performance bounds

- AOIs are limited to a five-degree by five-degree envelope, 25 square degrees, five polygon rings, and 100 coordinates. Antimeridian-crossing bboxes are not accepted in v1.
- Search ranges must be timezone-aware, ordered, and no longer than 366 days.
- Provider samples are limited to 300 normalized records. Sentinel-1 follows at most three 100-item STAC pages. Umbra traversal defaults to at most 500 catalogs and 500 items and reports when either sample limit is reached.
- HTTP metadata is restricted to the Umbra public-catalog and Copernicus Data Space STAC hosts. Initial URLs and final redirect hosts are checked. Each request has a 20-second timeout and a 5 MB response cap.
- Aggregated responses are limited to 2 MB. At most 128 query results are cached in memory for five minutes using a canonical request fingerprint; expired entries are pruned and the oldest entry is evicted at capacity. Cursors contain only an offset and that fingerprint; a cursor cannot be reused with a different query.
- Provider geometry is normalized to 2D WGS84 Polygon coordinates. The service filters every normalized result again by AOI, time, product, polarization, and resolution before returning it.
- No raster asset is requested by the search endpoint or CLI.

## Provider behavior

### Umbra

Umbra publishes a static STAC hierarchy rather than an Item Search API. `UmbraCatalogSearchAdapter` performs a bounded traversal, maps provider items to the shared contract, and filters their reported footprints against the request. A global-root result can be a bounded sample; the response reports traversal limits rather than implying exhaustive Umbra coverage.

The adapter suppresses asset-resolution warnings because EAT-017 is metadata-only. The legacy EAT-002 indexer still includes those warnings and its separate public-S3 resolution behavior when exact objects are required.

### Sentinel-1

`Sentinel1CatalogSearchAdapter` queries the official Copernicus Data Space STAC endpoint at `https://stac.dataspace.copernicus.eu/v1/search` and the `sentinel-1-grd` collection. It sends the bounded bbox, time range, collection, and result limit, follows only allowlisted `next` links, and preserves the collection's legal-notice link. The official [STAC product catalogue documentation](https://documentation.dataspace.copernicus.eu/APIs/STAC.html) describes the endpoint, collection, Item Search behavior, and supported spatial/temporal filters.

## Deterministic and live evidence

`services/backend/tests/test_catalog_search.py` covers request bounds, host/redirect/size/timeout failures, cache reuse, query-bound cursors, provider isolation, partial results, Umbra spatial filtering, 3D-to-2D footprint normalization, Sentinel pagination, schema rejection, and the normalized no-provider-payload boundary. API tests cover the versioned route and response.

The checked-in [2026-08-25 live smoke summary](../data/catalog-search-smoke-2026-08-25.json) records two bounded metadata-only searches over the approved Bingham Canyon AOI:

- Sentinel-1 GRD, 1 June through 1 August 2025: 15 matching provider items, complete, no warnings;
- Umbra June 2025 catalog, 1 June through 1 July 2025: five matching provider items, complete, no warnings.

The Umbra smoke intentionally starts at the June 2025 month catalog and caps traversal at 40 catalogs and 300 items. This verifies the adapter and AOI filter, not a claim that Umbra has globally exhaustive coverage.

Reproduce the Sentinel smoke:

```bash
uv run echoatlas-search-catalog \
  --bbox=-112.2,40.45,-112.05,40.6 \
  --start 2025-06-01T00:00:00Z \
  --end 2025-08-01T00:00:00Z \
  --provider sentinel-1 \
  --page-size 5
```

Reproduce the bounded Umbra month smoke:

```bash
uv run echoatlas-search-catalog \
  --bbox=-112.2,40.45,-112.05,40.6 \
  --start 2025-06-01T00:00:00Z \
  --end 2025-07-01T00:00:00Z \
  --provider umbra \
  --page-size 5 \
  --umbra-root-url https://umbra-open-data-catalog.s3.us-west-2.amazonaws.com/stac/2025/2025-06/catalog.json \
  --umbra-max-catalogs 40 \
  --umbra-max-items 300
```

Live catalogs can change. A later result count may differ without invalidating the deterministic fixtures or the contract.
