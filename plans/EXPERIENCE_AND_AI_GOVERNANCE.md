# Experience and AI governance

## Experience principles

1. Evidence before explanation.
2. Machine candidates and analyst conclusions are visually and semantically distinct.
3. Quality limitations stay near the decision, not buried in documentation.
4. Every state offers a next step: retry, inspect, change pair, dismiss, or request context.
5. The prepared demo works without accounts, live APIs, or proprietary platforms.

## MVP information architecture

`EAT-DES-001` converts this experience plan into approved wireframes, high-fidelity key states, an annotated interaction specification, responsive layouts, accessibility behavior, design tokens, and a component inventory before `EAT-008` begins implementation.

### Mission header

Shows event/AOI, analysis status, acquisition timestamps, bundle freshness, and the highest-severity quality warning. It must not claim the event caused a detected change.

### Temporal map and comparison workspace

- synchronized map viewport and before/after views;
- time toggle as the keyboard- and screen-reader-safe baseline;
- optional draggable comparison reveal for pointer users;
- candidate overlay with selected/pending/reviewed states;
- visible legend and non-color state indicators.

### Review queue

- candidate ID, area/shape measurements, transparent change score, status, and warning count;
- deterministic sort and filters;
- confirm, reject, or needs-context actions with optional analyst note;
- undo by superseding assessment rather than deleting history.

### Evidence drawer

- links to both source acquisitions and original catalog metadata;
- acquisition geometry and comparability table;
- processing steps, parameter values, software version, checksums, and artifacts;
- explanation of what the score does and does not mean;
- raw/derived licensing and attribution.

## Required states

| State | Required experience |
| --- | --- |
| Loading | Show which bundle/job is loading and retain layout stability. |
| Empty | Explain that no pair or no candidates are available and offer the correct next step. |
| Error | Name the failed stage, preserve safe work, and provide retry/details. |
| Degraded | Keep valid evidence usable while identifying missing artifacts or quality warnings. |
| Permission denied | Reserved for future remote systems; explain the exact missing capability without leaking data. |
| Partial success | Separate completed outputs from failed outputs and never label the whole run successful. |
| Success | Show run identity, freshness, candidate count, and review progress. |
| Disabled action | Explain the unmet prerequisite in accessible text. |

Responsive MVP supports desktop analysis first and a read-only tablet/mobile inspection path. Candidate review actions must remain usable at 200% zoom. Map interactions cannot be the only way to select or understand a candidate.

## AI automation level

MVP AI level: **off** through M2, then **draft explanation** in M3.

The AI component may:

- summarize structured acquisitions, quality flags, measurements, candidates, and analyst assessments;
- answer questions by retrieving bundle records;
- draft a plain-language run summary with evidence references;
- state when the available evidence does not support an answer.

It may not:

- inspect or interpret raw pixels independently;
- convert a candidate into a confirmed finding;
- infer damage, cause, identity, intent, or operational status without cited evidence;
- change an assessment, create an external alert, subscribe an AOI, or publish a report;
- call unrestricted network, filesystem, deployment, or messaging tools;
- hide unsupported claims behind a numeric confidence value.

## AI output contract

Every draft summary must include:

- generator and prompt/evaluation version;
- bundle and run IDs;
- a list of claims with supporting candidate/artifact IDs;
- explicit limitations and unresolved quality flags;
- `draft` status and the analyst action that accepted, edited, or rejected it;
- no free-form source links that were not present in the validated evidence graph.

Unsupported questions return an explicit insufficiency response. Deterministic code validates citations and allowed claim fields before the draft is displayed.

## Evaluation and monitoring

- curated fixtures for supported, unsupported, conflicting, and missing-evidence questions;
- claim-to-evidence citation precision target of 100% for displayed factual claims;
- zero autonomous assessment or external-action attempts in permission tests;
- review for overclaiming causality, damage, confidence, and object identity;
- latency and cost recorded separately from answer quality;
- user edits/rejections retained locally as evaluation evidence, with no silent prompt training or external upload.

AI remains disabled if the evaluation threshold is not met or a provider key is absent. The deterministic workbench must remain fully usable. The EAT-015 owner-review package deliberately ships with AI disabled because EAT-012 independent SAR adjudication is incomplete and EAT-013 has not begun; no model key or model call is part of the release path.

## Trust, rights, and public-release gates

- retain Umbra item IDs, source URLs, access date, checksums, and CC BY 4.0 attribution;
- verify the license for every non-Umbra event-context source and base map;
- crop and minimize data to the selected civilian AOI;
- run a sensitivity review before publishing coordinates, derived tiles, or high-resolution artifacts;
- provide correction and takedown contact guidance for the public demo;
- do not market candidates as verified damage, intelligence conclusions, or real-time monitoring;
- require Carl's explicit approval for cloud deployment, provider keys, or public release.
