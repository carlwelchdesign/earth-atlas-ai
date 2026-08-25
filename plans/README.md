# EchoAtlas planning package

Status: EAT-001 through EAT-011, EAT-DES-001, and EAT-016 are complete. EAT-012 remains in qualified-review and adjudication. EAT-014 has a network-free bundle-to-Ontology projection, a zero-row-safe version 1.3.0 normalized-table package, an authenticated Developer Tier inventory, live raw/media/normalized synthetic imports, five domain object types linked by six dataset-backed relations, a verified live epoch-millisecond-to-`Timestamp` bridge for Acquisition and Analysis Run, and a sixth media-reference object type that places the bounded synthetic GeoTIFF in a persistent native Map template. A restricted read-only application, generated OSDK, and private synthetic-only Foundry-hosted workbench are now verified. Hosted UI-to-OSDK integration, cleanup behavior, durable screenshot evidence, real-imagery behavior, and the final decision remain open. The processed real Umbra Bingham Canyon pair is visible only in the standalone workbench through the validated, gitignored EAT-016 prepared-demo boundary.

EchoAtlas is a civilian disaster and infrastructure-change SAR intelligence workbench. The first release will prove one end-to-end analyst workflow with public Umbra data: select a comparable image pair, produce deterministic change candidates, inspect the evidence, and record a human assessment.

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
- The [Palantir feasibility spike](../docs/platform/palantir-feasibility.md) maps and normalizes the portable bundle locally, records live raw/media/normalized import and Ontology behavior including the empty-family boundary, timestamp bridge, and synthetic GeoTIFF ingestion, and now verifies restricted read-only application scopes, OSDK generation, and private synthetic-only hosting. Hosted UI-to-OSDK integration, cleanup, real-imagery behavior, and the final decision remain open.

## Definition of MVP complete

MVP is complete only when a new user can run or load the pinned public demonstration bundle, compare two SAR acquisitions on a temporal map, inspect deterministic change candidates with provenance and quality flags, record confirm/reject/needs-context assessments, and reproduce the bundle from documented inputs and parameters. The experience must include loading, empty, error, degraded, and keyboard-accessible review paths.
