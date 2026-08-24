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
