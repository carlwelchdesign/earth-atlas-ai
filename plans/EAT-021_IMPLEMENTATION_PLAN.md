# EAT-021 — Deploy portfolio-ready EchoAtlas to Vercel

Asana: [EAT-021](https://app.asana.com/1/9789386902387/project/1217790716964797/task/1218037320242154)

Status: complete

## Outcome

Deploy the current Explore-first React application and its bounded provider-metadata API to Carl's Vercel account as a public portfolio demonstration. The deployment must work without Foundry login, preserve the deterministic local processing boundary, and expose limitations where the serverless runtime cannot provide durable job orchestration.

## Architecture

```text
Vercel CDN
  -> Vite/React Explore + Analyze UI
  -> /api/* FastAPI Vercel Function
       -> bounded Umbra public STAC metadata
       -> bounded Copernicus Sentinel-1 STAC metadata
       -> local coordinates / bounded place adapter
       -> stateless pair comparability
       -> synchronous exact-pair prepared-demo handoff

Local/Docker processing remains separate
  -> acquisition download, raster alignment, candidate generation
  -> versioned analysis bundle
```

## Delivery choices

- Keep the browser API prefix explicit as `/api`; local Vite and Nginx proxy that prefix to the existing `/v1` backend contract.
- Use one Python FastAPI function with only the lightweight web dependencies. Move raster/acquisition libraries to the local processing dependency group so Vercel does not install unused native packages.
- Configure Vercel jobs synchronously. The exact approved Bingham Canyon pair may return the checked, reduced, CC BY 4.0 prepared bundle in the same request. Arbitrary pairs fail safely; no serverless background thread or durable queue is implied.
- Commit only the reduced display bundle and two derived PNGs (approximately 340 KB total), never raw GeoTIFFs, provider payloads, caches, change-score rasters, or full candidate overlays.
- Retain public OSM tiles as an attributed low-traffic portfolio fallback. Coordinate search remains local; place-name lookup remains bounded and replaceable. This deployment is a portfolio demonstration, not an SLA-backed operational service.

## Acceptance

- [x] Explore is the landing experience on the public URL.
- [x] MapLibre globe, provider metadata search, result footprints, pair review, and the approved Umbra handoff work.
- [x] The exact Bingham Canyon pair opens the reduced real-derived Analyze bundle; other pairs fail without substitution.
- [x] No login, secret, private map key, proprietary ontology, or raw imagery is required.
- [x] Security headers, SPA fallback, API duration/bundle limits, and ignored deployment files are configured.
- [x] Desktop/mobile browser checks, public endpoint checks, `make check`, and Vercel deployment inspection pass.
- [x] Deployment URL and evidence are recorded in README, plans, GitHub, and Asana.

## Non-goals

- Durable multi-user jobs or assessment storage.
- Real-time wildfire monitoring, alerts, or incident feeds.
- Processing arbitrary remote imagery inside a Vercel Function.
- Scientific validation or calibrated detection claims.

## Verification evidence

- Public URL: <https://earth-atlas-ai.vercel.app>
- Production deployment: `dpl_9xX9HY9QWjhxHwAB3tPmD9Fu93Sf`
- Public catalog smoke: 17 records in 2.46 seconds for the pinned AOI/date window (2 explicit Umbra items and 15 Sentinel-1 records).
- Public end-to-end check: Explore search, exact-pair selection, comparability review, synchronous prepared-bundle handoff, and two loaded imagery views passed in Playwright.
- Responsive evidence: `docs/qa/evidence/eat-021/`.
- Repository gate: `make check` passed with 113 backend tests and 74 frontend tests before the final deployment-only smoke.
