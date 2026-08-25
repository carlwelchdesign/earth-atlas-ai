# Palantir feasibility spike

Status: **provisional adjust with a live synthetic-import checkpoint** as of 2026-08-24. EchoAtlas can project a validated analysis bundle into a minimal Palantir-shaped import plan. Carl explicitly approved and completed AIP Developer Tier enrollment, the live plan and application catalog were inspected, and an `EchoAtlas` Foundry project was created. The exact tiny synthetic fixture has been uploaded as raw structured files and PNG evidence media. No real Umbra imagery, credentials, API keys, OAuth clients, EchoAtlas Ontology objects, or applications have been created.

## Decision

Use Palantir only as an optional downstream ontology, media, governance, and application-hosting layer. Keep EchoAtlas's deterministic SAR processing, analysis-bundle contract, local workbench, and assessment history portable and independently usable.

This is an **adjust**, not a full go:

- proceed with the network-free mapping contract and a future thin executor;
- do not make Foundry, AIP, or an OSDK application part of the standalone runtime;
- do not move candidate scoring, evidence policy, or assessment semantics into a Palantir-only implementation;
- defer a normalized Ontology import, restricted application configuration, cleanup validation, and the final go/no-go until the remaining evidence and approval gates are satisfied.

## Live enrollment evidence

The authenticated `earth-atlas-app` enrollment reports **AIP Developer Tier** as the current plan with the following limits:

- limited vCPUs;
- limited GPUs;
- 60 object types;
- 60–120K tokens per minute for latest-generation LLMs, with higher limits for other models;
- limited users.

The plan page does not publish numeric vCPU, GPU, or user quotas. The live Foundry home exposes Projects & Files, Data Connection, Pipeline Builder, Contour, Ontology Manager, Workshop, AIP Logic, Code Repositories, and AIP Assist. Exposure in the application catalog proves that the application is available to the enrollment; it does not prove that every connector, model family, operation, or administrative permission is enabled.

A Foundry project named `EchoAtlas` was created with the description “SAR intelligence workbench for evidence review, change-candidate triage, and analyst assessment.” Its RID is `ri.compass.main.folder.bcc541c1-3ee8-472c-abd9-00a625177310`.

The approved synthetic checkpoint created two additional remote resources:

- `EchoAtlas Synthetic Bundle Records`, dataset RID `ri.foundry.main.dataset.e8ddf29e-a9a8-4eba-9dc6-31c16ba00882`, containing the fixture's six structured JSON/GeoJSON files (8.4 KB reported by Foundry); and
- an image media set, RID `ri.mio.main.media-set.b60973e7-8855-4253-be81-b15cdab72867`, containing `before.png`, `after.png`, `candidate-overlay.png`, and `change-score.png`. All four uploads succeeded. The media-set overview reports four items but `0B`, so byte-usage accounting is not treated as verified.

Foundry reported “Unable to infer a schema for this dataset” for the heterogeneous raw JSON/GeoJSON bundle. This proves the bundle can be retained as a raw file collection, not that it is immediately tabular or Ontology-ready. EchoAtlas now provides a deterministic normalization package with one CSV per object family, one link CSV, one media-reference CSV, and a hashed manifest. Scalar properties become columns and nested properties use canonical JSON text. The raw source files remain the portable source of truth.

The live checkpoint resolves enrollment, plan-name, high-level capacity, application-catalog, raw-file import, PNG media-set creation, and schema inference for non-empty normalized CSV tables. It does not yet resolve raster-native geospatial behavior, transform execution, Ontology object/link creation, OSDK/static-hosting configuration, restricted application scopes, usage impact, or cleanup behavior.

### Live normalized datasets

The approved normalized-import checkpoint created one small raw dataset per CSV so schemas were not mixed:

