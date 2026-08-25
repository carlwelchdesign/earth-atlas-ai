# Palantir feasibility spike

Status: **provisional adjust with live synthetic Ontology, raster placement, restricted application, generated OSDK, private static hosting, and usage checkpoints** as of 2026-08-25. EchoAtlas can project a validated analysis bundle into a minimal Palantir-shaped import plan. Carl explicitly approved and completed AIP Developer Tier enrollment, the live plan and application catalog were inspected, and an `EchoAtlas` Foundry project was created. The exact tiny synthetic fixture has been uploaded as raw structured files and PNG evidence media; five domain object types and six non-empty link types now back that fixture in the live Ontology. A live Pipeline Builder bridge also converts the acquisition and analysis-run epoch-millisecond companions into native `Timestamp` columns. A separately generated synthetic GeoTIFF is connected through a sixth, raster-specific Ontology object type and persists as a native Map layer without uploading real Umbra pixels. A restricted public-client application now exposes those six object types and six link types through read-only operations, its generated OSDK is published inside the enrollment, and a synthetic-only workbench build is live on a private Foundry-hosted domain. No real Umbra imagery, API keys, client secrets, service users, action types, functions, or write operations were added.

## Decision

Use Palantir only as an optional downstream ontology, media, governance, and application-hosting layer. Keep EchoAtlas's deterministic SAR processing, analysis-bundle contract, local workbench, and assessment history portable and independently usable.

This is an **adjust**, not a full go:

- proceed with the network-free mapping contract and a future thin executor;
- do not make Foundry, AIP, or an OSDK application part of the standalone runtime;
- do not move candidate scoring, evidence policy, or assessment semantics into a Palantir-only implementation;
- defer OSDK integration into the hosted UI, cleanup validation, real-imagery behavior, and the final go/no-go until the remaining evidence and approval gates are satisfied.

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

Foundry reported “Unable to infer a schema for this dataset” for the heterogeneous raw JSON/GeoJSON bundle. This proves the bundle can be retained as a raw file collection, not that it is immediately tabular or Ontology-ready. EchoAtlas now provides a deterministic normalization package with one CSV per object family, a compatibility aggregate link CSV, one two-column join CSV per declared link type, one media-reference CSV, and a hashed manifest. Scalar properties become columns and nested properties use canonical JSON text. The raw source files remain the portable source of truth.

The live checkpoint resolves enrollment, plan-name, high-level capacity, application-catalog, raw-file import, PNG and TIFF media-set creation, schema inference for non-empty normalized CSV tables, the minimum object/link mapping, the bounded timestamp transform path, native synthetic GeoTIFF placement in Map, restricted read-only application configuration, OSDK generation, private static hosting, and current enrollment-wide usage reporting. It does not yet prove that the hosted UI consumes the generated OSDK, real-imagery behavior, scale or performance characteristics, per-operation cost attribution, or cleanup behavior.

### Live restricted application, OSDK, and hosting checkpoint

The approved `EchoAtlas Restricted Synthetic Test` application is enabled at RID `ri.third-party-applications.main.application.3e7f3b17-5771-449c-a8b0-6a05769fa8f7`. It is a public client using user permissions and Authorization Code Grant; it has local and Foundry-hosted callback URLs, but no client secret or service user. Resource restrictions are **Restricted** to these six object types and their six link types: `Echo Atlas Normalized Acquisition`, `EchoAtlas Analysis Run`, `EchoAtlas Area of Interest`, `EchoAtlas Change Candidate`, `EchoAtlas Evidence Artifact`, and `EchoAtlas Synthetic Raster`. The application includes zero action types, functions, interfaces, or projects.

Operation restrictions are **Restricted** to `api:use-ontologies-read` and `api:use-mediasets-read`. Ontology write and media-set write were explicitly removed, and no other operation was enabled. Marking restrictions remain **Unrestricted**, which does not bypass access controls: effective access remains the intersection of the signed-in user's permissions and the application's resource and operation restrictions.

