# EchoAtlas planning package

Status: EAT-001 through EAT-011, EAT-DES-001, and EAT-016 are complete. EAT-012 remains in qualified-review and adjudication. EAT-014 has a network-free bundle-to-Ontology projection, a zero-row-safe version 1.3.0 normalized-table package, an authenticated Developer Tier inventory, live raw/media/normalized synthetic imports, five domain object types linked by six dataset-backed relations, a verified live epoch-millisecond-to-`Timestamp` bridge for Acquisition and Analysis Run, and a sixth media-reference object type that places the bounded synthetic GeoTIFF in a persistent native Map template. A restricted read-only application, generated OSDK, and private Foundry-hosted workbench are verified. Deployed asset `0.4.0` completes the exact-host browser-OAuth/OSDK boundary and serves the bounded real-derived Bingham Canyon evidence profile: two 361×512 images, 26 candidate records, the approved central-pit boundary, licensing, and an explicit warning that optional full-resolution diagnostics are omitted. Raw GeoTIFFs and provider payloads remain outside Foundry, so Media Set/Ontology-backed real imagery, cleanup behavior, durable screenshot evidence, and the final decision remain open.

EchoAtlas is a civilian disaster and infrastructure-change SAR intelligence workbench. The first release will prove one end-to-end analyst workflow with public Umbra data: select a comparable image pair, produce deterministic change candidates, inspect the evidence, and record a human assessment.

Post-MVP milestone M5 expands that proven workflow with a global **Explore** mode: a MapLibre globe and equivalent accessible results list let users define a civilian AOI, inspect truthful Umbra and Sentinel-1 catalog availability, select a candidate pair, and hand it to the existing **Analyze** workflow. Global navigation is not a promise of global Umbra coverage, paid tasking, or automatic scientific suitability.

EAT-017 now supplies the versioned provider-neutral search boundary needed by Explore. The API and CLI query bounded provider metadata, preserve actual acquisition footprints, license and source identity, keep raw payloads behind adapters, and report provider failures or sample limits without erasing successful results. The MapLibre interface remains EAT-018 and does not begin until EAT-DES-002 design approval is recorded.

EAT-DES-002's approved [Explore specification](../docs/design/explore-interface-v1.md) and responsive standalone prototype define Explore/Analyze navigation, AOI/search/filter behavior, map/list parity, provider/failure language, retained pair selection, mobile order, and the EAT-019 comparability handoff. Browser walkthrough checks pass, and Carl's 2026-08-25 approval unlocks EAT-018 implementation.

Canonical GitHub repository: [carlwelchdesign/earth-atlas-ai](https://github.com/carlwelchdesign/earth-atlas-ai).

## Canonical plan

- [Product and MVP](./PRODUCT_AND_MVP.md)
- [Technical architecture](./TECHNICAL_ARCHITECTURE.md)
- [Experience and AI governance](./EXPERIENCE_AND_AI_GOVERNANCE.md)
- [Delivery plan](./DELIVERY_PLAN.md)
- [Execution backlog](./BACKLOG.md)
- [Risk register](./RISK_REGISTER.md)
- [Decision log](./DECISION_LOG.md)
- [Asana synchronization](./ASANA_SYNC.md)
- [Git and ticket workflow](./GIT_WORKFLOW.md)

## Planning rules

1. This directory is the durable source for product scope, architecture, decisions, risks, and acceptance criteria.
2. Asana is the execution system of record for ticket ownership, current activity, blockers, evidence, and completion.
3. Every development change must map to one `EAT-*` ticket and a dedicated branch once Git is initialized.
4. A task is not complete because code exists. Its acceptance checklist and required verification evidence must be satisfied and recorded in Asana.
5. Local processing, the standalone workbench, Palantir integration, public deployment, operational readiness, and public release are separate gates.
6. Changes to MVP scope, the pinned demonstration dataset, AI permissions, or the portability boundary require a decision-log entry.

## Current evidence and constraints

- The [AWS Open Data Registry](https://registry.opendata.aws/umbra-open-data/) describes Umbra's public SAR bucket, frequent updates, multiple time-series locations, GEC/SICD/SIDD/CPHD products, and CC BY 4.0 licensing.
- The live [Umbra STAC root](https://umbra-open-data-catalog.s3.us-west-2.amazonaws.com/stac/catalog.json) reports STAC 1.1.0 and currently links 2024 and 2025 catalogs.
- EAT-002 proved public object resolution despite empty STAC asset `href` values, and EAT-003 pinned the approved Bingham Canyon GEC pair with exact object identities, access evidence, and checksums.
- The live Palantir enrollment identifies AIP Developer Tier as the current plan, reports limited compute/users plus a 60-object-type cap and LLM rate limits, and exposes the core data, Ontology, application, code, and AIP tools. Resource Management currently reports zero Foundry compute, storage, and Ontology volume for the last 30 days and separately identifies the Small AIP tier with limited enrollment activity. Exact quota ceilings and EchoAtlas model invocation remain explicit feasibility gates rather than MVP dependencies.
- The [Palantir feasibility spike](../docs/platform/palantir-feasibility.md) maps and normalizes the portable bundle locally, records live raw/media/normalized import and Ontology behavior including the empty-family boundary, timestamp bridge, and synthetic GeoTIFF ingestion, and verifies restricted read-only application scopes, OSDK generation, private hosting, the production browser OAuth/query path, and a bounded real-derived static evidence profile. Cleanup, Media Set/Ontology-backed real-imagery behavior, and the final decision remain open.

## Definition of MVP complete

MVP is complete only when a new user can run or load the pinned public demonstration bundle, compare two SAR acquisitions on a temporal map, inspect deterministic change candidates with provenance and quality flags, record confirm/reject/needs-context assessments, and reproduce the bundle from documented inputs and parameters. The experience must include loading, empty, error, degraded, and keyboard-accessible review paths.
