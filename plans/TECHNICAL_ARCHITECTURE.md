# Technical architecture

## Architectural intent

Keep geospatial processing portable, deterministic, and independent of any operational platform. Keep framework and provider I/O at the edges. Use one versioned analysis-bundle contract between processing, the standalone workbench, and tests.

## Proposed repository shape

```text
apps/
  workbench/              React + TypeScript analyst UI
services/
  backend/
    src/echoatlas/
      api/                 Thin local HTTP boundary for bundles and assessments
      processor/           Python discovery, download, preprocessing, and detection
schemas/                  Versioned JSON Schema and GeoJSON conventions
fixtures/
  demo/                   Small, licensed, reproducible derived demo artifacts
docs/                     Operator, dataset, demo, and architecture documentation
plans/                    Product and delivery source of truth
data/                     Git-ignored raw/cache/derived workspace
```

EAT-001 selected a Python 3.12+ FastAPI modular monolith managed with `uv`, plus a React 19 and TypeScript workbench managed as an npm workspace and built with Vite. API and processing remain separate Python modules in one environment until measured deployment or scaling needs justify separate services. Python owns raster science; TypeScript owns the analyst experience; JSON/GeoJSON schemas connect them.

## Processing flow

```text
Umbra STAC/S3 discovery
  -> acquisition index
  -> dataset feasibility report
  -> pinned selection manifest
  -> resumable download + checksum cache
  -> raster validation and common AOI crop
  -> reprojection/resampling to a declared grid
  -> documented intensity normalization and preview generation
  -> deterministic change score/mask
  -> connected candidate geometries + measurements
  -> versioned analysis bundle
  -> analyst review UI and append-only assessments
```

## Post-MVP discovery flow

```text
MapLibre globe or accessible search/list
  -> bounded AOI + time range + provider filters
  -> provider-neutral catalog query API
  -> Umbra public-catalog adapter + Sentinel-1 catalog adapter
  -> normalized acquisition footprints, provenance, licenses, and warnings
  -> explicit candidate-pair selection and comparability review
  -> immutable selection manifest
  -> existing deterministic processing flow
  -> provider-neutral analysis bundle
  -> Analyze workbench
```

MapLibre owns navigation and rendering only. It may display basemap/vector tiles, acquisition-footprint GeoJSON, and explicitly configured raster tile sources, but it does not decide provider availability, pair suitability, processing policy, candidate meaning, or permissions.

## Boundaries and responsibilities

### Catalog adapter

- Traverses the public STAC catalog and, where catalog asset links are incomplete, resolves objects through a separately tested public-S3 adapter.
- Maps provider metadata into internal `Acquisition` records.
- Preserves the raw source document and records parse warnings.
- Never leaks provider-specific property names into UI components.
- Implements the same bounded spatial/time query contract for every provider and reports partial provider failures independently.
- Returns only acquisitions and footprints actually reported by a provider; global map extent must never be rendered as global imagery coverage.
- Applies AOI, result-count, pagination, timeout, cache, host-allowlist, and response-size limits before any later download or processing step.

### Processing domain

- Accepts a validated selection manifest and local/streamed GEC inputs.
- Produces deterministic outputs for declared parameters and software versions.
- Separates raster I/O, registration/resampling, normalization, change policy, and vectorization.
- Fails closed when required CRS, transform, polarization, dimensions, or overlap data is missing.
- Emits warnings for geometry/resolution differences that affect interpretation.

### Bundle contract

The first bundle version contains:

- `manifest.json`: bundle version, run identity, timestamps, input acquisitions, checksums, license, software commit, parameters, status, and warnings;
- `aoi.geojson`: declared area of interest;
- `acquisitions.json`: normalized acquisition metadata and source provenance;
- aligned before/after previews or tiles with declared CRS and transforms;
- `change-raster` preview plus `candidates.geojson`;
- `assessments.json`: local append-only review events or an empty initial array;
- optional `summary.json`: future AI draft with evidence references, never authoritative state.

All untrusted JSON is validated at runtime against versioned schemas.

### API boundary

