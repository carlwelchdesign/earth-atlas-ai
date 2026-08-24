# Architecture foundation

EchoAtlas begins as a modular monolith rather than separate deployable services:

- `echoatlas.api` owns HTTP parsing, response contracts, and application orchestration.
- `echoatlas.processor` will own deterministic domain policy and geospatial processing.
- `echoatlas.processor.catalog` now owns the provider-edge STAC traversal and public-S3 metadata resolution introduced by EAT-002.
- the React workbench will consume versioned API and analysis-bundle contracts rather than provider payloads.

This structure keeps Python raster dependencies in one reproducible environment while preserving boundaries that can be split later if measured deployment or scaling needs justify it.

The only HTTP behavior remains `/health`. Catalog discovery is currently a local CLI boundary; this avoids implying remote imagery, detection, persistence, AI, or operational readiness.

See [Catalog indexer](catalog-indexer.md) for the normalized record, trust boundary, and live-smoke evidence.
