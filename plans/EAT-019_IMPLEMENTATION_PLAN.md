# EAT-019 implementation plan

Status: implementation and local acceptance complete on `feature/eat-019-explore-analyze` from merged main `3e6d1db`; PR and remote CI pending.

## Outcome

Connect an explicitly reviewed Explore pair to the existing provider-neutral Analyze bundle without making scientific-validity claims or coupling deterministic processing to MapLibre, deployment vendors, or AI.

## Boundaries

1. A deterministic selection service validates the AOI and normalized catalog records, orders before/after timestamps, computes geometric and metadata comparability evidence, and returns a frozen content-hashed manifest.
2. Processing is a separate injected runner. The default local runner may load only a configured prepared bundle, bounds its path and size, and verifies that its acquisition identities exactly match the immutable manifest.
3. A bounded in-memory job coordinator exposes queued, running, succeeded, failed, and cancelled states. Cancellation is cooperative, retry creates a new job linked to the original, and completed records are capped.
4. The Explore dialog first presents comparability evidence and warnings. Processing begins only after a second explicit action. Success passes the validated bundle to the existing Analyze workbench and the existing Explore navigation remains available.
5. Catalog metadata is not imagery. A job that has no configured prepared bundle fails explicitly; it never substitutes synthetic pixels or labels a pair scientifically valid.

## Verification

- Deterministic manifest hashing, source/provenance retention, AOI hashing, pair ordering, overlap failure, and provider-specific fixture paths.
- Job state, bounded capacity, success, configured-bundle identity validation, failure, cancellation, and retry.
- API contract and safe errors.
- Explore comparability-before-processing, job progress, cancellation, retry, success handoff, and no-comparable-pair behavior.
- Existing Analyze flow receives the validated bundle and retains a clear return to Explore.
- `make check`, desktop/mobile browser verification, secret scan, unsigned commits, PR, and Asana evidence.

## Non-goals

- Downloading arbitrary catalog imagery inside the browser.
- Calling a selected pair scientifically valid.
- Paid acquisition ordering, AI interpretation, vendor-only execution, calibrated truth, or public operational deployment.
