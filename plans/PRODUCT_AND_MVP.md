# Product and MVP

## Product thesis

Open SAR imagery is technically available but not automatically decision-ready. EchoAtlas should reduce the work between finding a viable acquisition pair and producing a reviewable, evidence-backed change assessment.

The product promise is deliberately narrow: **See change through anything, with the evidence and uncertainty needed to review it.**

## Beachhead user

The MVP serves one primary user: a geospatial analyst or technically capable disaster-response investigator evaluating change in a known civilian area of interest.

Job to be done:

> When an event may have affected infrastructure, help me compare suitable SAR acquisitions, find candidate changes, and record an evidence-backed assessment without hiding source quality or processing assumptions.

The public portfolio viewer is a secondary audience, not a second workflow. They should be able to load a prepared demo and understand the analyst process without an account or a live cloud dependency.

## MVP workflow

1. Open the pinned civilian event and area of interest.
2. Inspect the two selected acquisitions, coverage, timestamps, geometry, and comparability flags.
3. View synchronized before/after imagery and a temporal map.
4. Review deterministic change candidates ranked by a transparent score.
5. Inspect source imagery, processing parameters, measurements, and quality warnings.
6. Mark each candidate `confirmed`, `rejected`, or `needs_context` and add a note.
7. Export or reload the analysis bundle and retain the assessment audit trail.

## Dataset selection gate

The event is not yet pinned. `EAT-002` and `EAT-003` must choose it from live evidence using this rubric:

- civilian disaster or infrastructure-change story suitable for public explanation;
- at least two legally usable Umbra GEC acquisitions with meaningful AOI overlap;
- enough pre/post temporal separation to plausibly reveal change;
- compatible polarization and processable spatial resolution;
- acquisition geometry and incidence differences documented, not concealed;
- assets small enough for a reproducible local demo or support bounded crop/range access;
- an external event source can establish what happened without being treated as pixel-level ground truth;
- no person-level surveillance, military target tracking, or sensitive-site targeting.

If no pair passes, the ticket returns a documented no-go and the plan is revised before development continues. The backlog must not quietly substitute a different data provider.

## Product outcome and measures

Primary outcome: one analyst can move from a validated acquisition pair to a reviewable set of change candidates with visible evidence.

MVP measures:

- deterministic rebuild produces the same manifest and geometries from the same source objects and parameters;
- prepared demo reaches the first reviewable candidate in under two minutes on the reference machine;
- live-data pipeline emits actionable failure and quality states instead of partial silent output;
- every candidate links to both acquisitions, the run, parameters, and derived artifacts;
- a reviewer can complete the core workflow using keyboard controls;
- structured usability sessions show that reviewers can distinguish machine candidates from analyst conclusions.

Metrics are local and privacy-preserving in MVP. No third-party behavioral analytics is required.

## Hard non-goals

- military target tracking, person-level surveillance, or automated intelligence conclusions;
- autonomous alerts or external actions;
- an LLM interpreting raw SAR pixels;
- learned object detection before a labeled evaluation set and baseline exist;
- real-time ingestion, global imagery discovery within the MVP, multi-tenancy, enterprise RBAC, or production operations;
- Palantir as a required runtime or source of truth;
- a marketplace, billing, subscriptions, or customer onboarding;
- claiming disaster impact, causal damage, or operational truth from a change mask alone.

## Roadmap boundaries

- **M1 proves data and processing.** No polished application can compensate for an invalid pair.
- **M2 proves the analyst review experience.** Prepared fixtures are allowed, but all displayed evidence must come from the same bundle contract as live processing.
- **M3 adds AI only as a cited draft explanation over structured evidence.** It remains feature-gated.
- **M4 tests Palantir as an adapter and hardens a public demo.** Palantir work does not block the standalone MVP.
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
