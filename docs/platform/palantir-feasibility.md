# Palantir feasibility spike

Status: **provisional adjust** as of 2026-08-24. EchoAtlas can project a validated analysis bundle into a minimal Palantir-shaped import plan, but no Palantir account was created, no enrollment was authenticated, and no remote resource was changed. Live Developer Tier quotas and enabled products remain unverified.

## Decision

Use Palantir only as an optional downstream ontology, media, governance, and application-hosting layer. Keep EchoAtlas's deterministic SAR processing, analysis-bundle contract, local workbench, and assessment history portable and independently usable.

This is an **adjust**, not a full go:

- proceed with the network-free mapping contract and a future thin executor;
- do not make Foundry, AIP, or an OSDK application part of the standalone runtime;
- do not move candidate scoring, evidence policy, or assessment semantics into a Palantir-only implementation;
- defer live import, authentication, screenshots, and the final go/no-go until Carl explicitly approves enrollment access.

## Current public evidence

Only Palantir-controlled documentation was used for capability claims. “Verified” below means the public documentation was available; it does not mean the capability was exercised in Carl's enrollment.

| Question | Public evidence | Spike finding |
| --- | --- | --- |
| Developer Tier access | [Developer hub](https://www.palantir.com/docs/foundry/developers) advertises a free Developer Tier account; [getting started](https://www.palantir.com/docs/foundry/getting-started/overview) describes AIP Developer Tier as a trial account. | Signup exists, but the mixed free/trial language means duration and commercial terms must be checked during enrollment. |
| Tier-wide limits | [Resource Management](https://www.palantir.com/docs/foundry/resource-management) explains compute and storage accounting. Exact Developer Tier quotas are not enumerated on the public pages reviewed. | The authenticated enrollment's plan/usage screens are required evidence before importing real artifacts or invoking AIP. |
| Raster and imagery | [Raster data](https://www.palantir.com/docs/foundry/geospatial/raster_data/) documents TIFF/GeoTIFF, NITF, and JPEG2000 as raster media-set formats; PNG and JPEG are file-level formats. [Media limits](https://www.palantir.com/docs/foundry/media-sets-advanced-formats/media-usage-limits) documents per-item and transaction constraints plus compute usage. | Current EchoAtlas PNG previews can be media evidence, but they are not raster-native geospatial layers. A future raster-native path needs bounded GeoTIFF or another documented raster format. |
| Transforms | [Media transforms](https://www.palantir.com/docs/foundry/pipeline-builder/transforms-transform-media) supports media manipulation and extraction in Pipeline Builder. | Useful for presentation or downstream enrichment, but EchoAtlas processing policy remains outside Foundry. |
| Ontology and SDKs | [Developer Console](https://www.palantir.com/docs/foundry/developer-console/overview) generates application-specific OSDKs from selected Ontology resources. [SDK guidance](https://www.palantir.com/docs/foundry/api/v2/general/overview/sdks) distinguishes portable platform SDKs from enrollment-specific OSDKs. | Use an enrollment-specific OSDK for a Palantir UI; keep the import projection independent of generated SDK code. |
| Hosting | [Foundry web hosting](https://www.palantir.com/docs/foundry/developer-console/deploy-custom-application-on-foundry) supports frontend-only static applications and currently documents 1,000 files and a 20 MB upload limit. [Developer Tier hosting announcement](https://www.palantir.com/docs/foundry/announcements/2025-01) explicitly includes Developer Tier enrollments. | A built React workbench may fit, but no backend or Python processing can run in that hosting feature. |
| AIP | [AIP enablement](https://www.palantir.com/docs/foundry/aip/enable-aip-features) says AIP is enabled by default in new enrollments while individual model families require administrator enablement and terms. [Supported LLMs](https://www.palantir.com/docs/foundry/aip/supported-llms) makes availability enrollment-, region-, and legal-state-dependent. [AIP compute usage](https://www.palantir.com/docs/foundry/aip/aip-compute-usage) meters token use in compute-seconds. | AIP cannot be assumed available or free for EchoAtlas. It remains separate from EAT-013 and is not needed for this adapter. |
| Restricted access | [Application restrictions](https://www.palantir.com/docs/foundry/developer-console/application-restrictions) states applications are restricted by default and tokens are bounded by user permissions, application resource/operation restrictions, and requested scopes. | Any future application must enumerate only its object types, actions, project resources, and public API operations. An unscoped application is out of scope. |

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

## Live validation gate

Explicit owner approval is required before the remaining spike:

1. Create or authenticate to a Developer Tier enrollment.
2. Capture the enrollment plan, compute/storage quotas, country/term limits, and enabled products.
3. Confirm media-set creation, raster support, transforms, Ontology/OSDK resources, web hosting, and AIP state in that enrollment.
4. Configure a restricted test application and record its exact resources and operation scopes.
5. Import only the synthetic bundle first; verify object identities, links, media references, and deletion/cleanup behavior.
6. Record screenshots, usage impact, limitations, and the final go/adjust/no-go decision.

Real Umbra imagery remains outside the live spike until its storage, license, sensitivity, and usage implications are separately reviewed.
