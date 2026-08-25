# EchoAtlas

EchoAtlas is a planned civilian disaster and infrastructure-change SAR intelligence workbench. It will turn public Umbra imagery into deterministic change candidates, evidence, and human-reviewed assessments.

**Current status:** the Bingham Canyon civilian demonstration pair is approved and pinned. The backend can fetch those exact public Umbra objects into a bounded, checksum-verified local cache, produce deterministic AOI-cropped engineering previews on a declared common grid, generate a transparent baseline queue of pending change candidates, and prepare the real satellite-derived comparison for the local workbench. It does not confirm physical change or provide operational intelligence.

## Architecture

- `services/backend`: Python modular backend with a thin FastAPI boundary and an independent processing domain.
- `apps/workbench`: React and TypeScript analyst application.
- `schemas`: versioned analysis-bundle contracts.
- `fixtures`: pinned source selections and bounded synthetic fixture documentation.
- `docs/design`: approved or approval-gated product-design specifications and validation evidence.
- `plans`: canonical product, architecture, governance, and execution plans.

The portable analysis bundle is the boundary between processing, UI, tests, and optional platform adapters. The local workbench prefers a prepared real-data bundle when one has been staged and otherwise falls back to a clearly labeled synthetic fixture. The Palantir feasibility layer currently produces a network-free import plan and is not a required runtime. A Developer Tier enrollment and EchoAtlas project now exist. The exact tiny synthetic fixture has been uploaded as six raw structured files and four PNG evidence items, and its five non-empty object families plus six non-empty relationship families are indexed in the live Ontology. A separate generated GeoTIFF also verifies bounded TIFF ingestion and preview, while Ontology-backed map tiling remains unverified. No real Umbra imagery has been uploaded to Palantir, and no credentials, API keys, OAuth clients, actions, or applications have been created there.

## Prerequisites