| Logical table | Live result | Dataset RID |
| --- | --- | --- |
| Area of interest | 1 row, 7 columns | `ri.foundry.main.dataset.4a4b11e0-990d-43f4-be3b-47e151169613` |
| Acquisition | 2 rows, 13 columns | `ri.foundry.main.dataset.a5ad41ac-0b91-4e5b-ba45-b6ed46c655b5` |
| Analysis run | 1 row, 10 columns | `ri.foundry.main.dataset.7d385b94-d59c-4383-8419-474051382258` |
| Evidence artifact | 4 rows, 10 columns | `ri.foundry.main.dataset.13628647-6005-41b5-9924-e54068870435` |
| Change candidate | 1 row, 12 columns | `ri.foundry.main.dataset.bac8ffcc-5ae7-40a0-b12b-103f27061014` |
| Analyst assessment | Source had 0 rows; Foundry incorrectly interpreted the header-only CSV as 1 row with two `untitled_column_*` string columns. This dataset is invalid and must not back an object type. | `ri.foundry.main.dataset.fb95ac11-4b2f-4fc5-8cea-0747a0a82575` |
| Ontology links | 13 rows, 5 columns | `ri.foundry.main.dataset.2c1bf615-7df9-4734-8c0f-25f5902665f4` |
| Media references | 4 rows, 5 columns | `ri.foundry.main.dataset.f7ff5093-412e-4035-9ff9-483b83c522c1` |

Foundry preserved the declared identity/link column names. It inferred acquisition and run timestamps as `datetime`, artifact `required` as `boolean`, and artifact/media byte sizes as `integer`; canonical nested JSON remained `string`. These are live schema observations, not Ontology objects or links.

The header-only assessment behavior invalidated package version 1.0.0's assumption that an empty CSV could safely represent a zero-row object family. Package version 1.1.0 records that family in the manifest with `row_count: 0`, `upload_ready: false`, and `omission_reason: no_rows`, and emits no assessment CSV. An empty Ontology type requires an explicitly defined schema or a future valid assessment event; EchoAtlas will not invent a row to force inference.

## Current public evidence

Only Palantir-controlled documentation was used for capability claims. “Verified” below means the public documentation was available; it does not mean the capability was exercised in Carl's enrollment.

