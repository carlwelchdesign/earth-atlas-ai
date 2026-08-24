# Technical architecture

## Architectural intent

Keep geospatial processing portable, deterministic, and independent of any operational platform. Keep framework and provider I/O at the edges. Use one versioned analysis-bundle contract between processing, the standalone workbench, tests, and any future Palantir adapter.

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

## Boundaries and responsibilities

### Catalog adapter

- Traverses the public STAC catalog and, where catalog asset links are incomplete, resolves objects through a separately tested public-S3 adapter.
- Maps provider metadata into internal `Acquisition` records.
- Preserves the raw source document and records parse warnings.
- Never leaks provider-specific property names into UI components.

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

### Palantir adapter

Deferred until the standalone bundle is stable. It maps bundles into datasets/media and a minimal Ontology without moving processing policy into Foundry. Any OSDK application must use restricted application resources and operation scopes.

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