- Python 3.12 or newer
- [uv](https://docs.astral.sh/uv/)
- Node.js 20.19 or newer
- npm 10 or newer
- GNU Make or the macOS command-line developer tools

## Setup

```sh
make setup
```

Run every local quality gate:

```sh
make check
```

Start the backend and workbench in separate terminals:

```sh
make dev-api
make dev-web
```

The local health endpoint is `http://127.0.0.1:8000/health`. The Vite development server prints the workbench URL when it starts.

Run a bounded live catalog smoke test:

```sh
uv run echoatlas-catalog \
  --max-catalogs 120 \
  --max-items 100 \
  --report-output data/umbra-catalog-report.json \
  --index-output data/umbra-acquisition-index.json
```

This command only reads small STAC JSON and S3 listing XML documents. Object URLs and declared sizes are indexed, but raster payloads are never requested. See [the catalog indexer documentation](docs/architecture/catalog-indexer.md).

Download the approved pair into the Git-ignored local cache:

```sh
uv run echoatlas-acquire \
  --manifest fixtures/demo/selection-manifest.v1.json \
  --data-root data
```

The pinned inputs total about 524 MB. Downloads are allowlisted, resumable, size-bounded, and verified against the manifest's full-object CRC64NVME checksums before atomic cache promotion. See [the acquisition cache documentation](docs/architecture/acquisition-cache.md).

Produce the aligned working rasters, display previews, thumbnails, and quality/run reports:

```sh
uv run echoatlas-process-previews \
  --manifest fixtures/demo/selection-manifest.v1.json \
  --data-root data
```

The default run uses an EPSG:32612 one-meter grid, bilinear resampling, exact approved-AOI masking, no speckle filter, and independent 2–98% display stretches. These are engineering preview choices, not calibrated SAR normalization or change detection. See [the SAR preview processing documentation](docs/architecture/sar-preview-processing.md).

Generate the deterministic baseline score, mask, overlay, and pending candidate GeoJSON from the verified preview run:

```sh
uv run echoatlas-change-candidates \
  --preview-run data/derived/echoatlas-bingham-canyon-2025-v1/preview-48b949a1b72ac7f8f54d \
  --data-root data
```

The score threshold, two-pixel registration tolerance, morphology, connectivity, minimum component size, and candidate-count guard are explicit parameters stored with the output. The default policy is an engineering heuristic for human review, not calibrated confidence. See [the baseline change-candidate documentation](docs/architecture/change-candidate-baseline.md).

Stage the validated real comparison for the local workbench:

```sh
uv run echoatlas-prepare-workbench-demo \
  --selection-manifest fixtures/demo/selection-manifest.v1.json \
  --preview-run data/derived/echoatlas-bingham-canyon-2025-v1/preview-48b949a1b72ac7f8f54d \
  --change-run data/derived/echoatlas-bingham-canyon-2025-v1/changes/change-9c8a27b2a55081fc6b07 \
  --output apps/workbench/public/generated-demo
```

The command validates manifest lineage, hashes, sizes, dimensions, the quality report, and all 26 candidate records before atomically staging thumbnails, display evidence, candidate GeoJSON, and a runtime bundle. The destination is Git-ignored. Raw and aligned GeoTIFFs, cache/provider payloads, generated real-data artifacts, and assessment state remain outside version control. The destination must not already exist; remove or archive an earlier generated directory deliberately before rebuilding it.

Generate and validate the tiny deterministic contract demonstration:

```sh
uv run echoatlas-generate-demo-bundle \
  --output data/fixtures/eat007-valid \
  --case valid
uv run echoatlas-validate-bundle \
  --bundle data/fixtures/eat007-valid
```

The generated pixels and metadata are synthetic, CC0-licensed, and contain no Umbra imagery. The validator checks the exact contract version, bounded JSON, safe paths, hashes, sizes, media signatures, partial state, and cross-document references. See [the analysis-bundle v1 documentation](docs/architecture/analysis-bundle-v1.md).

Project a validated bundle into the optional, network-free Palantir import contract:

```sh
uv run echoatlas-plan-palantir-import \
  --bundle data/fixtures/eat007-valid \
  --output data/platform/palantir-import-plan.json
```

This writes a local JSON plan only. It performs no authentication or remote writes. See the [Palantir feasibility spike](docs/platform/palantir-feasibility.md) for the current mapping, authenticated plan/application inventory, and remaining live-validation gates.

Normalize a validated bundle into deterministic CSV tables suitable for the next
Palantir dataset-import checkpoint:

```sh
uv run echoatlas-package-palantir-import \
  --bundle data/fixtures/eat007-valid \
  --output data/platform/palantir-import-package
```

The destination must not already exist. Package version 1.3.0 describes all six
object families, the aggregate relationship table, one two-column join table per
declared link type, and media references. CSV files are emitted only for tables
that contain rows. Zero-row families are marked `upload_ready: false` instead of
producing a header-only file that a target could misinterpret as data. The manifest
contains row counts, columns, and SHA-256 hashes. Nested values use canonical JSON
text inside CSV cells. Recognized object timestamps retain their original RFC3339
columns and add UTC epoch-millisecond companion columns for an explicit target-side
timestamp conversion. Values with sub-millisecond precision fail packaging instead
of being silently truncated. The command still performs no authentication or
remote writes and does not create Ontology resources.

Review the approval-gated [analyst workbench interface specification](docs/design/workbench-interface-v1.md) and [standalone prototype](prototypes/eat-des-001/README.md). The prototype is separate from production React and uses only synthetic design material.

## Delivery

Read [the planning package](plans/README.md), [contribution guide](CONTRIBUTING.md), and [Git workflow](plans/GIT_WORKFLOW.md) before implementation. Every change maps to one Asana `EAT-*` ticket and a dedicated branch.

## Licensing and data

Source code is available under the [MIT License](LICENSE). Imagery, metadata, basemaps, event context, and generated demonstration artifacts retain their own licenses and attribution requirements; see [third-party data](THIRD_PARTY_DATA.md).
