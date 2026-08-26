# Explore interface v1 implementation evidence

Status: EAT-018 in progress on `feature/eat-018-maplibre-explore` as of 2026-08-25.

This evidence covers the first production Explore vertical slice. It does not close EAT-018 or claim that every approved design state is implemented.

## Implemented boundary

- Explore is a peer mode and the existing Analyze workbench remains intact.
- MapLibre GL JS 6.6.0 is loaded only by the isolated map component.
- A replaceable development basemap config uses attributed OpenStreetMap tiles. It is navigation context, not SAR imagery or a production tile-service decision.
- Exact WGS84 AOI editing, two-corner pointer drawing with Escape cancellation and focus return, global place search, local coordinate resolution, provider/date/product/polarization/resolution filters, explicit search, map/list selection, source/license metadata, and draft before/after assignment are wired to the EAT-017 contract.
- Explicit place submissions pass through a server-side Nominatim adapter. It fixes the HTTPS host, identifies EchoAtlas, bounds time and response size, rate-limits upstream access to one request per 1.1 seconds, caches repeated queries in memory, performs no autocomplete or bulk lookup, and returns a small fixed AOI rather than a provider-wide administrative boundary. The browser uses a POST body so place text is absent from the local API access-log URL; coordinates never leave the browser.
- Umbra and Sentinel-1 are requested independently through the same provider-neutral API. A 25-second client bound converts a stalled provider into a visible partial result instead of hiding another provider's success.
- HTTP permission and rate-limit responses, bounded timeouts, and unreachable-service failures retain explicit client classifications for state messaging and tests.
- Candidate-pair review opens in a contained keyboard dialog, moves focus to its heading, returns focus on close, and keeps EAT-019 comparability disabled and accurately labeled.
- Search draws the AOI and provider-reported acquisition footprints. It does not download raster imagery.

## Automated verification

The focused Explore/catalog suite has 19 tests covering place and catalog transport, state behavior, drawing, selection, and automated accessibility. Together with the existing Analyze coverage and reversible-mode test, the complete workbench suite has 67 tests. The new tests cover:

- provider-neutral request serialization;
- safe API errors, permission/rate-limit/offline classification, and the provider timeout;
- allowlisted Nominatim normalization, upstream throttling, caching, response bounds, no-match behavior, local-coordinate privacy, and invalid runtime data;
- exact AOI validation before a provider call;
- no-coverage wording;
- partial-provider preservation;
- stale-result state after filter changes;
- equivalent list-only pair selection;
- pointer-mode instructions, Escape cancellation, and exact-coordinate fallback;
- pair-review focus entry/return and disabled comparability handoff; and
- refusal to place the same acquisition in both pair slots; and
- no automated accessibility violations in the list-equivalent Explore path.

The complete `make check` gate passes: 107 backend tests, 67 workbench tests, formatting, lint, type checking, production build, and secret scanning. The production build keeps MapLibre in a separate `249.36 kB` gzip chunk; total first Explore JavaScript is approximately `371.84 kB` gzip and complete workbench CSS is `17.04 kB` gzip.

## Browser evidence

Local browser checks passed at 1440 CSS pixels and 390 CSS pixels:

- no page-level horizontal overflow;
- mobile reading order is query, results, map, pair;
- the MapLibre canvas, controls, AOI, attribution, and geographic basemap render;
- keyboard/screen-reader controls expose the same acquisition identities and pair actions without map gestures; and
- the browser console contains no warnings or errors.

Versioned screenshots capture the 1280×720 candidate-pair dialog, the 390×844 mobile results path, and a 720×900 responsive viewport equivalent to a 1440-pixel layout at 200% zoom. The latter proves responsive reflow and no horizontal overflow; it is not a substitute for a manual browser-zoom or assistive-technology pass.

- [Desktop candidate-pair review](./evidence/eat-018-desktop-pair-review.jpg)
- [Mobile non-map results](./evidence/eat-018-mobile-results.jpg)
- [200% responsive viewport equivalent](./evidence/eat-018-200-percent-viewport-equivalent.jpg)
- [Global Sacramento place resolution](./evidence/eat-018-global-place-search.jpg)

A bounded live request resolved `Sacramento, California` through the backend to `Sacramento, Sacramento County, California, United States`, centered a 0.15° × 0.15° AOI, exposed OpenStreetMap attribution, rendered the geographic basemap, and produced no page overflow. This is direct, explicit geocoding—not autocomplete—and does not imply SAR coverage at that location.

With Umbra intentionally deselected for a fast live check, the local API returned 15 actual Sentinel-1 acquisition records for the approved Bingham Canyon AOI and 2025-06-01 through 2025-08-01 range. The UI displayed `Sentinel-1 complete · 15 records`, source links, licenses, metadata cards, and the corresponding provider footprints. These are provider-reported availability records, not imagery pixels or scientifically approved pairs.

## Provisional performance budget

Pending owner agreement, use these EAT-018 limits:

- MapLibre lazy chunk: at most 300 kB gzip;
- total first Explore JavaScript, including MapLibre: at most 450 kB gzip;
- application CSS: at most 25 kB gzip; and
- no raster acquisition download during catalog search.

Current output is within these provisional limits. Basemap tile transfer remains external and must receive a production provider, privacy, caching, attribution, and terms decision before deployment.

## Remaining before EAT-018 completion

- a production geocoder/basemap provider, privacy, caching, SLA, and terms decision beyond the bounded public-OSM development adapters;
- manual browser-zoom and assistive-technology evidence;
- pointer rectangle handles/drag editing beyond the implemented two-corner redraw and exact-coordinate path;
- owner agreement on the performance budget; and
- a production basemap decision. The OpenStreetMap development tile endpoint is not the production configuration.
