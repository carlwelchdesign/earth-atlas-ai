# EAT-025 — Refresh README Analyze screenshot after viewport fix

Status: in progress

Asana: [EAT-025](https://app.asana.com/1/9789386902387/project/1217790716964797/task/1218039562751547)

Branch: `docs/eat-025-readme-analyze-capture`

## Outcome

The repository README shows a high-quality production Analyze capture that reflects EAT-024 instead of the prior stretched-page layout.

## Acceptance

- [x] Capture the live public Analyze workspace at a desktop viewport after selecting a representative candidate.
- [x] Show the Explore/Analyze navigation, real public Umbra-derived comparison, bounded candidate queue, and useful evidence content in one balanced frame.
- [x] Preserve the EAT-021 image as historical release evidence; store the replacement under EAT-025.
- [x] Update the README image reference and descriptive alt text.
- [ ] Verify image dimensions, Markdown path, repository checks, merged GitHub rendering, and public source behavior.

## Non-goals

- Changing the Analyze interface or evidence claims.
- Rewriting the README narrative.
- Replacing historical release evidence in place.

## Capture evidence

- Source: public production [earth-atlas-ai.vercel.app](https://earth-atlas-ai.vercel.app).
- Viewport: 1440 x 900 CSS pixels.
- State: Analyze, two-up comparison, candidate `C-021` selected with Review evidence visible.
- Geometry: document 900 px client / 900 px scroll height; candidate queue 388 px client / 1,789 px scroll height with `overflow-y: auto`.
