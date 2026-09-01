# EchoAtlas planning package

Status: EAT-001 through EAT-011, EAT-DES-001, and EAT-014 through EAT-020 are complete. EAT-012 remains in qualified-review and adjudication, so EAT-013 remains gated. EAT-020 removed the retired Palantir experiment and recorded that EchoAtlas needs no ontology dependency at its current scale. EAT-021 and EAT-022 cover the approved public Vercel deployment and portfolio case-study closeout.

EchoAtlas is a civilian disaster and infrastructure-change SAR intelligence workbench. The first release will prove one end-to-end analyst workflow with public Umbra data: select a comparable image pair, produce deterministic change candidates, inspect the evidence, and record a human assessment.

Post-MVP milestone M5 expands that proven workflow with a global **Explore** mode: a MapLibre globe and equivalent accessible results list let users define a civilian AOI, inspect truthful Umbra and Sentinel-1 catalog availability, select a candidate pair, and hand it to the existing **Analyze** workflow. Global navigation is not a promise of global Umbra coverage, paid tasking, or automatic scientific suitability.

EAT-017 now supplies the versioned provider-neutral search boundary needed by Explore. The API and CLI query bounded provider metadata, preserve actual acquisition footprints, license and source identity, keep raw payloads behind adapters, and report provider failures or sample limits without erasing successful results. The MapLibre interface remains EAT-018 and does not begin until EAT-DES-002 design approval is recorded.

EAT-DES-002's approved [Explore specification](../docs/design/explore-interface-v1.md) and responsive standalone prototype define Explore/Analyze navigation, AOI/search/filter behavior, map/list parity, provider/failure language, retained pair selection, mobile order, and the EAT-019 comparability handoff. Carl's 2026-08-25 approval unlocked EAT-018. Its production vertical slice now renders an isolated MapLibre Explore mode, validated exact/two-corner AOI drawing, real provider footprints, provider-neutral filters, classified failure states, partial-provider preservation, accessible list-based pair selection, a focus-contained metadata-review dialog, and responsive desktop/mobile layouts. Explicit place submissions resolve globally through a bounded server-side adapter; coordinates remain local. D-012 selects environment-driven MapTiler Cloud adapters for private R&D hosting while public OSM remains the visible local-development fallback. [Implementation evidence](../docs/qa/explore-interface-v1.md) records live Sacramento place resolution, the 15-record Sentinel-1 check, the accessibility pass, and the owner-approved measured performance budget.

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
5. Local processing, the standalone workbench, public deployment, operational readiness, and public release are separate gates.
6. Changes to MVP scope, the pinned demonstration dataset, AI permissions, or the portability boundary require a decision-log entry.

## Current evidence and constraints

- The [AWS Open Data Registry](https://registry.opendata.aws/umbra-open-data/) describes Umbra's public SAR bucket, frequent updates, multiple time-series locations, GEC/SICD/SIDD/CPHD products, and CC BY 4.0 licensing.
- The live [Umbra STAC root](https://umbra-open-data-catalog.s3.us-west-2.amazonaws.com/stac/catalog.json) reports STAC 1.1.0 and currently links 2024 and 2025 catalogs.
- EAT-002 proved public object resolution despite empty STAC asset `href` values, and EAT-003 pinned the approved Bingham Canyon GEC pair with exact object identities, access evidence, and checksums.
- The versioned analysis bundle already supplies the stable identities, typed records, links, provenance, and validation needed by the current product. D-015 rejects an ontology dependency until a concrete semantic-query, inference, or cross-system interchange requirement exists.

## Definition of MVP complete

MVP is complete only when a new user can run or load the pinned public demonstration bundle, compare two SAR acquisitions on a temporal map, inspect deterministic change candidates with provenance and quality flags, record confirm/reject/needs-context assessments, and reproduce the bundle from documented inputs and parameters. The experience must include loading, empty, error, degraded, and keyboard-accessible review paths.
