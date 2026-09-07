# EAT-033 Nepal production release

Production verification: 7 September 2026 PDT

- Release branch: `release/2026-09-07-nepal`
- Application commit: `b4a3d40`
- Release merge-back: [PR #68](https://github.com/carlwelchdesign/earth-atlas-ai/pull/68)
- Verified deployment: `dpl_6gHbwWiEuMwxYazScBm9umRUjdFA`
- Immutable deployment URL: <https://earth-atlas-qrqj4uh1f-carlwelchdesigns-projects.vercel.app>
- Public alias: <https://earth-atlas-ai.vercel.app>
- Rollback target: `dpl_5pVfcaEx1dPjrqxfBRNVegEYV1Uw`

The deployment was built from an explicit CLI upload allowlist so Git-ignored
prepared Nepal assets entered the Vite static build while raw data, local
environments, plans, and QA files stayed out of the upload.

## Public evidence

- The public `case.json`, before/after thumbnails, and a sampled zoom-14 RGBA
  tile matched their local SHA-256 hashes byte for byte.
- Production Playwright passed all four tests in 8.0 seconds: Nepal assessment,
  reload, and brief export; narrow Context geometry; Explore real-pair handoff;
  and the Bingham Canyon Analyze viewport regression.
- Chromium verified the Nepal root at 1440 × 900 and the investigation at
  390 × 844. A mobile flex-basis defect found in the first capture was corrected
  before final acceptance; **Compare imagery** now remains in the initial view.
- Production overview timing measured DOM complete at 168.6 ms and both 720 px
  thumbnails complete by 424.1 ms on the recorded browser/network, within the
  five-second target.
- Vercel inspection reported `READY`, production target, and the expected public
  alias. The post-verification error-log query returned no error entries.

Artifacts:

- `images/eat-033-production-desktop.png`
- `images/eat-033-production-narrow.png`

The five-person first-time-reviewer study remains unperformed human evidence and
is not claimed by this release record.

## Post-release packaging correction

The merge-back to `main` triggered a Git-connected Vercel deployment that did
not contain the Git-ignored prepared Nepal assets. The SPA rewrite returned
`index.html` for the missing `case.json`, which initially masked the regression.

PRs [#69](https://github.com/carlwelchdesign/earth-atlas-ai/pull/69) and
[#70](https://github.com/carlwelchdesign/earth-atlas-ai/pull/70) corrected the
recursive CLI upload allowlist. A follow-up release disables Git-connected
deployments in `vercel.json`; production is deployed only through the documented
CLI release path that packages the prepared assets. A repository test preserves
both controls.

The corrected deployment must pass these checks before its alias is accepted:

- the public and local case-manifest SHA-256 values match;
- both thumbnails and a sampled RGBA raster tile load as PNG files;
- all four public Playwright workflows pass; and
- a repeated alias check after the merge-back still returns the case manifest,
  rather than the SPA fallback.
