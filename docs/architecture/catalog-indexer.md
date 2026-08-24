# Catalog indexer

EAT-002 adds a bounded, metadata-only discovery path for the public Umbra catalog.

## Adapter boundary

`StacCatalogAdapter` traverses static STAC `child` and `item` links and maps valid features into provider-neutral `Acquisition` records. Each record preserves the source STAC document and exposes identity, time, WGS84 geometry, SAR product and geometry fields, platform, license, assets, and source URL. Malformed documents are skipped with structured warnings rather than partially trusted.

`PublicS3ObjectResolver` separately calls S3 `ListObjectsV2` under the acquisition's public `umbra:task_id` prefix. It follows continuation tokens and records object keys, public URLs, declared byte sizes, and ETags. It does not request those object URLs. STAC-declared assets and S3-resolved objects remain distinct because live filenames do not always correspond exactly.

## Safety and bounds

- HTTPS hosts are allowlisted.
- Metadata responses are capped at 5 MB and have request timeouts.
- Catalog, item, and S3 page counts are explicit runtime limits.
- Empty asset links, missing geometry, malformed links, network failures, absent task IDs, empty S3 prefixes, and pagination anomalies remain visible as warnings.
- Candidate time-series AOIs are coarse spatial groupings for EAT-003 investigation, not approved pairs, change findings, or semantic interpretations.
- No raster payload is downloaded by this command.

## Outputs

The CLI can write a complete normalized index and/or a smaller feasibility report. The checked-in [2026-08-24 smoke report](../data/umbra-catalog-smoke-2026-08-24.json) records a bounded live run. The full generated index is intentionally not checked in; it can be regenerated into the ignored `data/` workspace.

The smoke report's declared object-byte total describes the objects found in public metadata. It is not transferred bytes, cache size, or a storage forecast.
