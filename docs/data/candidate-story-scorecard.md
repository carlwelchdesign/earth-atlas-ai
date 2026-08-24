# EAT-003 candidate story scorecard

Date evaluated: 2026-08-24

Status: recommendation prepared; owner approval pending

Scale: each rubric dimension scores `0` (fails), `1` (conditional), or `2` (strong). A zero in pair access/overlap, public suitability, or sensitivity is disqualifying regardless of total.

External context establishes only that a civilian event or infrastructure program exists. It is not pixel-level ground truth and does not prove that any SAR difference is meaningful, causal, or damaging.

## Score summary

| Candidate | Civilian public story | Two usable overlapping GECs | Temporal separation | Polarization/resolution | Geometry documented | Reproducible size/access | External context | Sensitivity boundary | Total | Decision |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Bingham Canyon mine surface-change review | 2 | 2 | 2 | 2 | 2 | 2 | 1 | 1 | **14/16** | Recommend, approval pending |
| Western Sydney airport construction review | 2 | 2 | 2 | 2 | 2 | 1 | 2 | 0 | **13/16** | Reject for public demo sensitivity |
| Palisades fire context review | 2 | 0 | 0 | 2 | 1 | 1 | 2 | 0 | **8/16** | No-go: no pre-fire acquisition in sampled adjacent catalog |
| Francis Scott Key Bridge collapse | 2 | 0 | 0 | 1 | 1 | 0 | 2 | 1 | **7/16** | No-go: post-event only and legacy objects unresolved |

## Recommended: Bingham Canyon mine

Story framing: compare two public Umbra GEC acquisitions over the central open-pit mine during an officially documented period of ongoing mine development. The workflow may surface review candidates, but it must not claim that a candidate is excavation, production, damage, equipment movement, or any other semantic change without analyst evidence.

Why it leads:

- the proposed pair is 25 days apart and has 99.896659% footprint overlap in both directions;
- both are `GEC`, `VV`, left-looking, ascending, and approximately 0.5 m in range and azimuth resolution;
- incidence differs by 2.138753 degrees and both public objects are byte-range accessible;
- the two GEC files total 524,289,889 bytes, small enough for the EAT-004 bounded acquisition/cache work;
- Rio Tinto describes Kennecott as a civilian integrated mining operation, documents the South Wall Pushback and other growth work, and offers a public visitor experience. This supports the infrastructure context only; it is not truth for the pixels. [Rio Tinto Kennecott](https://www.riotinto.com/en/operations/us/kennecott)

Sensitivity boundary:

- process only the central pit AOI in the proposed manifest;
- exclude the smelter, refinery, tailings facilities, nearby communities, and access roads;
- do not identify or track workers, vehicles, or equipment;
- do not infer output, intent, safety, environmental compliance, or operational status;
- do not publish full-resolution derivatives until the later sensitive-site and owner release gates pass.

## Reserve: Western Sydney airport construction

The pair is technically credible: 38 days apart, same product/polarization/look/orbit, identical nominal resolution, 2.306537-degree incidence difference, and about 90% mutual footprint overlap. Both objects support range requests. It is not recommended for the public demo because the files total 2.35 GB and a high-resolution operational-airport narrative presents a stronger critical-infrastructure sensitivity concern. The official airport site labels the project an airport construction milestone; that context would not prove visible construction change. [Western Sydney International Airport construction milestone](https://www.wsiairport.com.au/media-releases/airport-construction-milestone)

## No-go: Palisades fire

The January catalog has public GEC acquisitions over the area on January 8 and 9, after the fire began, but the sampled December catalog had no matching pre-event acquisition. CAL FIRE records the Palisades Fire as starting January 7, 2025. A post-only pair cannot support the planned before/after story, and residential-area sensitivity is too high for the first public demonstration. [CAL FIRE Palisades Fire](https://www.fire.ca.gov/incidents/2025/1/7/palisades-fire)

## No-go: Francis Scott Key Bridge collapse

Umbra has multiple March 26-28 GEC acquisitions over the bridge after the collapse, but the sampled February catalog had no matching pre-event acquisition. The legacy 2024 STAC items also lack the task identifier used by the current public-S3 resolver, so exact GEC object access is not pinned. NTSB records the bridge strike and collapse on March 26, 2024; that establishes event context, not pixel interpretation. [NTSB investigation DCA24MM031](https://www.ntsb.gov/investigations/Pages/DCA24MM031.aspx)

## Remaining approval gate

Carl must explicitly approve the Bingham Canyon public story and the sensitivity boundary in Asana before the manifest status changes from `awaiting_owner_approval` to `approved`. If it is rejected, Western Sydney remains a technical reserve but requires a revised sensitivity decision; the two disaster candidates remain no-go.