| Question | Public evidence | Spike finding |
| --- | --- | --- |
| Developer Tier access | [Developer hub](https://www.palantir.com/docs/foundry/developers) advertises a free Developer Tier account; [getting started](https://www.palantir.com/docs/foundry/getting-started/overview) describes AIP Developer Tier as a trial account. | The authenticated enrollment identifies the current plan as AIP Developer Tier. Duration and commercial conversion terms are not displayed on the plan page and remain a caveat. |
| Tier-wide limits | [Resource Management](https://www.palantir.com/docs/foundry/resource-management) explains compute and storage accounting. Exact Developer Tier quotas are not enumerated on the public pages reviewed. | The live plan reports limited vCPUs, limited GPUs, 60 object types, 60–120K tokens/minute for latest-generation LLMs, and limited users. Numeric compute, storage, GPU, and user quotas remain undisclosed. |
| Raster and imagery | [Raster data](https://www.palantir.com/docs/foundry/geospatial/raster_data/) documents TIFF/GeoTIFF, NITF, and JPEG2000 as raster media-set formats; PNG and JPEG are file-level formats. [Media limits](https://www.palantir.com/docs/foundry/media-sets-advanced-formats/media-usage-limits) documents per-item and transaction constraints plus compute usage. | The live image media-set form exposes PNG, BMP, JP2K, JPG, NITF, TIFF, and WEBP and accepted all four synthetic PNGs with PNG as the primary format. This verifies file/media evidence only, not georeferencing or raster-native layers. A future raster-native path needs a bounded GeoTIFF or another documented raster format. |
| Transforms | [Media transforms](https://www.palantir.com/docs/foundry/pipeline-builder/transforms-transform-media) supports media manipulation and extraction in Pipeline Builder. | Useful for presentation or downstream enrichment, but EchoAtlas processing policy remains outside Foundry. |
| Ontology and SDKs | [Developer Console](https://www.palantir.com/docs/foundry/developer-console/overview) generates application-specific OSDKs from selected Ontology resources. [SDK guidance](https://www.palantir.com/docs/foundry/api/v2/general/overview/sdks) distinguishes portable platform SDKs from enrollment-specific OSDKs. | Use an enrollment-specific OSDK for a Palantir UI; keep the import projection independent of generated SDK code. |
| Hosting | [Foundry web hosting](https://www.palantir.com/docs/foundry/developer-console/deploy-custom-application-on-foundry) supports frontend-only static applications and currently documents 1,000 files and a 20 MB upload limit. [Developer Tier hosting announcement](https://www.palantir.com/docs/foundry/announcements/2025-01) explicitly includes Developer Tier enrollments. | A built React workbench may fit, but no backend or Python processing can run in that hosting feature. |
| AIP | [AIP enablement](https://www.palantir.com/docs/foundry/aip/enable-aip-features) says AIP is enabled by default in new enrollments while individual model families require administrator enablement and terms. [Supported LLMs](https://www.palantir.com/docs/foundry/aip/supported-llms) makes availability enrollment-, region-, and legal-state-dependent. [AIP compute usage](https://www.palantir.com/docs/foundry/aip/aip-compute-usage) meters token use in compute-seconds. | The live Model Catalog exposes 54 stable, 11 experimental, and 8 sunset entries, including current recommended GPT-5.6, Claude 5, Gemini 3.x, and Grok families. Catalog exposure does not prove successful invocation, terms acceptance, or zero cost. AIP remains separate from EAT-013 and is not needed for this adapter. |
| Restricted access | [Application restrictions](https://www.palantir.com/docs/foundry/developer-console/application-restrictions) states applications are restricted by default and tokens are bounded by user permissions, application resource/operation restrictions, and requested scopes. | Developer Console is live and currently contains zero applications. Any future application must enumerate only its object types, actions, project resources, and public API operations. No application, OAuth client, API key, or credential was created during this checkpoint. |

## Minimal Ontology mapping

| EchoAtlas bundle record | Palantir object type | Stable identity in the local plan | Links |
| --- | --- | --- | --- |
| `aoi.geojson` | `AreaOfInterest` | AOI ID; geometry hash remains a property | covered by acquisitions; affected by candidates |
| `acquisitions.json` | `Acquisition` | provider plus source item ID | covers AOI; used by run |
| `manifest.json` | `AnalysisRun` | processing run ID plus manifest checksum | uses acquisitions; produces artifacts and candidates |
| manifest artifact record | `EvidenceArtifact` | bundle, artifact ID, and checksum | produced by run; referenced by candidates and assessments |
| candidate feature | `ChangeCandidate` | change run ID plus candidate ID | produced by run; affects AOI; references artifacts |
| append-only assessment event | `AnalystAssessment` | bundle plus assessment ID | assesses candidate; references artifacts; optionally supersedes a prior assessment |

The mapper represents missing artifacts as metadata but never schedules them for upload. It preserves candidate and assessment language from the validated bundle and performs no alerts, AI inference, external actions, or remote writes.

## Local projection

Generate a deterministic import plan from any valid analysis bundle:

```sh
uv run echoatlas-plan-palantir-import \
  --bundle data/fixtures/eat007-valid \
  --output data/platform/palantir-import-plan.json
```

The command validates the bundle before mapping it. Its output explicitly records `requires_authenticated_target: true` and `writes_performed: false`. It does not install a Palantir SDK, request credentials, or contact a Palantir endpoint.

Normalize the plan into stable tabular files:

```sh
uv run echoatlas-package-palantir-import \
  --bundle data/fixtures/eat007-valid \
  --output data/platform/palantir-import-package
```

The exporter writes atomically into a destination that must not already exist,
preventing stale rows from surviving a later package. The package manifest records
the source bundle and import-plan hashes plus every table's columns and row count.
Non-empty entries also include an upload-ready path and SHA-256 hash. Object tables
preserve stable primary keys; the link table preserves typed source and target
identities; and the media table contains only available artifacts. An object family
with no records, such as the synthetic fixture's assessment family, remains in the
manifest but emits no CSV and is explicitly marked non-uploadable.

This solves the local heterogeneous-file normalization problem. It does not prove
Foundry schema inference, create datasets or Ontology resources, configure links,
or perform remote writes.

## Live validation gate

Explicit owner approval is required before the remaining spike:

1. [x] Create and authenticate to a Developer Tier enrollment with Carl's explicit approval.
2. [ ] Complete the plan evidence: high-level limits and enabled applications are captured, but numeric compute/storage/GPU/user quotas and country/term limits remain unavailable.
3. [ ] Media-set creation and catalog-level model state are confirmed. Raster-native behavior, transforms, normalized Ontology resources, and OSDK/static-hosting configuration remain open.
4. [ ] Configure a restricted test application and record its exact resources and operation scopes.
5. [ ] The exact synthetic bundle is present as raw files and media. Non-empty normalized datasets preserve expected row counts, columns, object identities, typed link endpoints, and available-media references. Empty-family behavior is now guarded locally. Ontology verification and deletion/cleanup behavior remain open.
6. [ ] Record durable visual evidence, usage impact, limitations, and the final go/adjust/no-go decision.

Real Umbra imagery remains outside the live spike until its storage, license, sensitivity, and usage implications are separately reviewed.
