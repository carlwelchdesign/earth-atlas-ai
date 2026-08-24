# EchoAtlas

EchoAtlas is a planned civilian disaster and infrastructure-change SAR intelligence workbench. It will turn public Umbra imagery into deterministic change candidates, evidence, and human-reviewed assessments.

**Current status:** the Bingham Canyon civilian demonstration pair is approved and pinned, and the backend can fetch those exact public Umbra objects into a bounded, checksum-verified local cache. It does not yet process SAR pixels, produce change candidates, or provide operational intelligence.

## Architecture

- `services/backend`: Python modular backend with a thin FastAPI boundary and an independent processing domain.
- `apps/workbench`: React and TypeScript analyst application.
- `schemas`: future versioned analysis-bundle contracts.
- `fixtures/demo`: future small, licensed demonstration artifacts.
- `plans`: canonical product, architecture, governance, and execution plans.

The portable analysis bundle is the boundary between processing, UI, tests, and future platform adapters. Palantir remains an optional later adapter rather than a required runtime.

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

## Delivery

Read [the planning package](plans/README.md), [contribution guide](CONTRIBUTING.md), and [Git workflow](plans/GIT_WORKFLOW.md) before implementation. Every change maps to one Asana `EAT-*` ticket and a dedicated branch.

## Licensing and data

Source code is available under the [MIT License](LICENSE). Imagery, metadata, basemaps, event context, and generated demonstration artifacts retain their own licenses and attribution requirements; see [third-party data](THIRD_PARTY_DATA.md).
