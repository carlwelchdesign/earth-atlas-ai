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

Open `data/review/eat012-bingham-v1/index.html` locally. The packet provides synchronized before, after, and candidate-overlay crops for all 26 candidates. Decisions and notes stay in browser storage until explicitly exported as JSON.

Review choices have deliberately narrow meanings:

- `Evidence supports follow-up; independent region required` records that a candidate merits separate reference labeling. It does not turn the candidate geometry into truth.
- `False positive / artifact` requires one declared failure class.
- `Unresolved` preserves uncertainty without forcing a label.

The export is audit evidence for the labeling process. It is not accepted directly by `echoatlas-evaluate`, because evaluating a candidate against its own reviewed geometry would be circular.