- Thin endpoints for listing/loading bundles, saving assessments, and reading processing status.
- File-backed local persistence is acceptable for the first vertical slice if writes are atomic and validated.
- Processing is modeled as an asynchronous job with explicit `queued`, `running`, `succeeded`, `failed`, and `cancelled` states, even if the initial runner is local.
- No remote deployment or multi-user claims until authentication, authorization, durable storage, migrations, backups, and operations are separately designed.

### Workbench

- Keeps server data, local comparison controls, and presentation state separate.
- Loads only the provider-neutral bundle contract.
- Treats candidates as machine-generated review items, not findings.
- Makes stale, degraded, missing, and incompatible data visible.
- Separates post-MVP `Explore` navigation/catalog state from `Analyze` bundle/review state.
- Provides an equivalent searchable acquisition list for every map-only discovery action, including AOI results, selection, and no-coverage explanations.
- Keeps MapLibre, geocoding, basemap, and raster-tile providers behind UI adapters so they can be replaced without changing catalog or analysis contracts.

### Knowledge model

The versioned bundle is the current knowledge model: stable identities, typed records, explicit links, provenance, and schema validation. No RDF/OWL/SPARQL or proprietary ontology dependency is justified until the product has a concrete semantic-query, inference, or cross-system interchange requirement.

### Packaging and containers

- Native `uv` and npm workflows remain the fastest supported development path.
- `EAT-015` packages the standalone backend and built workbench as reproducible, production-oriented container images plus a local Compose configuration.
- Containers run as non-root users, include health checks, receive configuration and secrets only at runtime, and mount local bundle/assessment storage explicitly.
- The standalone Compose stack cannot require an ontology platform, an AI provider, or other optional platform integrations.
- Container readiness proves packaging and local orchestration only; authentication, durable multi-user storage, operations, public deployment, and release remain separate approval gates.

## MVP object model

| Object | Required identity | Lifecycle | Important links |
| --- | --- | --- | --- |
| `AreaOfInterest` | stable AOI ID + geometry hash | proposed, selected, retired | covered by acquisitions |
| `Acquisition` | provider + STAC/item ID | discovered, validated, rejected | covers AOI; source for run |
| `AnalysisRun` | run ID + manifest hash | queued, running, succeeded, failed, cancelled | uses acquisitions; produces artifacts/candidates |
| `EvidenceArtifact` | artifact ID + checksum | produced, invalidated | derived from run/input |
| `ChangeCandidate` | run-scoped candidate ID | pending, reviewed | derived from run; affects AOI geometry |
| `AnalystAssessment` | append-only event ID | recorded, superseded | assesses candidate; references evidence |
| `DraftSummary` | run + generator version | generated, accepted, rejected, superseded | cites candidates/evidence |

`Vessel`, `Facility`, `InfrastructureAsset`, `Alert`, and `Investigation` remain future types until the single change-review workflow proves a need.

## Comparability and quality report

Selection and processing must report, at minimum:

- AOI overlap ratio and common valid-data area;
- product type, polarization, platform, orbit direction, observation direction, resolution, incidence/grazing angle, timestamps, and CRS;
- reprojection/resampling choices;
- nodata and invalid-pixel proportions;
- normalization and filtering parameters;
- warnings for geometry, seasonal, surface-moisture, speckle, layover, shadow, or resolution conditions that can mimic change.

Initial thresholds are configuration and must be labeled as engineering heuristics until reviewed by a qualified SAR practitioner. They cannot be presented as calibrated confidence.

## Security and operations foundations

- Allowlist remote hosts and URL schemes before downloads.
- Validate content length, file type, raster dimensions, and decompression limits.
- Use checksums and immutable source manifests; never commit large raw imagery.
- Prevent path traversal in bundle names and archive extraction.
- Record structured processing events without secrets or sensitive payloads.
- Separate cancellable work directories from the immutable successful cache.
- Publish third-party licenses and Umbra attribution with demo artifacts.

## Testing strategy

- unit tests for metadata mapping, selection policy, state transitions, scoring, and schema validation;
- fixture tests for catalog irregularities, missing metadata, incompatible pairs, corrupt rasters, and partial downloads;
- golden tests for small raster preprocessing/change outputs with declared tolerances;
- API contract tests for success and failure states;
- UI behavior and accessibility tests for load, compare, review, recover, and export;
- one documented end-to-end rebuild of the pinned demo from source manifest to bundle.
