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
- Why: it preserves reproducibility, isolates raster science, and prevents platform lock-in.
- Revisit when: a proven performance or governance constraint requires a different transport, without changing the domain contract.

## D-004 — Deterministic candidates precede AI explanations

- Date: 2026-08-24
- Status: accepted
- Decision: no LLM is in the pixel-processing or candidate-confirmation path; M3 AI is feature-gated draft explanation over structured evidence.
- Why: measurements, provenance, and analyst control must exist before generated language.
- Revisit when: only with evaluation evidence and an explicit governance revision.

## D-005 — Historical platform-spike decision

- Date: 2026-08-24
- Status: superseded by D-015
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
- Why: the processing ecosystem is Python-native, a modular monolith avoids premature service operations, and the provider-neutral bundle preserves a future split. The selected frontend stack supports a portable React experience.
- Revisit when: measured dependency isolation, scaling, deployment, or platform-adapter constraints justify a service split or runtime upgrade.

## D-009 — Use containers for reproducible standalone packaging

- Date: 2026-08-24
- Status: accepted
- Decision: keep native `uv` and npm workflows for day-to-day development, then package the standalone backend and production workbench as non-root container images with health checks and a local Compose configuration in `EAT-015`. The Compose path uses explicit local persistence and has no ontology-platform or AI-provider requirement.
- Why: containers provide a consistent fresh-machine demo and a portable deployment artifact without slowing the current data-processing proof or coupling the product to a platform provider.
- Revisit when: an approved deployment target imposes runtime, ingress, orchestration, storage, or observability requirements beyond the local standalone package.

## D-010 — Add a portable Explore mode after the single-story MVP

- Date: 2026-08-25
- Status: accepted
- Decision: add a post-MVP Explore mode built on MapLibre GL JS plus an equivalent accessible results list. Provider-neutral Umbra and Sentinel-1 catalog adapters report actual acquisition footprints and metadata; an explicit pair selection then enters the existing deterministic Analyze workflow.
- Why: users need a spatial way to discover where data exists, but the rendering engine must not be confused with imagery coverage, provider policy, pair suitability, or analysis science. Sentinel-1 supplies a broad free foundation while Umbra remains the higher-resolution layer where its open catalog has coverage.
- Revisit when: measured performance, accessibility, provider terms, geocoder privacy, or deployment constraints require a different renderer or catalog provider; the provider-neutral contracts and truthful coverage boundary remain.

## D-011 — Use public OSM services only as bounded development adapters

