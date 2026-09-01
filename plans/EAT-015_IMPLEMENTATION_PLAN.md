# EAT-015 implementation plan

Status: complete in [PR #48](https://github.com/carlwelchdesign/earth-atlas-ai/pull/48),
merged as `cbaf17f36713d923b91eef7de3556fa81e247bf8` after green CI.

## Outcome

Package the truthful standalone owner-review demo as reproducible non-root containers while retaining native `uv`/npm development.

## Sequencing decision

Carl's instruction to finish the project authorizes release-packaging work to proceed while EAT-012 awaits external qualified SAR review and EAT-013 remains gated. The package ships with AI disabled and describes the real benchmark and AI summaries as unavailable roadmap. This changes execution order, not the scientific or public-release gates.

## Work

1. Add exact-version, lockfile-driven backend and workbench container builds, non-root runtimes, health checks, a same-origin API proxy, and secret-safe build contexts.
2. Add a standalone Compose stack with health dependencies, explicit data storage, a synthetic-default path, and an optional read-only prepared-demo mount.
3. Persist append-only local assessment events safely across reload and container restart for the same browser/origin, with bounded validation and tests.
4. Add native/container runbooks, operator/story guidance, dataset/architecture/AI/license/security/sensitivity review evidence, and fresh-build verification scripts.
5. Capture desktop/tablet/mobile release evidence, then replace the stale README with a shipped/prototype/roadmap account and final screenshots.
6. Run native and container verification, publish unsigned commits/PR, require green CI, merge, and update Asana.

## Boundaries

- No raw SAR, cache, credentials, assessment state, or generated large artifacts enter an image or Git.
- The base stack uses the explicit synthetic fallback. The prepared profile mounts an already generated, licensed display bundle read-only.
- Browser-local assessment persistence is single-origin owner-review storage, not a multi-user audit service.
- MapTiler and AI keys are not required or embedded.
- Public deployment/publication, calibrated SAR claims, and AI summaries remain unavailable and separately gated.
