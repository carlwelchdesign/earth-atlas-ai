# EchoAtlas Explore interface v1

Status: approved by Carl Welch for EAT-018 implementation on 2026-08-25.

Ticket: [EAT-DES-002](https://app.asana.com/1/9789386902387/project/1217790716964797/task/1217846797595944)

Prototype: [`prototypes/eat-des-002/index.html`](../../prototypes/eat-des-002/index.html)

## Product frame

Explore helps a civilian analyst move from a place or coordinate to a bounded, attributable list of provider-reported SAR acquisitions, then deliberately choose a candidate before/after pair for the existing Analyze workflow. It is an availability and selection tool—not a live global mosaic, coverage promise, suitability engine, or operational monitor.

Entry: open Explore without a selection, return from Analyze with retained selection state, or follow an approved place/AOI link. Exit: save nothing, refine the search, or hand an explicit AOI and candidate pair to EAT-019 comparability review.

Proposed validation targets, not measured outcomes:

- a first-time user can explain that map extent is not imagery coverage;
- every discovery and pair-selection task works without map gestures;
- provider, time, footprint, resolution, polarization, license, and source are visible before pair review;
- `no results` is not read as `never imaged`, and `pair selected` is not read as `scientifically valid`; and
- keyboard, screen reader, 200% zoom, 320/390/768/1440 px paths preserve the same decisions.

## Explore and Analyze

- **Explore** owns navigation, AOI definition, provider metadata search, footprint/list inspection, filters, and draft pair selection.
- **Analyze** owns a validated processing bundle, deterministic candidates, evidence review, and analyst assessments.

The global header uses two text-labeled mode controls, not a navigation rail. Analyze displays `no pair` or `pair retained`. Explore preserves the last query, AOI, camera, filters, cursor, before/after IDs, and list position during the session. Entering Analyze never converts a catalog acquisition into a validated bundle.

Handoff sequence:

1. Explore holds the selection as a draft.
2. **Review pair** opens a metadata summary, not processing.
3. EAT-019 later checks comparability and creates an immutable manifest/job.
4. Analyze opens the resulting bundle and offers **Return to Explore**.
5. Return restores the query and pair; refresh never silently replaces source identities.

Deep links may carry a bounded AOI and source identities, but never credentials or raw provider documents.

## Layout and responsive behavior

At 1180 CSS px and wider, four persistent regions form the workspace:

1. **Area and filters**: AOI, exact coordinates, draw/edit/reset, provider, date, product, polarization, resolution, and explicit search.
2. **Map and footprints**: replaceable basemap, AOI, provider-reported footprints, legend, attribution, zoom/reset, and edit affordances.
3. **Acquisition results**: the complete non-map path with the same identities, metadata, footprint focus, and before/after actions.
4. **Candidate pair tray**: retained identities, comparability warning, and review action.

At 721–1179 px, filters and map share the first row and results become full width. This is also the expected 200% zoom reflow on a 1440 px display; no capability disappears.

At 320–720 px, order is mode navigation, search, coverage boundary, AOI/filters, results, optional map, and pair tray. Results precede the map so phone discovery never depends on a precision gesture. Coordinate editing, filtering, list selection, and pair review remain available.

## Primary workflow

1. Search a place or enter `latitude, longitude`; autocomplete names its geocoder source.
2. Draw a rectangle/polygon or enter exact coordinates. Show area and limit before search.
3. Choose providers, dates, and optional product/resolution/polarization filters.
4. Activate **Search reported acquisitions**. Geometry edits never trigger an implicit provider query.
5. Read per-provider status before the result count.
6. Inspect cards or footprints; both repeat provider, time, product, resolution, polarization, license, and source.
7. Assign distinct records to Before and After; either slot can be replaced or cleared.
8. Activate **Review pair** and read the AOI/source identities and comparability warning.
9. EAT-019 later evaluates comparability before processing can start.

## AOI contract

- V1 accepts a non-antimeridian WGS84 rectangle or Polygon within EAT-017's five-degree/25-square-degree and 100-coordinate limits.
- **Draw AOI** enters a labeled edit mode. Escape cancels; **Done editing** commits; **Reset** restores the last searched AOI.
- Numeric bbox inputs and coordinate paste are equivalent to pointer drawing. Exact inputs are the baseline accessible method.
- Area, extent, geometry type, validity, and errors are text; color and geometry are supplementary.
- Editing an existing query marks its results `stale for this draft`; it does not silently clear or relabel them.
- Disallowed sensitive AOIs fail before search with safe policy language and without exposing blocklist internals.

## Results, footprints, and filters

- One normalized EAT-017 result drives card and footprint. Provider payloads never enter the renderer.
- Default sort is newest, provider, then source ID; the full rule is visible.
- **Show footprint** centers the map without moving focus. Map selection sets `aria-current` on the corresponding list record.
- A hidden footprint does not remove its list record or pair slot. Overlaps use line style plus text, not color alone.
- Pagination retains list position. When any provider reports `has_more` or sampling warnings, the UI says `sampled results`, never `all acquisitions`.
- Basemap and optional raster layers are separately labeled and attributed. Raster visibility never changes availability or pair status.
- Provider/date filters stay visible. Product, resolution, and polarization may be progressive form controls. Filter edits mark results stale until explicit search.
- A retained acquisition outside current filters remains labeled and requires confirmation before removal.

## Pair review

The same acquisition cannot fill both slots. EAT-018 compares metadata and footprints; legal preview derivatives, if later available, remain optional.

**Review pair** requires two distinct identities and shows AOI summary/hash placeholder; provider, item ID, collection, time, product, polarization, resolution, orbit/direction, license, source, freshness, and warnings for both records. It states `Machine-selected inputs, not a valid scientific pair.` The only forward action before EAT-019 is a disabled or preview-only **Check comparability**.

## Required state language

| State       | Heading                                                        | Meaning and recovery                                                                                  |
| ----------- | -------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------- |
| Loading     | `Searching bounded provider metadata`                          | Show each provider pending/complete/failed; say no raster is downloading; Cancel keeps prior results. |
| No coverage | `No provider reported coverage for this query`                 | Never say never imaged. Offer date, provider, filter, and AOI changes.                                |
| Partial     | `Sentinel-1 completed; Umbra reached its bounded sample limit` | Preserve successful records and identify the incomplete provider; never imply an exhaustive total.    |
| Stale       | `These results are older than the freshness policy`            | Show generation time; review may continue, but manifest creation requires a refresh decision.         |
| Rate limit  | `Umbra is temporarily rate limited`                            | Preserve other providers and retry only Umbra; absence is not shown as no coverage.                   |
| Invalid AOI | `The AOI exceeds the supported 25-square-degree limit`         | Make no provider call; focus the geometry error and preserve the draft.                               |
| Offline     | `Catalog search is offline`                                    | Cached basemap is not coverage evidence; preserve the query and offer retry.                          |
| Permission  | `This workspace cannot access the selected provider`           | Expose no restricted names, items, or counts; retain public results.                                  |

Warnings, rate limits, and permission failures never collapse into `0 results`.

## Accessibility contract

- A skip link targets results. Landmarks identify navigation, search, filters, map, results, and pair regions.
- Search, exact AOI, filters, result inspection, footprint focus, pair assignment/clearing, and review use ordinary controls in document order.
- The map is a named region, not an ARIA image containing controls. The canvas is supplementary and has a text extent/status summary.
- Cards use headings and description lists. Production actions include acquisition identity in their accessible names.
- Provider/selection changes announce politely; blocking validation/connection errors use alerts.
- Camera movement never moves focus. Dialog focus starts at its heading, stays inside, and returns to the invoker.
- Production targets are at least 44 × 44 CSS px. No page-level horizontal scrolling occurs at 200% zoom.
- Provider outlines combine color, dash, and labels. Reduced motion removes camera fly-to.
- MapLibre keyboard gestures enhance the map but are never required for completion.

## Trust, safety, and provenance

Persistent language:

- `Civilian research use`
- `The globe is navigation—not imagery coverage.`
- `Provider-reported acquisition`
- `No raster imagery is downloaded by search.`
- `Machine-selected inputs, not a valid scientific pair.`

Every record exposes provider, source identity/link, time, collection/product, footprint, license, and warnings. The interface never uses identity, target, threat, damage, intent, cause, or real-time operational-status language.

## EAT-018 component boundary

- `ExploreRoute`: query, view, and retained draft orchestration.
- `ExploreModeNav`: mode navigation labels only.
- `PlaceSearchAdapter`, `BasemapAdapter`, `MapRendererAdapter`: replaceable vendors.
- `AoiEditor`: validated provider-neutral GeoJSON and bbox.
- `CatalogQueryPanel`: EAT-017 request draft.
- `ProviderStatusSummary`: complete/partial/failed/stale wording.
- `FootprintMap` and `AcquisitionResults`: the same normalized view model.
- `PairTray` and `PairReviewDialog`: draft identities, never scientific policy.

Route state distinguishes `idle`, `editing`, `loading`, `ready`, `empty`, `partial`, `stale`, `offline`, and `blocked`, with nested provider reports. Camera state is disposable presentation state; AOI, query, response identity, cursor, and pair selection are domain-facing state.

## Privacy and analytics

No analytics ship by default. If later approved, useful consented events include search submitted, provider status seen, list/map selection, pair review opened, and handoff cancelled. General analytics must never contain raw AOI coordinates, place queries, item IDs, or sensitivity-policy outcomes.

## Non-goals

Production MapLibre/React code, provider procurement, global coverage, paid tasking, automatic pair approval, processing, interpretation, alerts, monitoring, or changes to SAR/sensitivity policy.
