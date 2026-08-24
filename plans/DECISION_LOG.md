# Decision log

## D-001 — Civilian disaster and infrastructure-change wedge

- Date: 2026-08-24
- Status: accepted
- Decision: the first demonstration excludes military target tracking and person-level surveillance.
- Why: it proves the geospatial and operational workflow while remaining safer and easier to discuss publicly.
- Revisit when: only after a public MVP, governance review, and explicit owner decision.

## D-002 — Prove the pair before building the workbench

- Date: 2026-08-24
- Status: accepted
- Decision: live catalog discovery and pair feasibility gate M2 work.
- Why: SAR UX and AI are not credible without accessible, comparable source data.
- Revisit when: never for the MVP; a prepared fixture must still be generated from a valid live-source manifest.

## D-003 — Portable analysis bundle is the system boundary

- Date: 2026-08-24
- Status: accepted
- Decision: Python processing emits a versioned, provider-neutral bundle consumed by React, tests, and platform adapters.
- Why: it preserves reproducibility, isolates raster science, and prevents Palantir lock-in.
- Revisit when: a proven performance or governance constraint requires a different transport, without changing the domain contract.

## D-004 — Deterministic candidates precede AI explanations

- Date: 2026-08-24
- Status: accepted
- Decision: no LLM is in the pixel-processing or candidate-confirmation path; M3 AI is feature-gated draft explanation over structured evidence.
- Why: measurements, provenance, and analyst control must exist before generated language.
- Revisit when: only with evaluation evidence and an explicit governance revision.

## D-005 — Palantir is an optional adapter

- Date: 2026-08-24
- Status: accepted
- Decision: Developer Tier work is a bounded feasibility spike after the standalone bundle exists.
- Why: tier limits and live enrollment capabilities can change, and the public demo must remain reproducible without a proprietary runtime.
- Revisit when: EAT-014 produces current evidence and a go/adjust/no-go recommendation.

## D-006 — No marketplace or monetization in MVP

- Date: 2026-08-24
- Status: accepted
- Decision: billing, subscriptions, entitlements, and customer onboarding are excluded.
- Why: the project must first prove analyst value, scientific honesty, operating cost, and a repeatable workflow.
- Revisit when: post-MVP user evidence supports a commercial use case.

## D-007 — Approve the interface before frontend implementation

- Date: 2026-08-24
- Status: accepted
- Decision: `EAT-DES-001` produces and validates an implementation-ready workbench design before `EAT-008` begins.
- Why: the analyst workflow combines maps, imagery comparison, evidence, warnings, and consequential review states; designing it ad hoc in code would increase usability, accessibility, and rework risk.
- Revisit when: only after an approved design handoff records why implementation should proceed with unresolved findings.

## D-008 — Establish a Python modular backend and React workspace

- Date: 2026-08-24
- Status: accepted
- Decision: use Python 3.12+ with `uv` and FastAPI for one modular backend distribution; keep API and processor as separate modules. Use Node 20.19+, npm workspaces, React 19, TypeScript 5, and Vite 7 for the workbench. Use GitHub Actions for CI and MIT for source code while preserving separate data licenses.
- Why: the processing ecosystem is Python-native, a modular monolith avoids premature service operations, and the provider-neutral bundle preserves a future split. The selected frontend stack supports a custom standalone and later OSDK-compatible React experience.
- Revisit when: measured dependency isolation, scaling, deployment, or platform-adapter constraints justify a service split or runtime upgrade.

## D-009 — Use containers for reproducible standalone packaging

- Date: 2026-08-24
- Status: accepted
- Decision: keep native `uv` and npm workflows for day-to-day development, then package the standalone backend and production workbench as non-root container images with health checks and a local Compose configuration in `EAT-015`. The Compose path uses explicit local persistence and has no Palantir or AI-provider requirement.
- Why: containers provide a consistent fresh-machine demo and a portable deployment artifact without slowing the current data-processing proof or coupling the product to a platform provider.
- Revisit when: an approved deployment target imposes runtime, ingress, orchestration, storage, or observability requirements beyond the local standalone package.