- Date: 2026-08-25
- Status: accepted for local and owner-review use; production provider remains undecided.
- Decision: MapLibre uses a replaceable OpenStreetMap raster-tile configuration for interactive development viewing. Explicit, user-submitted place queries use a server-side Nominatim adapter with a fixed HTTPS host allowlist, identifiable User-Agent, maximum one upstream request per 1.1 seconds, bounded response size and timeout, in-memory query cache, no autocomplete/bulk search, and a small fixed AOI around the selected place. Latitude/longitude queries resolve locally and are not disclosed to the geocoder.
- Why: this makes global navigation and typed place discovery testable without hard-coding provider behavior into the renderer or promising production capacity from community-funded services. It follows the current [Nominatim usage policy](https://operations.osmfoundation.org/policies/nominatim/) and [tile usage policy](https://operations.osmfoundation.org/policies/tiles/) for moderate interactive development use while keeping switching possible without domain changes.
- Revisit when: selecting a production deployment, adding meaningful traffic, storing durable geocoder results, requiring an SLA/offline use, or changing privacy terms. Public OSM services are best-effort and may withdraw access; production requires an explicit provider/self-hosting, caching, attribution, privacy, and cost decision.

## D-012 — Select MapTiler for private R&D Explore hosting

- Date: 2026-08-25
- Status: accepted for private R&D configuration; account/key activation and public/commercial release remain separate owner gates.
- Decision: use environment-selected MapTiler Cloud adapters for the hosted private R&D basemap and explicit place-name geocoding. `VITE_MAPTILER_API_KEY` selects the MapTiler Dataviz style in MapLibre; `ECHOATLAS_MAPTILER_API_KEY` selects the server-side allowlisted geocoder. No key is committed. Missing keys visibly select the public OSM local-development fallback. Coordinate queries remain local.
- Why: MapTiler supports MapLibre, global maps, and geocoding behind one replaceable API. Its current Free plan requires no billing information and permits non-commercial use plus commercial-product R&D, which matches EchoAtlas's current private research status. It pauses at quota and has no production SLA, so it is not a silent public/commercial deployment decision.
- Revisit when: creating or restricting the MapTiler keys, deploying beyond private R&D, approaching quota, requiring an SLA/offline service, or approving spending. Public/commercial launch requires a suitable paid plan, another adapter, or a documented self-hosted stack. See `docs/architecture/explore-map-provider.md`.

## D-013 — Historical platform-spike closeout

- Date: 2026-08-25
- Status: superseded by D-015
- Decision: close EAT-014 with an **adjust** result. Foundry may be used as an optional downstream Ontology, media, Map, restricted application, and private-hosting layer. The provider-neutral bundle and standalone deterministic runtime remain canonical; processing policy, assessments, and provider access do not move exclusively into Foundry.
- Why: live evidence proves the synthetic object/link/raster path, read-only OSDK application, and bounded real-derived static profile, but not real Media Set/Ontology-backed Umbra imagery, cleanup, exact tier ceilings/duration, public scale, or cost. Keeping the adapter optional captures demonstrated value without converting untested platform behavior into product dependencies.
- Revisit when: a deployment has an approved Palantir operating model, real-imagery scale and licensing evidence, cleanup/retention procedures, known quotas and cost, and a reason the standalone bundle boundary is insufficient.

## D-014 — Package the AI-disabled standalone before external SAR adjudication

- Date: 2026-08-25
- Status: accepted for owner-review packaging; public release remains blocked.
- Decision: EAT-015 may build and verify the reproducible standalone package while EAT-012 awaits qualified independent SAR adjudication and EAT-013 remains gated. The shipped package keeps AI disabled and labels benchmark/AI work as unavailable roadmap.
- Why: containerization, runbooks, security review, responsive evidence, and truthful portfolio packaging are independently verifiable engineering work. Waiting to package would not accelerate the external review, while pretending the review or AI exists would violate the product boundary.
- Revisit when: EAT-012 is adjudicated and EAT-013 either passes its governance thresholds or is explicitly removed. Only then may benchmark or AI capabilities move from roadmap to shipped documentation.

## D-015 — Retire Palantir and do not replace it with an ontology dependency

- Date: 2026-08-31
- Status: accepted; supersedes D-005 and D-013 for active product architecture.
- Decision: remove the Palantir adapter, OSDK/OAuth runtime, private hosted build, import/package tooling, and active platform documentation. Do not add RDFLib, Oxigraph, Apache Jena, NetworkX, or another ontology/graph dependency now. Keep the versioned analysis bundle as the portable knowledge boundary.
- Why: the private Foundry surface does not satisfy the public portfolio objective, and EchoAtlas has no current semantic inference, RDF/SPARQL query, graph-algorithm, or cross-system ontology requirement. The existing bundle already provides stable identities, typed records, explicit links, provenance, and validation. A replacement ontology would add operational and conceptual cost without user-visible value.
- Revisit when: a concrete requirement exists for linked-data interchange, cross-domain semantic queries, inference, or graph algorithms. RDFLib is the first standards-based Python option to evaluate; Oxigraph is the first embedded persistent RDF store to evaluate.

## D-016 — Publish a bounded Vercel portfolio deployment

- Date: 2026-08-31
- Status: accepted by Carl for public portfolio deployment.
- Decision: publish the Explore-first Vite application and lightweight FastAPI metadata/comparability boundary on Vercel. Include only the reduced approved Bingham Canyon display bundle needed for the exact-pair demonstration. Keep raster processing, raw imagery, provider payloads, caches, durable jobs, and multi-user assessment storage outside Vercel.
- Why: the portfolio needs a public, login-free product surface. Vercel supports Vite static assets and FastAPI Functions, while EchoAtlas's provider-neutral API and bundle contracts let the deployment remain bounded and truthful.
- Revisit when: traffic, provider terms, durable storage, background processing, operational monitoring, paid tasking, authentication, or a public SLA becomes a real requirement.