Developer Console generated and published `@echoatlas-restricted-synthetic-test/sdk@0.1.0` with generator version `2.58.0`. The package contains the six selected object types and six link types, with zero actions, functions, or interfaces. This proves application-specific OSDK generation; the current hosted UI does not yet import or call that package.

Foundry Website Hosting deployed asset version `0.2.0` to `https://echoatlas-restricted-test-teae6zflavlbtz3q.apps.usw-3.palantirfoundry.com/`. The uploaded archive contains five files: the application shell, one JavaScript bundle, one stylesheet, and the two deterministic synthetic SVG fixtures. The gitignored prepared real Bingham Canyon directory was removed from the distribution before packaging, so no real Umbra pixels or generated real-data bundle were uploaded. Production browser verification confirmed the synthetic fixture label, the interpretation boundary, three pending candidates, and the explicit `no Umbra pixels represented` attribution.

The first uploaded asset (`0.1.0`) exposed a static-host fallback edge case: an unknown `/generated-demo/bundle.json` route returned the HTML application shell with status 200, which the client attempted to parse as JSON. The client now treats an HTML shell response as an absent prepared bundle and uses the explicit synthetic fallback, while malformed responses that claim to be JSON still fail closed. Asset `0.2.0` contains that fix and is the deployed version.

The Developer Tier allows the private hosted domain but does not support custom IP-address range allowlists; Control Panel requires a plan upgrade for that feature. The approved attempt to add only the current connection therefore made no network-policy change. No country rule or broader CIDR was added.

### Live usage checkpoint

At the 2026-08-25 checkpoint, enrollment-wide Resource Management reported the following **Last 30 days** totals:

| Meter | Reported value |
| --- | ---: |
| Foundry compute | 0.00 compute-seconds |
| Ontology volume | 0.00 GB-months |
| Foundry storage | 0.00 GB-months |

The overview also reported no usage for top accounts, projects/ontologies, sources, or resources. The synthetic GeoTIFF media-set detail separately reported `0.00` compute-hours in the previous week and `0.00 B` on 2026-08-24. These are live displayed values, not proof that every previously created resource is free or that future processing will remain at zero; small values may round to zero, model usage is metered separately, and exact Developer Tier quota ceilings remain undisclosed.

Resource Management identified the AIP tier as **Small**. In the **Last 24 hours** view, the enrollment showed Claude Haiku 4.5 at `300K TPM / 200 RPM` with 32K tokens across 8 requests, and `text-embedding-ada-002` at `2.4M TPM / 2.4K RPM` with 629 tokens across 26 requests. Both rows reported zero project/user and enrollment rate-limit hits. This is enrollment-level activity and is not attributed to an EchoAtlas application. EchoAtlas does not require AIP for its deterministic adapter or standalone workbench.

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

The header-only assessment behavior invalidated package version 1.0.0's assumption that an empty CSV could safely represent a zero-row object family. Package version 1.1.0 records that family in the manifest with `row_count: 0`, `upload_ready: false`, and `omission_reason: no_rows`, and emits no assessment CSV. Package version 1.2.0 applies the same rule to every declared link type and adds dedicated two-column join tables while preserving the aggregate link table for compatibility. Package version 1.3.0 preserves each recognized RFC3339 object timestamp and adds a UTC epoch-millisecond companion column for deterministic target conversion. An empty Ontology type or link requires an explicitly defined schema or a future valid assessment event; EchoAtlas will not invent a row to force inference.

### Live Ontology resources

The approved Ontology checkpoint created five object types from the non-empty synthetic tables. `AnalystAssessment` remains intentionally absent because the fixture contains no valid assessment event and the invalid zero-row dataset is never used.

