# EchoAtlas planning package

Status: EAT-001 through EAT-011, EAT-DES-001, and EAT-014 through EAT-032 are complete. EAT-033 is production-verified from `release/2026-09-07-nepal`, with exact merge-back tracked in PR #68. EAT-034 is in progress for bounded Nepal acquisition date selection and the 60-day catalogue contract. EAT-012 remains in qualified review and adjudication, so EAT-013 and M3 remain gated. EAT-020 removed the retired proprietary-platform experiment; EchoAtlas has no Palantir or ontology dependency.

EchoAtlas is a civilian disaster and infrastructure-change investigation workbench. The current release retains the public Umbra SAR workflow as a secondary regression reference and adds a Nepal-first, evidence-first investigation using prepared georeferenced Sentinel-2 imagery and cited observations. It does not compute Nepal change candidates or use AI.

Post-MVP milestone M5 expands that proven workflow with a global **Explore** mode: a MapLibre globe and equivalent accessible results list let users define a civilian AOI, inspect truthful Umbra and Sentinel-1 catalog availability, select a candidate pair, and hand it to the existing **Analyze** workflow. Global navigation is not a promise of global Umbra coverage, paid tasking, or automatic scientific suitability.

EAT-017 supplies the versioned provider-neutral search boundary used by Explore. The API and CLI query bounded provider metadata, preserve actual acquisition footprints, license and source identity, keep raw payloads behind adapters, and report provider failures or sample limits without erasing successful results. EAT-018 and EAT-019 completed the MapLibre interface and Analyze handoff; these now remain addressable secondary workflows.

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

## Definition of Nepal release complete

The release is complete only when a new user can open the public root without an account, navigate the pinned Nepal before/after imagery, inspect a cited source observation, record and reload a separate assessment, and export a deterministic brief. The exact source products, case, tiles, coverage, transparent nodata, alignment measurements, limitations, and attribution must be reproducible. Loading, invalid-case, missing-tile, WebGL-failure, storage-failure, narrow-screen, and keyboard-accessible paths must remain usable. Explore and Analyze must continue to pass their regression checks.
