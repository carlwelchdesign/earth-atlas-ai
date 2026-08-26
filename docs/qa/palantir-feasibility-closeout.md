# Palantir feasibility closeout evidence

Date: 2026-08-25

Ticket: EAT-014

Decision: **adjust**

## Proven live

- AIP Developer Tier enrollment and authenticated Foundry inventory.
- Deterministic bundle projection and version 1.3.0 normalized import package.
- Five non-empty domain object types, six link types, native timestamp transforms, and a separate synthetic raster media-reference object.
- A 64×64 synthetic GeoTIFF accepted by a Media Set and persisted in a native Map template at a 2 km scale.
- Restricted public browser application with six object types, six link types, Ontology/media-set read only, and no actions, functions, projects, secret, service user, or write scope.
- Published application OSDK and private static hosting.
- Hosted OAuth/query profile reporting one synthetic analysis run as available.
- Deployed asset `0.4.0`: 472 KB, 16 files, SHA-256 `275189198bac11fee3463586f1b45d0f4f26d0d42a70e944e54466dfbd14b513`, two 361×512 Umbra-derived previews, 26 candidate records, approved central-pit boundary, CC BY 4.0 attribution, and explicit reduced-diagnostics warning. Preview and production checks recorded both images loaded and no browser warnings or errors.
- Enrollment usage checkpoint: 0.00 Foundry compute-seconds, 0.00 Ontology GB-months, and 0.00 Foundry storage GB-months over the inspected 30-day window; Small AIP activity was enrollment-wide and not attributed to EchoAtlas.

## Durable application evidence

The same validated real-derived bundle used by hosted asset `0.4.0` is shown below in the standalone workbench after the exact acquisition-ID handoff. This screenshot is local application evidence, not a claim that the image pixels are served through a Foundry Media Set.

![Validated Bingham Canyon evidence profile](evidence/eat019-analyze-handoff.png)

Live hosted verification is preserved by the deployment version, archive hash, application/resource restrictions, timestamps, and Asana execution record. A fresh browser context redirected to Palantir login during closeout; no screenshot was relabeled as authenticated live evidence.

## Unproven and intentionally retained

- Raw or derived real Umbra GeoTIFFs were not uploaded to a Foundry Media Set or mapped through the Ontology. Static hosted PNG evidence does not prove that path.
- The retained synthetic spike resources were not deleted merely to manufacture a cleanup result. Cleanup behavior is unexercised and remains an operator caveat.
- Exact Developer Tier duration, country/term constraints, and numeric compute/storage/GPU/user ceilings were not displayed.
- AIP catalog access and unrelated enrollment activity do not prove model enablement, terms acceptance, cost, or an EchoAtlas invocation.
- Static hosting omits optional full-resolution diagnostics and does not host the Python processing backend.

## Decision rationale

Use Foundry only as an optional downstream Ontology, media, Map, restricted application, and private-hosting layer when a deployment specifically benefits from those capabilities. Keep deterministic acquisition, processing, candidate generation, bundle validation, assessments, and the complete standalone demo outside Foundry. Do not make public launch, cost, real-imagery scale, cleanup, or AIP claims without separate evidence and approval.
