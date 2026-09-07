# Product and MVP

## Product thesis

Satellite imagery is technically available but not automatically decision-ready. EchoAtlas reduces the work between opening a bounded event, comparing trustworthy imagery, and producing a reviewable, evidence-backed assessment.

The product promise is deliberately narrow: **See change through anything, with the evidence and uncertainty needed to review it.**

## Beachhead user

The MVP serves one primary user: a geospatial analyst or technically capable disaster-response investigator evaluating change in a known civilian area of interest.

Job to be done:

> When an event may have affected a civilian area, help me navigate aligned before/after imagery, inspect sourced observations, and record an evidence-backed assessment without hiding coverage or quality limits.

The public portfolio viewer is a secondary audience, not a second workflow. They should be able to load a prepared demo and understand the analyst process without an account or a live cloud dependency.

## MVP workflow

1. Open the prepared 26 August 2026 Nepal flood case without signing in.
2. Inspect the case boundary, choose Sentinel-2 acquisitions within the bounded case window, and review sources, attribution, and cloud limitations.
3. Navigate synchronized before/after MapLibre imagery or use swipe and single-date controls.
4. Select an immutable source-reported observation from the map or accessible list.
5. Inspect its cited evidence and record `supported`, `rejected`, or `needs_context` with a note.
6. Correct an assessment without deleting history and reload the browser-local draft.
7. Export matching printable HTML and JSON briefs with sources, unresolved issues, limitations, and case version.

## Prepared Nepal dataset gate

EAT-027 passed the source gate for the Bhote Koshi–Trishuli corridor using exact Sentinel-2 L2A products from 12 and 27 August 2026 plus preliminary UNOSAT reference geometry. The gate requires:

- civilian disaster or infrastructure-change story suitable for public explanation;
- at least two legally usable same-sensor acquisitions with meaningful AOI overlap;
- enough pre/post temporal separation to plausibly reveal change;
- compatible polarization and processable spatial resolution;
- acquisition geometry and incidence differences documented, not concealed;
- assets small enough for reproducible bounded local preparation;
- an external event source can establish what happened without being treated as pixel-level ground truth;
- no person-level surveillance, military target tracking, or sensitive-site targeting.

The prepared default remains limited by 78.47% scene-level cloud cover in the after image. Reviewers can inspect other Sentinel-2 dates from the 60-day case window, while full-tile quality metadata remains distinct from visible AOI quality. The source gate prohibits stretching a published comparison JPEG onto the map or silently substituting another disaster.

## Product outcome and measures

Primary outcome: one reviewer can navigate the prepared Nepal case, distinguish cited observations from their own conclusions, and export a reviewable brief.

MVP measures:

- deterministic rebuild produces the same case manifest, tile coverage, and observation geometries from the same source objects and parameters;
- prepared imagery becomes usable within five seconds on a recorded reference device and network;
- the guided Context → Compare → Review → Brief flow completes within three minutes;
- live-data pipeline emits actionable failure and quality states instead of partial silent output;
- every published observation links to cited evidence while user assessments remain separate;
- a reviewer can complete the core workflow using keyboard controls;
- at least four of five first-time reviewers complete the flow without coaching and distinguish source observations from their own conclusions.

Metrics are local and privacy-preserving in MVP. No third-party behavioral analytics is required.

## Hard non-goals

- military target tracking, person-level surveillance, or automated intelligence conclusions;
- autonomous alerts or external actions;
- an LLM interpreting raw SAR pixels;
- AI summaries or model-generated conclusions in the Nepal release;
- arbitrary-area processing or newly computed Nepal change candidates;
- learned object detection before a labeled evaluation set and baseline exist;
- real-time ingestion, global imagery discovery within the MVP, multi-tenancy, enterprise RBAC, or production operations;
- an ontology platform as a required runtime or source of truth;
- a marketplace, billing, subscriptions, or customer onboarding;
- claiming disaster impact, causal damage, or operational truth from a change mask alone.

## Roadmap boundaries

- **M1 proves data and processing.** No polished application can compensate for an invalid pair.
- **M2 proves the analyst review experience.** Prepared fixtures are allowed, but all displayed evidence must come from the same bundle contract as live processing.
- **M3 adds AI only as a cited draft explanation over structured evidence.** It remains feature-gated.
- **M4 hardens the reproducible standalone demo.** Retired platform experiments do not remain product dependencies.
- **M5 adds global imagery exploration after the single-story workflow is proven.** A MapLibre globe and accessible results list expose provider-reported coverage from Umbra and Sentinel-1 adapters, then hand an explicitly selected pair to the existing analysis pipeline. Navigating anywhere does not imply that suitable imagery exists there.

## Post-MVP Explore workflow

1. Search for a place or navigate the globe.
2. Draw or edit a bounded civilian area of interest.
3. Query provider-neutral catalog adapters for an explicit time range.
4. Inspect acquisition footprints, timestamps, provider, product, resolution, polarization, license, provenance, and quality warnings on both the map and an equivalent results list.
5. Compare candidate before/after pairs without treating availability as scientific suitability.
6. Create an immutable selection manifest and start the existing deterministic processing flow.
7. Open the resulting provider-neutral bundle in **Analyze**, with a clear return path to **Explore**.

The first Explore release does not purchase or automate commercial tasking, promise continuous global coverage, download the world, create operational alerts, or relax the civilian-use and sensitivity boundaries.
