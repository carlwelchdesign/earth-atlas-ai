# Bingham Canyon demonstration dataset card

## Purpose

This is a bounded civilian infrastructure-change demonstration for the EchoAtlas
owner-review workflow. Carl approved the story and sensitivity boundary on
2026-08-24. It is not a benchmark-quality ground-truth dataset.

## Source and license

- Provider: Umbra Lab Inc, Open Data Program
- License: CC BY 4.0 for the source imagery and permitted derivatives
- Selection: two public GEC acquisitions pinned in
  `fixtures/demo/selection-manifest.v1.json`
- Provenance retained: provider item/object identity, source URL/key, acquisition
  time, access date, byte size, ETag, and full-object CRC64NVME checksum
- Software: MIT; the MIT license does not replace the imagery license

The exact identities and checksums live in the manifest rather than this narrative
so they remain machine-verifiable.

## Processing

The prepared comparison uses an approved AOI, an EPSG:32612 one-metre common grid,
bilinear resampling, exact AOI masking, no speckle filter, and independent 2–98%
display stretches. Candidate generation uses an explicit deterministic score,
two-pixel registration tolerance, morphology, connected components, a minimum
component size, and a candidate-count guard. All parameters and artifact hashes
are retained with the run.

## Known limitations

- Independent display stretches can make images easier to inspect but do not
  provide calibrated radiometry.
- The baseline is sensitive to registration, viewing geometry, speckle, terrain,
  moisture, and acquisition differences.
- The 26 candidate regions are machine-generated review prompts, not confirmed
  physical change, damage, cause, or operational truth.
- No qualified independent SAR reviewer has completed adjudication; EAT-012
  remains open. Accordingly, no accuracy, recall, precision, or calibration claim
  is supported.
- The single site does not establish geographic, seasonal, sensor, or event-class
  generalization.

## Sensitivity and publication

The approved scope is a widely documented civilian mine and uses only public open
data. The repository does not contain raw imagery or generated real-data files.
Any public deployment, new high-resolution site, or downloadable derived imagery
requires a fresh license and sensitivity review plus Carl's explicit approval.
