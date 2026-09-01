# EAT-025 — Refresh README Analyze screenshot after viewport fix

Status: complete

Asana: [EAT-025](https://app.asana.com/1/9789386902387/project/1217790716964797/task/1218039562751547)

Branch: `docs/eat-025-readme-analyze-capture`

## Outcome

The repository README shows a high-quality production Analyze capture that reflects EAT-024 instead of the prior stretched-page layout.

## Acceptance

- [x] Capture the live public Analyze workspace at a desktop viewport after selecting a representative candidate.
- [x] Show the Explore/Analyze navigation, real public Umbra-derived comparison, bounded candidate queue, and useful evidence content in one balanced frame.
- [x] Preserve the EAT-021 image as historical release evidence; store the replacement under EAT-025.
- [x] Update the README image reference and descriptive alt text.
- [x] Verify image dimensions, Markdown path, repository checks, merged GitHub rendering, and public source behavior.

## Non-goals

- Changing the Analyze interface or evidence claims.
- Rewriting the README narrative.
- Replacing historical release evidence in place.

## Capture evidence

- Source: public production [earth-atlas-ai.vercel.app](https://earth-atlas-ai.vercel.app).
- Viewport: 1440 x 900 CSS pixels.
- State: Analyze, two-up comparison, candidate `C-021` selected with Review evidence visible.
- Geometry: document 900 px client / 900 px scroll height; candidate queue 388 px client / 1,789 px scroll height with `overflow-y: auto`.
- Artifact: JPEG, 1440 x 900, 204,838 bytes; repository object `fce1f7c7a92139b0e09b06e2d026a1b2ccdfaf80`.
- Delivery: [PR #59](https://github.com/carlwelchdesign/earth-atlas-ai/pull/59) merged after Backend, Workbench, and Vercel checks passed.
- GitHub verification: rendered README references the EAT-025 path and the raw `main` asset returns HTTP 200 with `content-type: image/jpeg`.
- Repository verification: `make check` passed with 114 backend tests, 77 frontend tests, build, and secret scanning.
