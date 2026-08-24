# Architecture foundation

EchoAtlas begins as a modular monolith rather than separate deployable services:

- `echoatlas.api` owns HTTP parsing, response contracts, and application orchestration.
- `echoatlas.processor` will own deterministic domain policy and geospatial processing.
- provider adapters and persistence remain future edge modules introduced by the ticket that needs them.
- the React workbench will consume versioned API and analysis-bundle contracts rather than provider payloads.

This structure keeps Python raster dependencies in one reproducible environment while preserving boundaries that can be split later if measured deployment or scaling needs justify it.

The only initial HTTP behavior is `/health`. It proves packaging and runtime wiring without implying imagery, detection, persistence, AI, or operational readiness.
