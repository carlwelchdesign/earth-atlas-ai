# SAR preview processing

EAT-005 turns the exact, checksum-verified GEC pair from the approved selection manifest into local engineering previews. The stage is deterministic and provider-neutral. It does not detect change, calibrate backscatter, identify objects, or authorize publication.

## Processing contract

The default Bingham Canyon run uses:

- the approved `processing_aoi` polygon and its stored geometry checksum;
- `EPSG:32612` as the common projected CRS;
- a north-up, one-meter grid whose bounds are snapped outward to whole pixels;
- single-band numeric GeoTIFF inputs with a declared CRS, invertible transform, and nodata value;
- bilinear reprojection onto the common grid, followed by exact AOI masking;
- no speckle filter;
- an independent 2nd-to-98th percentile display stretch for each acquisition.

Independent stretches make each image readable, but their tones are not directly calibrated measurements. Bilinear resampling changes source pixel values, and no speckle suppression is performed. The outputs therefore remain engineering review artifacts rather than evidence of confirmed change, cause, damage, or confidence.

## Outputs and immutability

Run identity is derived from the selection ID, AOI geometry checksum, pinned input checksums, and all processing parameters. A successful run is written atomically to:

```text
data/derived/<selection-id>/<run-id>/
  aligned/before.tif
  aligned/after.tif
  previews/before.png
  previews/after.png
  thumbnails/before.png
  thumbnails/after.png
  quality-report.json
  processing-manifest.json
```

Existing run directories are immutable. Repeating the same run requires using its existing outputs or deliberately selecting a different data root; the processor will not overwrite the directory.

The aligned GeoTIFFs preserve float intensity values and use NaN outside the valid AOI. PNG previews reserve zero for invalid pixels and map valid pixels into 1–255. The quality report records source metadata, the common grid, AOI coverage, value and normalization ranges, and interpretation warnings. The run manifest records input identities, license provenance, parameters, software versions, artifact hashes, interpretation limits, and sensitivity controls.

All source and derived rasters remain under the Git-ignored `data` tree.

## Run locally

After the approved pair is cached, run:

```sh
uv run echoatlas-process-previews \
  --manifest fixtures/demo/selection-manifest.v1.json \
  --data-root data
```

The CLI validates the cached objects again before processing. Changing a processing parameter creates a different deterministic run ID.

## Verification boundary

Synthetic golden tests declare exact grid and normalization expectations, allow at most one grayscale level of preview rounding, and cover missing CRS, missing nodata, multiple bands, corrupt files, non-overlap, and immutable reruns. The approved full-size pair must also complete locally with both roles meeting the configured AOI coverage threshold and must receive a visual preview review.

These checks establish reproducible software behavior. A qualified SAR reviewer remains required before scientific or calibrated performance claims.

The approved local verification run `preview-48b949a1b72ac7f8f54d` completed on a 2,763 by 3,922 pixel grid. Both roles covered all 10,533,042 approved-AOI pixels, and visual review confirmed matching crop and orientation with no obvious clipping or blank-data seams. The generated files remain local, Git-ignored, and release-gated.
