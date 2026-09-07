# EAT-032 Nepal release-candidate evidence

Verified locally on 7 September 2026 PDT from `main` commit `4f6a99b` plus the
EAT-032 validation branch.

## Data and geographic assets

`uv run --group processing python scripts/prepare_nepal_case.py` rebuilt the
case from the four pinned source files. `scripts/verify_nepal_case.py` then
verified:

- the four source SHA-256 values match the published dataset card and generated manifest;
- the declared WGS 84 extent is `85.3000, 28.0800, 85.4200, 28.2800`;
- zooms 8–14 contain exactly 95 expected Web Mercator tiles per date;
- every tile is a 256 × 256 RGBA PNG with imagery, and two edge tiles per date preserve transparent nodata;
- the before and after thumbnails are 720 × 720;
- all five shared-grid landmarks have a measured residual of 0.0 m, below the approved 10 m tolerance;
- three attribution entries remain present, including modified Copernicus Sentinel data.

The residual test establishes common-grid display registration. It does not
establish absolute orthorectification accuracy or validate a scientific damage
claim.

## Product verification

- Focused component tests cover synchronized camera copying, north-up/zero-pitch enforcement, coverage status, side-by-side, swipe, date toggles, static fallback, append-only correction, reload, version isolation, storage failure, deterministic export, escaped user text, and exact source/date reconciliation.
- Permanent regressions require one consolidated quality summary and keep the canyon Analyze and Explore workflows addressable at `/analyze` and `/explore`.
- `axe-core` reports no automated violations for the Nepal overview and the complete non-map investigation path, with color contrast assessed separately by visual review because JSDOM cannot compute it.
- Chromium evidence exists at 1280 × 900 and 390 × 844. The narrow view retains one geographic map, fixed dates, observations, assessment state, and all comparison modes.
- The final local Playwright run completed all three workflows in 5.2 seconds:
  the Nepal assessment/reload/export flow, the bounded Explore search and real
  prepared-pair handoff, and the Bingham Canyon Analyze viewport regression.

## Reference performance

Reference: local Chromium, 1280 × 900, loopback Vite server, Mac development
host. The overview became DOM-complete in 88.3 ms. The two 720 px prepared
thumbnails completed by 564.1 ms. This passes the five-second prepared-imagery
target on the recorded reference setup. Production timing is measured again in
EAT-033 and is a separate result.

The automated flow passes the three-minute interaction target. The planned
five-person first-time-reviewer study has not occurred and is not represented as
complete; it remains human usability evidence to collect after release.
