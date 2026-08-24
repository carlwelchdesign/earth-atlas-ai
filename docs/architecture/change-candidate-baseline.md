# Baseline change candidates

EAT-006 consumes one immutable EAT-005 preview run and produces a transparent queue of machine-generated engineering candidates. This is a review baseline, not calibrated SAR change detection. It does not establish confirmed surface change, cause, identity, impact, safety, or operational status.

## Input boundary

Before reading pixels, the processor validates:

- the processing and quality manifests against their runtime models;
- matching processing-run and selection identities;
- the quality-report checksum stored in the processing manifest;
- canonical, run-local aligned-raster paths;
- aligned-raster byte size and SHA-256 against the source artifact records;
- one-band GeoTIFF, CRS, dimensions, affine transform, and NaN nodata against the declared grid.

Any mismatch fails the run. The source EAT-005 directory remains immutable.

## Default engineering policy

For each role, source intensity `x` is converted to the clipped display-normalized value:

```text
n(x) = clip((x - percentile_low) / (percentile_high - percentile_low), 0, 1)
```

The percentile limits are reused exactly from the EAT-005 quality report. Because each role has its own limits, the result is not calibrated backscatter and score magnitude cannot be interpreted as calibrated confidence.

To reduce simple registration responses, the score compares each normalized pixel with the best-matching value in the other image's declared two-pixel neighborhood in both directions:

```text
forward = min |after[p] - before[q]| for q within two pixels of p
reverse = min |before[p] - after[q]| for q within two pixels of p
score[p] = max(forward, reverse)
```

The common-valid mask is eroded by the same tolerance to guard nodata/AOI edges. The default candidate policy is then:

- score threshold: `0.50` on the bounded `0–1` engineering score;
- cleanup: one 3-by-3 binary opening, then one 3-by-3 binary closing;
- connected-component neighborhood: eight-way;
- minimum retained component: 512 pixels, or 512 square meters on the current one-meter grid;
- maximum output count: 500, with fail-closed behavior instead of silent truncation.

Threshold, registration tolerance, cleanup iterations, connectivity, minimum component size, and maximum count are validated run parameters. The defaults were selected to create a review-sized Bingham Canyon demonstration queue. They have not been evaluated against labeled truth or approved by a qualified SAR practitioner.

Binary opening removes isolated foreground fragments; closing fills small gaps. Connected labels are vectorized using the declared raster transform and converted to WGS84 GeoJSON. The implementation follows the documented SciPy morphology/labeling and Rasterio shape-extraction boundaries.

## Candidate contract

Every GeoJSON feature contains:

- a deterministic run-scoped candidate ID;
- the UI-facing label `Change candidate` and status `pending`;
- source processing-run and change-run linkage;
- WGS84 geometry plus projected and WGS84 bounds;
- pixel count and projected square-meter area;
- mean, 95th-percentile, and maximum engineering score;
- mean signed normalized delta and brightening/darkening pixel fractions;
- explicit review and interpretation warnings.

The signed delta is descriptive only. It does not classify a physical process.

## Outputs and reproducibility

Change-run identity is derived from the source processing-run ID, source manifest and quality-report hashes, aligned-raster hashes, every change parameter, and the recorded Git commit:

```text
data/derived/<selection-id>/changes/<change-run-id>/
  change-score.tif
  change-score.png
  candidate-mask.tif
  candidate-overlay.png
  candidates.geojson
  change-manifest.json
```

The output directory is written through a temporary sibling and atomically promoted. Existing successful run directories are immutable. Source and generated imagery remain inside the Git-ignored `data` tree and retain the original release gate.

Run from an existing preview directory:

```sh
uv run echoatlas-change-candidates \
  --preview-run data/derived/echoatlas-bingham-canyon-2025-v1/preview-48b949a1b72ac7f8f54d \
  --data-root data
```

The CLI records the current Git commit automatically. `--software-commit` is available for packaged environments without repository metadata.

## Verification boundary

Golden tests cover one known candidate, deterministic artifact hashes, isolated speckle removal, nodata-edge handling, one-pixel shift tolerance, four/eight-way geometry connectivity, modified source hashes, grid mismatch, manifest mismatch, immutable reruns, and the maximum-candidate fail-closed gate.

The real demonstration run must also be inspected for candidate count, retained pixel fraction, geometry validity, score distribution, and visual overlay quality. This verifies software behavior and queue usability only; it is not a precision/recall or scientific validation result.

The approved local verification run `change-9c8a27b2a55081fc6b07`, produced from preview run `preview-48b949a1b72ac7f8f54d` at code commit `38b860f`, emitted 26 pending candidates. They cover 38,008 of 10,506,334 guarded valid pixels, approximately 0.36%. All geometries, statuses, labels, bounds, raster grids, and artifact records validated. A separate temporary rebuild reproduced the same run ID and all five artifact hashes.

Visual review confirmed a readable, correctly aligned score and candidate overlay. The two-pixel tolerance reduced the initial one-pixel diagnostic from 38 to 26 candidates and from 65,449 to 38,008 retained pixels. Several remaining responses still follow western high-contrast terrain and bench geometry; they must be treated as review items subject to the recorded geometry and registration warnings, not as validated physical changes.
