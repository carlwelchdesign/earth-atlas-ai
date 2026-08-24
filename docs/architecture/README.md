# Architecture foundation

EchoAtlas begins as a modular monolith rather than separate deployable services:

- `echoatlas.api` owns HTTP parsing, response contracts, and application orchestration.
- `echoatlas.processor` owns deterministic domain policy and geospatial processing.
- `echoatlas.processor.catalog` now owns the provider-edge STAC traversal and public-S3 metadata resolution introduced by EAT-002.
- the React workbench will consume versioned API and analysis-bundle contracts rather than provider payloads.

This structure keeps Python raster dependencies in one reproducible environment while preserving boundaries that can be split later if measured deployment or scaling needs justify it.

The only HTTP behavior remains `/health`. Catalog discovery, safe acquisition, and preview processing are currently local CLI boundaries; this avoids implying detection, persistence, AI, or operational readiness.

See [Catalog indexer](catalog-indexer.md) for the normalized record, trust boundary, and live-smoke evidence.

See [Acquisition cache](acquisition-cache.md) for the pinned-object download boundary and [SAR preview processing](sar-preview-processing.md) for the deterministic common-grid and display-normalization contract.
