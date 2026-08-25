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
