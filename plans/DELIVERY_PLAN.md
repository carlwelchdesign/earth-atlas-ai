# Delivery plan

## Milestones

### M0 — Planning baseline

Outcome: the product boundary, architecture, risks, decisions, backlog, and Asana execution model exist before development.

Exit evidence:

- canonical files under `/plans`;
- specialist review findings integrated;
- Asana milestones and execution tickets created;
- dependencies recorded;
- no application code started.

### M1 — Data and processing proof

Outcome: one live Umbra pair is demonstrably accessible, comparable enough for the demo, reproducibly processed, and represented as a validated analysis bundle.

Tickets: `EAT-001` through `EAT-007`.

Gate: stop if no dataset pair passes the selection rubric. A polished UI does not start against speculative data.

### M2 — Analyst workbench

Outcome: a user can load a bundle, compare acquisitions, inspect candidates/evidence, and record reversible assessments across required states.

Tickets: `EAT-DES-001` and `EAT-008` through `EAT-011`.

Gate: Carl approves the implementation-ready interface handoff before frontend construction. Candidate status, provenance, and quality limitations are visible before any AI explanation work begins.

### M3 — Evaluation and explainable assistance

Outcome: deterministic pipeline quality has a benchmark and an optional AI layer can only draft cited explanations over structured evidence.

Tickets: `EAT-012` and `EAT-013`.

Gate: AI stays disabled unless citation, permission, and overclaiming evaluations pass.

### M4 — Demo hardening and retired platform experiment

Outcome: the standalone path remains intact, the retired platform experiment is recorded historically, and a reproducible public-demo package is ready for owner review.

Tickets: `EAT-014`, `EAT-016`, and `EAT-015`.

Gate: Developer Tier access and limits are feasibility results, not assumed capabilities. Public deployment and release require separate owner approval.

### M5 — Global imagery exploration

Outcome: a user can navigate or search a global map, define a bounded civilian AOI, inspect truthful Umbra and Sentinel-1 availability, select a candidate pair, and hand it into the existing Analyze workflow.

Tickets: `EAT-DES-002` and `EAT-017` through `EAT-019`.

Gate: Carl approves the Explore design before MapLibre implementation. Provider coverage, provenance, license, comparability, empty/error states, and a non-map accessible path must be visible. Global navigation must not imply global Umbra coverage, automatic pair validity, paid tasking, or operational monitoring.

## Dependency chain

```text
EAT-001 -> EAT-002 -> EAT-003 -> EAT-004 -> EAT-005 -> EAT-006 -> EAT-007
                                                               |          |
                                                               |          +-> EAT-DES-001 -> EAT-008 -> EAT-009 -> EAT-010 -> EAT-011
                                                               +-> EAT-012 -----------------------------------------+          |
                                                                                                                     +-> EAT-013
EAT-007 -> EAT-014
EAT-011 -> EAT-016
EAT-011 + EAT-012 + EAT-013 + EAT-016 -> EAT-015
EAT-014 informs EAT-015 but does not block the standalone demo if platform access is unavailable.
EAT-DES-002 -> EAT-018
EAT-017 -> EAT-018 -> EAT-019
EAT-007 -----------------> EAT-019
M5 is post-MVP and does not delay the M4 release-evidence gate.
```

## Delivery cadence

Work one unblocked ticket at a time unless a ticket explicitly documents safe parallel work. Each ticket follows:

1. Re-read canonical plan, dependencies, and current Asana state.
2. Add a start comment with branch, scope, and intended evidence.
3. Implement only ticket scope with tests.
4. Run focused checks, appropriate broader checks, runtime verification, and diff hygiene.
5. Add completion evidence to Asana, including commit/PR when available, test commands/results, artifacts, and remaining risk.
6. Mark complete only after acceptance criteria are satisfied.
7. Synchronize the durable plan when a decision, risk, or scope boundary changed.

Before a remote exists, commit evidence may be local. After a remote and protected workflow exist, completion requires a dedicated branch and meaningful PR unless the ticket explicitly changes that rule.

## RACI

| Decision/work | Carl | Codex delivery agent | SAR domain reviewer | Security/privacy reviewer |
| --- | --- | --- | --- | --- |
| MVP scope and public story | Accountable | Responsible for proposal | Consulted | Consulted |
| Dataset pair selection | Approves | Responsible | Consulted/required before calibrated claims | Informed |
| Architecture and implementation | Approves material changes | Responsible | Consulted for science boundaries | Consulted for release controls |
| Candidate interpretation | Accountable as analyst | Supplies tooling, not conclusions | Consulted | Informed |
| Provider account actions | Approves explicitly | Responsible only after approval | Informed | Consulted |
| Public deployment/release | Approves explicitly | Prepares evidence | Consulted | Review required |
| Global Explore design and provider expansion | Approves design and scope | Responsible | Consulted on pair-comparability language | Consulted on sensitivity, location, and provider controls |

## Validation plan

- planning: link and ticket-ID consistency; dependency and risk traceability;
- data: catalog fixtures plus a live discovery smoke test;
- processing: deterministic unit/golden tests and one clean rebuild;
- UX: automated behavior/accessibility checks plus desktop/tablet/mobile screenshots;
- AI: evidence-citation, unsupported-question, permission, and overclaiming evaluation set;
- demo: a fresh-machine runbook test and attribution/security review.
- exploration: contract fixtures plus bounded live catalog smoke tests, map/list parity, no-coverage and partial-provider states, accessibility checks, and desktop/mobile visual evidence.

## Specialist review synthesis

The ten planning-role passes produced these integrated decisions:

- Product: one analyst, one civilian change-review workflow, and explicit no-go criteria.
- Platform: provider adapters, versioned bundle contract, asynchronous job states, checksum cache, and vendor-neutral deployment boundaries.
- AI: delayed, draft-only assistance with structured evidence and deterministic permission gates.
- Content/data model: MVP object lifecycles and provenance links are canonical; future ontology types are deferred.
- Trust: licensing, sensitive-site review, public-release approval, and non-causal language are gates.
- Marketplace: commercialization is excluded until workflow value and operating costs are measured.
- UX: prepared no-account demo, non-map alternatives, reversible review, and all system states are required.
- Design gate: approved wireframes, high-fidelity key states, interaction annotations, responsive behavior, accessibility, and a walkthrough precede frontend construction.
- Analytics: comparability/quality reports, raw-versus-normalized separation, deterministic rebuilds, and meaningful local measures replace vanity metrics.
- Documentation: dataset card, runbook, architecture decisions, attribution, examples, and release evidence are versioned deliverables.
- TPM: ordered dependencies, ticket-level acceptance evidence, risk ownership, RACI, and decision logging govern execution.