| Object type | Live rows / mapped properties | Ontology RID |
| --- | --- | --- |
| EchoAtlas Area of Interest | 1 row / 7 properties | `ri.ontology.main.object-type.7d82106a-dcfe-4693-93b3-ec0d33bbd230` |
| Echo Atlas Normalized Acquisition | 2 rows / 13 properties, including native `Acquired At` Timestamp | `ri.ontology.main.object-type.e9e52fa7-7ad0-4b0a-9a9a-fb1a4ad4cff0` |
| EchoAtlas Analysis Run | 1 row / 10 properties, including native `Created At` Timestamp | `ri.ontology.main.object-type.470eed9a-55e5-40ac-968c-b581d94e90f4` |
| EchoAtlas Evidence Artifact | 4 rows / 10 properties | `ri.ontology.main.object-type.d85965ef-f0f2-4853-a27f-82069830027e` |
| EchoAtlas Change Candidate | 1 row / 12 properties | `ri.ontology.main.object-type.435f50f8-8eee-4f9e-b8d1-07f50240ad0b` |

Direct mapping exposed a timestamp boundary: Ontology Manager proposed `Struct<Timestamp,Offset>` for `acquired_at` and `created_at`, while the backing datasets reported `offsetdatetimeudt` to the indexer. Package version 1.3.0 therefore preserves those source strings and emits `acquired_at_epoch_millis`, `created_at_epoch_millis`, and, when assessments exist, `recorded_at_epoch_millis`. Offsets are normalized to the same UTC instant, and sub-millisecond values are rejected instead of truncated. Palantir documents an [Epoch milliseconds to timestamp](https://www.palantir.com/docs/foundry/pipeline-builder/functions-index#epoch-milliseconds-to-timestamp) Pipeline Builder expression whose output type is `Timestamp`, which is a [supported Ontology property type](https://www.palantir.com/docs/foundry/object-link-types/properties-overview#supported-property-types).

The approved live timestamp checkpoint exercised that contract in the batch pipeline `EchoAtlas Timestamp Bridge` (`ri.eddie.main.pipeline.bed724ca-d984-449b-9b94-1694e2ff6ee4`). Build `ri.foundry.main.build.40085d69-687c-4902-b252-f27434e9c6dc` finished both outputs:

| Timestamp path | Source dataset | Output dataset | Verified native values |
| --- | --- | --- | --- |
| Acquisition | `ri.foundry.main.dataset.65ed10ed-9f72-4952-84f4-f5533f8f7839` | `ri.foundry.main.dataset.f13bcb55-2c6e-4823-b601-03e28c4217eb` | `2025-02-10T12:00:00.000Z`, `2025-01-10T12:00:00.000Z` |
| Analysis run | `ri.foundry.main.dataset.15f488a9-b8d5-40d7-8fb2-b44b5be86603` | `ri.foundry.main.dataset.4b8d66b7-02df-4b50-b2f4-9c18a79d3432` | `2026-01-15T12:00:00.000Z` |

Foundry reports `acquired_at_timestamp` and `created_at_timestamp` as native timestamp columns. The two object types now use the output datasets as backing datasources while preserving their primary keys, object counts, and existing link-type topology. Post-remap verification found both object types and all six existing relation RIDs indexed. The transform gate is complete for the approved synthetic checkpoint; this does not establish production scheduling, real-imagery ingestion, or cost behavior.

### Live synthetic GeoTIFF ingestion

The approved raster checkpoint generated a deterministic 64-by-64, single-band `uint8` GeoTIFF solely for platform validation. It declares EPSG:4326, bounds `(-112.2, 40.45, -112.05, 40.6)`, nodata `0`, DEFLATE compression, and synthetic-purpose tags. Its SHA-256 is `1082c0c0e3fd59a29e62733bd9b8449cc6479fb78886bb6a528072a9f21df975`; its local and live reported size is 1.6 KB. The file contains generated values, not Umbra or other observed pixels.

The live `EchoAtlas Synthetic GeoTIFF Validation` media set is `ri.mio.main.media-set.9c715a70-74d8-46fc-8bf9-06a5c85bf0af`; its view is `ri.mio.main.view.43aec2dc-bf66-44ec-ad93-b73d432dad17`. The TIFF upload produced media item `ri.mio.main.media-item.01a039e3-afe7-71f7-aa64-2beb8944e24d`. Foundry reports one Image/TIFF item and its detail view renders the pixels while reporting TIFF, 1.6 KB, one page, and 64-by-64 dimensions. The media-set overview still reports aggregate size as `0B`, matching the earlier PNG media-set accounting caveat.

This proves that the live enrollment can create a TIFF media set, accept a georeferenced TIFF, retain it as a media item, and render its pixel content. The media detail UI does not expose the embedded CRS, transform, or bounds. Palantir's [raster-data workflow](https://www.palantir.com/docs/foundry/geospatial/raster-data) says map display additionally requires an Ontology object with a media-reference property and the backing media set declared in that object's capabilities.

A read-only Map checkpoint first opened a new unsaved map and inspected **Add to map** without saving it. The **Objects** view reported that it was showing only mappable objects and that no object types matched; the existing five EchoAtlas domain object types were therefore not available as map layers. The **Overlays** view exposed only the default Day/Night overlay, and searching it for `EchoAtlas` returned no results. This negative result confirmed that a retained or previewable GeoTIFF media item does not automatically become a Map overlay.

### Live synthetic raster placement

With Carl's explicit approval, the follow-up checkpoint exercised the documented media-reference path using only the existing 64-by-64 synthetic GeoTIFF. The batch pipeline `EchoAtlas Synthetic Raster Reference` (`ri.eddie.main.pipeline.3108f4f3-10ca-4c8d-99bf-50f2730617e8`) reads the existing media set directly as a tabular input and deployed successfully with one row, four columns, and one passing expectation. Its backing dataset is `ri.foundry.main.dataset.fabf099a-4032-4080-bfdd-174e3188ef95`.

The pipeline created the indexed object type `EchoAtlas Synthetic Raster` (`ri.ontology.main.object-type.97a34e0c-430e-4b7e-b1a3-67a76c9f5b97`, API name `EchoAtlasSyntheticRaster`) with one object and four properties: timestamp, path, media reference, and media item RID. The media item RID is the primary key. Ontology Manager automatically recognized the `Media Reference` property and registered the existing `EchoAtlas Synthetic GeoTIFF Validation` media set in the object's capabilities with inherited markings.

After deployment, Map's mappable-object results increased from four enrollment examples to five and included the one `EchoAtlas Synthetic Raster` object. Its media-reference value resolved to the exact synthetic media-set, view, and item RIDs documented above. Adding the object created an `EchoAtlas Synthetic Rasters` layer with one object and moved the live map to a 2 km scale. The saved template `EchoAtlas Synthetic Raster Placement` persists at `ri.opus.main.map-template.f8dd42c2-2c6e-4802-8074-1820cabad9ab`; reopening that resource reproduced the template name, layer count, and 2 km map state.

This closes the bounded synthetic media-reference, capability, and native Map-placement gate. It does not validate real Umbra imagery, multi-scene performance, scale limits, cost, permissions, application integration, or cleanup. The raster object, pipeline, backing dataset, and Map template are test resources and are not part of the standalone EchoAtlas runtime.

Each non-empty relationship is backed by its own two-column join dataset. The one-row run-to-candidate dataset required an explicit **Apply a schema** step after automatic inference initially failed.

| Link type | Rows | Join dataset RID | Relation RID |
| --- | ---: | --- | --- |
| Acquisition Covers AOI | 2 | `ri.foundry.main.dataset.d76e21b2-20e7-4847-9943-381ece87fbd5` | `ri.ontology.main.relation.544dfb6d-5af5-4546-b499-4438228c86e4` |
| Run Uses Acquisition | 2 | `ri.foundry.main.dataset.4cd69b11-0e05-41e4-82cb-3a6c3b9d90c5` | `ri.ontology.main.relation.07a139c8-10fe-4b27-ac83-1727014efc52` |
| Run Produces Artifact | 4 | `ri.foundry.main.dataset.06f2e172-7122-4827-ba29-6b05a7fef698` | `ri.ontology.main.relation.5d55cecb-df8b-4384-9c36-5d291c946c97` |
| Run Produces Candidate | 1 | `ri.foundry.main.dataset.15627a0e-cdb7-4323-a401-0ad7daba9074` | `ri.ontology.main.relation.7d5d6266-fdc7-4dfe-b107-e803cbbdb0f5` |
| Candidate Affects AOI | 1 | `ri.foundry.main.dataset.c142c589-ee74-46bd-980f-0e7862215473` | `ri.ontology.main.relation.71c99542-8c86-4919-bdf7-b3bb9e62af31` |
| Candidate References Artifact | 3 | `ri.foundry.main.dataset.a9fd734e-4f24-487d-917b-b13392c3670e` | `ri.ontology.main.relation.9f6c05a9-d62b-4b95-bc8a-f8d2a831ba89` |

The candidate remains synthetic and pending; an Ontology link does not turn it into analyst-confirmed change. No assessment type, assessment links, actions, automations, or cleanup operations were created in this checkpoint.

## Current public evidence

Only Palantir-controlled documentation was used for capability claims. “Verified” below means the public documentation was available; it does not mean the capability was exercised in Carl's enrollment.

| Question | Public evidence | Spike finding |
| --- | --- | --- |
| Developer Tier access | [Developer hub](https://www.palantir.com/docs/foundry/developers) advertises a free Developer Tier account; [getting started](https://www.palantir.com/docs/foundry/getting-started/overview) describes AIP Developer Tier as a trial account. | The authenticated enrollment identifies the current plan as AIP Developer Tier. Duration and commercial conversion terms are not displayed on the plan page and remain a caveat. |
| Tier-wide limits | [Resource Management](https://www.palantir.com/docs/foundry/resource-management) explains compute and storage accounting. Exact Developer Tier quotas are not enumerated on the public pages reviewed. | The live plan reports limited vCPUs, limited GPUs, 60 object types, 60–120K tokens/minute for latest-generation LLMs, and limited users. Resource Management displayed 0.00 compute-seconds, 0.00 ontology GB-months, and 0.00 storage GB-months for the last 30 days. Numeric quota ceilings remain undisclosed. |
| Raster and imagery | [Raster data](https://www.palantir.com/docs/foundry/geospatial/raster-data) documents TIFF/GeoTIFF, NITF, and JPEG2000 as raster media-set formats; PNG and JPEG are file-level formats. [Media limits](https://www.palantir.com/docs/foundry/media-sets-advanced-formats/media-usage-limits) documents per-item and transaction constraints plus compute usage. | Four synthetic PNGs and a separate 1.6 KB synthetic GeoTIFF upload succeeded. The GeoTIFF renders with the expected dimensions and, through a one-object media-reference Ontology type, persists as a native Map layer and saved template at a 2 km scale. This verifies only the bounded synthetic path; real Umbra imagery, scale, performance, and cost remain open. |
| Transforms | [Media transforms](https://www.palantir.com/docs/foundry/pipeline-builder/transforms-transform-media) supports media manipulation and extraction in Pipeline Builder. | Useful for presentation or downstream enrichment, but EchoAtlas processing policy remains outside Foundry. |
| Ontology and SDKs | [Developer Console](https://www.palantir.com/docs/foundry/developer-console/overview) generates application-specific OSDKs from selected Ontology resources. [SDK guidance](https://www.palantir.com/docs/foundry/api/v2/general/overview/sdks) distinguishes portable platform SDKs from enrollment-specific OSDKs. | The restricted application published `@echoatlas-restricted-synthetic-test/sdk@0.1.0` for six object and six link types. The hosted UI does not yet consume it, and the import projection remains independent of generated SDK code. |
| Hosting | [Foundry web hosting](https://www.palantir.com/docs/foundry/developer-console/deploy-custom-application-on-foundry) supports frontend-only static applications and currently documents 1,000 files and a 20 MB upload limit. [Developer Tier hosting announcement](https://www.palantir.com/docs/foundry/announcements/2025-01) explicitly includes Developer Tier enrollments. | Synthetic-only asset `0.2.0` is live on the private Foundry domain. Hosting serves the frontend only; the Python processing backend remains outside Foundry. Custom IP-range allowlists are unavailable on this Developer Tier plan. |
| AIP | [AIP enablement](https://www.palantir.com/docs/foundry/aip/enable-aip-features) says AIP is enabled by default in new enrollments while individual model families require administrator enablement and terms. [Supported LLMs](https://www.palantir.com/docs/foundry/aip/supported-llms) makes availability enrollment-, region-, and legal-state-dependent. [AIP compute usage](https://www.palantir.com/docs/foundry/aip/aip-compute-usage) meters token use in compute-seconds. | The live Model Catalog exposes 54 stable, 11 experimental, and 8 sunset entries, including current recommended GPT-5.6, Claude 5, Gemini 3.x, and Grok families. Resource Management identifies a Small AIP tier and showed limited recent enrollment activity with no rate-limit hits. Catalog exposure and unrelated enrollment activity do not prove EchoAtlas invocation, terms acceptance, or zero cost. AIP remains separate from EAT-013 and is not needed for this adapter. |
| Restricted access | [Application restrictions](https://www.palantir.com/docs/foundry/developer-console/application-restrictions) states applications are restricted by default and tokens are bounded by user permissions, application resource/operation restrictions, and requested scopes. | The enabled test application restricts resources to six object and six link types and operations to Ontology read plus media-set read. It has no actions, functions, projects, write operations, client secret, or service user. |

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
preserve stable primary keys; the aggregate link table preserves typed source and
target identities; dedicated link-type tables expose only the two endpoint keys
needed by Foundry join datasets; and the media table contains only available
artifacts. An object or link family with no records, such as the synthetic fixture's
assessment families, remains in the manifest but emits no CSV and is explicitly
marked non-uploadable.

This solves the local heterogeneous-file normalization problem. It does not prove
Foundry schema inference or perform remote writes. The approved live checkpoint
used its output to create the resources documented above; the exporter itself
remains network-free.

## Live validation gate

Explicit owner approval is required before the remaining spike:

1. [x] Create and authenticate to a Developer Tier enrollment with Carl's explicit approval.
2. [ ] Complete the plan evidence: high-level limits, enabled applications, and current numeric usage are captured, but numeric compute/storage/GPU/user quota ceilings and country/term limits remain unavailable.
3. [x] Media-set creation, catalog-level model state, normalized object/link resources, the synthetic timestamp transform path, bounded GeoTIFF ingestion, Ontology media-reference/capability creation, and native synthetic Map placement are confirmed.
4. [x] Generate an application-specific OSDK and deploy a synthetic-only static workbench without coupling the standalone runtime to Palantir. The hosted UI-to-OSDK integration remains a separate open step.
5. [x] Configure a restricted test application and record its exact resources and read-only operation scopes.
6. [ ] The exact synthetic bundle is present as raw files and media. Non-empty normalized datasets and the live Ontology preserve expected row counts, object identities, typed link endpoints, available-media references, and native acquisition/run timestamps. Empty-family behavior is guarded locally. Deletion/cleanup behavior remains open.
7. [ ] Current usage values, limitations, and durable live resource evidence are recorded; screenshot capture and the final go/adjust/no-go decision remain open.

Real Umbra imagery remains outside the live spike until its storage, license, sensitivity, and usage implications are separately reviewed.
