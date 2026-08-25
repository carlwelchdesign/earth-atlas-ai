# Change-candidate evaluation labeling guidance v1

Status: engineering guidance awaiting qualified SAR-domain review.

This guide defines review labels for EchoAtlas change-candidate evaluation. Labels describe agreement between a machine candidate and a reviewer-drawn region. They do not establish damage, cause, identity, intent, safety, or operational status.

## Dataset separation and provenance

- Assign every source pair a stable fixture ID. A fixture ID used to choose thresholds, morphology, registration tolerance, or other processing policy is a tuning fixture and cannot appear in the evaluation set.
- Record the acquisition IDs, checksums, license, access date, processing run, grid, software commit, and labeling-guide version for derived public-SAR cases.
- Synthetic cases must say how their geometry was constructed and remain labeled `software-verification`; they cannot be promoted to a pipeline benchmark.
- Each region and false-positive annotation records one of: `pending`, `synthetic-established`, `engineering-reviewed`, or `domain-reviewed`. Reviewed labels require reviewer identity and timestamp.

## Reference-region rule

First draw the complete geometry actually reviewed at the declared grid. Only candidates and pixels inside that geometry enter denominators. Within it, draw the smallest contiguous region that the reviewer can support from the declared before/after evidence. Split spatially separate regions. Do not draw a region from external event knowledge alone. If radar evidence is ambiguous, leave the region pending and record the ambiguity instead of forcing a positive label.

Candidate matching is one-to-one. A candidate and reference region match only when their rasterized intersection-over-union meets the evaluation set's declared threshold. Multiple candidates cannot receive credit for one reference region, and one candidate cannot satisfy multiple reference regions.

## False-positive taxonomy

Classify an unmatched candidate only when the available evidence supports the class. Otherwise use `other` with a note or leave it unclassified.

| Class | Use when the dominant response is consistent with |
| --- | --- |
| `geometry` | viewing-geometry or terrain response not better described as shadow/layover |
| `water-moisture` | surface water, soil moisture, precipitation, or related dielectric variation |
| `speckle` | granular coherent-noise response or insufficiently filtered isolated texture |
| `shadow-layover` | radar shadow, foreshortening, or layover tied to terrain/building geometry |
| `registration-artifact` | spatial misalignment, resampling edge, or parallax-like boundary response |
| `other` | supported artifact class outside the declared categories |

## Adjudication

Two qualified reviewers should independently label real public-SAR cases. Disagreements remain unresolved until adjudicated and must not enter a published benchmark denominator. The benchmark report must identify reviewer role, unresolved cases, exclusions, and any case used during tuning.
