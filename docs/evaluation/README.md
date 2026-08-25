# Pipeline evaluation

EAT-012 introduces a provider-neutral evaluation harness and a versioned synthetic verification set. The harness reports candidate, pixel, and matched-region metrics with explicit numerators, denominators, and nullable values.

The committed synthetic set verifies arithmetic, one-to-one matching, tuning/evaluation separation, and false-positive accounting. It contains no SAR pixels and has not been reviewed by a qualified SAR practitioner. Its results are not a pipeline-accuracy claim.

The committed [synthetic baseline](synthetic-baseline-v1.json) deliberately contains one exact match and one constructed example of each false-positive class. Its `1/7` candidate precision and `9/30` pixel precision are fixture arithmetic, not observed model or pipeline performance.

Run it with:

```sh
uv run echoatlas-evaluate \
  --evaluation-set fixtures/evaluation/synthetic-v1/evaluation-set.json \
  --output docs/evaluation/synthetic-baseline-v1.json
```

Metric grain and limits:

- Candidate precision uses matched candidates divided by emitted candidates. It is null when no candidates are emitted.
- Candidate recall uses matched reference regions divided by eligible reference regions. It is null when there are no eligible reference regions.
- Candidate F1 uses `2TP / (2TP + FP + FN)` and is null when that denominator is zero.
- Pixel precision, recall, IoU, and F1 operate on the union of rasterized regions inside the explicitly reviewed evaluation geometry. Pixel count is grid-dependent and does not measure physical importance.
- Candidate metrics include only candidates with at least one rasterized pixel inside the evaluated geometry. Geometry is transformed from the case's declared geometry CRS to its evaluation grid before matching.
- Region mean IoU averages only one-to-one candidate/reference matches that meet the declared threshold. It is null when no regions match and must be read alongside false negatives.
- False-positive categories apply only to unmatched candidates and remain unclassified unless an annotation exists.
- Pending labels are rejected from metric denominators. A `pipeline-benchmark` manifest additionally requires derived-public-SAR source artifacts with checksums and domain-reviewed labels throughout.

## Real benchmark completion gate

Before this becomes a pipeline benchmark, the Bingham Canyon evaluation cases need immutable source/run provenance, labels made under the guidance, independent qualified SAR review and adjudication, and confirmation that none of the evaluation pairs influenced pipeline parameters. Until then, EAT-012 baseline evidence is limited to evaluator correctness.

## Local candidate-review packet

The review-packet generator validates the selected change run, candidate collection, lineage, artifact sizes, checksums, and image dimensions before producing a local, self-contained review interface. It references the existing local preview and overlay files rather than copying or publishing imagery.

For the approved local run:

```sh
uv run echoatlas-prepare-review \
  --change-run data/derived/echoatlas-bingham-canyon-2025-v1/changes/change-9c8a27b2a55081fc6b07 \
  --preview-run data/derived/echoatlas-bingham-canyon-2025-v1/preview-48b949a1b72ac7f8f54d \
  --output data/review/eat012-bingham-v1
```

Open `data/review/eat012-bingham-v1/index.html` locally. The packet provides synchronized before, after, and candidate-overlay crops for all 26 candidates. Decisions, notes, and provisional polygon drafts stay in browser storage until explicitly exported as JSON.

Review choices have deliberately narrow meanings:

- `Evidence supports follow-up; independent region required` records that a candidate merits separate reference labeling. It does not turn the candidate geometry into truth.
- `False positive / artifact` requires one declared failure class.
- `Unresolved` preserves uncertainty without forcing a label.

The export is audit evidence for the labeling process. It is not accepted directly by `echoatlas-evaluate`, because evaluating a candidate against its own reviewed geometry would be circular.

### Provisional reference-region capture

The packet also provides a separate polygon workspace over the clean after image, without the candidate overlay. A reviewer can add points with a pointer or enter projected `x,y` coordinates directly for keyboard-equivalent access. The interaction supports undo, explicit polygon closure, and a confirmed clear action.

Export version `1.1.0` keeps candidate decisions and `reference_regions` separate. Each region includes its candidate context, declared grid CRS, projected points, raster pixel points, closure state, timestamp, and one of two bounded statuses:

- `draft-incomplete` has points but no valid polygon geometry.
- `provisional-candidate-directed` has closed polygon geometry but still requires independent qualified review and adjudication.

These regions are candidate-directed because the reviewer reached them through the machine-candidate queue. They are not blinded, independent, or adjudicated labels, and the evaluator does not ingest them automatically. A later labeling checkpoint must establish an independently reviewed dataset and record adjudication before pipeline metrics are run.

## Candidate-hidden reference labeling

The separate labeling packet is built from the validated processing run only. It does not read the change run, candidate collection, candidate overlay, candidate identifiers, geometry, or scores. Deterministic overlapping tiles cover the complete preview grid so a reviewer can compare before/after imagery without machine-candidate cues.

For the approved local run:

```sh
uv run echoatlas-prepare-labeling \
  --preview-run data/derived/echoatlas-bingham-canyon-2025-v1/preview-48b949a1b72ac7f8f54d \
  --output data/labeling/eat012-bingham-v1
```

Open `data/labeling/eat012-bingham-v1/index.html` locally. Reviewers can draw multiple regions per tile with a pointer or projected coordinates, record no-region or unresolved tile decisions, preserve incomplete drafts, and export partial or complete coverage. Contradictory decisions are rejected, draft and saved-region removal is explicit, and every export is bound to the processing-manifest checksum.

The packet reduces candidate-confirmation bias but does not prove reviewer independence or expertise. Overlapping-tile regions can duplicate the same visible area. Exported `provisional-candidate-hidden` regions therefore require documented reviewer qualification, deduplication, independent review, and adjudication before conversion to `domain-reviewed` evaluation labels. The evaluator does not ingest this raw export automatically.
