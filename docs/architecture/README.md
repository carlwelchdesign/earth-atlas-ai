# Architecture foundation

EchoAtlas begins as a modular monolith rather than separate deployable services:

- `echoatlas.api` owns HTTP parsing, response contracts, and application orchestration.
- `echoatlas.processor` owns deterministic domain policy and geospatial processing.
- `echoatlas.processor.catalog` now owns the provider-edge STAC traversal and public-S3 metadata resolution introduced by EAT-002.
- [Catalog search contract v1](catalog-search-v1.md) defines EAT-017's bounded Umbra and Sentinel-1 metadata search, normalized API boundary, partial-provider behavior, caching, pagination, and live smoke evidence.
- [Explore-to-Analyze selection and jobs](explore-analysis-jobs.md) defines EAT-019's immutable manifest, comparability boundary, bounded asynchronous jobs, prepared-bundle identity checks, and UI handoff.
- the React workbench will consume versioned API and analysis-bundle contracts rather than provider payloads.

This structure keeps Python raster dependencies in one reproducible environment while preserving boundaries that can be split later if measured deployment or scaling needs justify it.

The HTTP surface includes health, bounded catalog/place discovery, immutable analysis selections, and bounded preparation-job orchestration. Safe acquisition and raster processing remain deterministic local boundaries; none of these routes imply confirmed detection, durable persistence, AI authority, or operational readiness.

See [Catalog indexer](catalog-indexer.md) for the normalized record, trust boundary, and live-smoke evidence.

See [Acquisition cache](acquisition-cache.md) for the pinned-object download boundary and [SAR preview processing](sar-preview-processing.md) for the deterministic common-grid and display-normalization contract.

See [Baseline change candidates](change-candidate-baseline.md) for the explicit engineering score, registration tolerance, cleanup, vectorization, candidate contract, and interpretation boundary.

See [Analysis bundle v1](analysis-bundle-v1.md) for the provider-neutral schema, runtime trust boundary, compatibility policy, migration rules, and synthetic fixture evidence.

## Owner-review deployment

EAT-015 packages this modular monolith as two non-root containers: the FastAPI
backend and a static nginx workbench that proxies `/v1` and `/health` to the
backend on the Compose network. The default stack uses the synthetic fallback;
an optional overlay mounts a prepared, validated real-derived bundle read-only.
Both paths preserve native development, require neither Palantir nor an AI
provider, and bind host ports only to loopback. Browser-local append-only
assessment history is deliberately separate from deterministic processing and is
not represented as durable multi-user audit storage.
