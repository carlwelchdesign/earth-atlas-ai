# EAT-015 owner-review release evidence

Status: owner-review package verification passed on 2026-08-25. Public release is not approved.

## Package under review

- Standalone backend and workbench images use exact runtime image tags, lockfile
  installation, non-root users, health checks, read-only root filesystems,
  dropped Linux capabilities, and `no-new-privileges`.
- Compose binds web and API ports to loopback, starts the workbench only after a
  healthy backend, and names the local data volume explicitly.
- The optional prepared profile mounts validated display derivatives read-only.
  Source imagery, caches, provider payloads, credentials, and assessment data are
  excluded from the image build context and Git.
- The browser-local assessment store validates untrusted persisted data, caps it
  at 1,000 events and 512 KB per bundle, preserves append-only correction chains,
  and fails visibly without hiding the evidence workspace.

## Review matrix

| Review | Evidence | Result |
| --- | --- | --- |
| Architecture | deterministic backend, portable bundle boundary, optional adapters, same-origin web proxy | pass |
| Dependency reproducibility | `uv.lock`, `package-lock.json`, exact base-runtime tags and manifest digests | pass |
| Secrets | narrow `.dockerignore`; repository secret scan in `make check`; no runtime credentials required | pass |
| License/attribution | MIT software separated from Umbra CC BY 4.0 and basemap/provider terms | pass |
| Sensitive site | owner-approved civilian Bingham Canyon boundary; no new site added | pass for private owner review only |
| AI boundary | no model invocation or provider key; EAT-013 remains gated | pass |
| Scientific claims | candidate language and unresolved EAT-012 adjudication disclosed | pass |
| Accessibility/responsive | keyboard, automated accessibility, desktop/tablet/mobile evidence | pass |
| Container lifecycle | clean build, health, web/API, prepared mount, restart persistence, shutdown | pass |

## Verification result

- `make check`: pass — 121 backend tests, 79 frontend tests, 84%/84% line
  coverage respectively, format, lint, strict typing, production build, and secret
  scan all passed.
- Clean multi-stage build: pass. Runtime inputs resolved to the pinned manifest
  digests. The backend image is 170,327,395 bytes and runs as UID/GID 10001; the
  workbench image is 23,391,151 bytes and runs as nginx UID 101.
- Runtime hardening: pass. Both containers were healthy with read-only roots,
  attempts to write `/root-probe` failed, host ports were loopback-only, and the
  same-origin `/health` proxy returned the backend `0.1.0` response.
- Base and prepared Compose lifecycle: pass. Both `make container-check` and
  `ECHOATLAS_VERIFY_PREPARED=1 make container-check` built, started, waited for
  health, checked routes, printed state, and shut down without deleting the named
  volume.
- Prepared mount: pass. `/generated-demo/bundle.json` loaded
  `bundle-change-9c8a27b2a55081fc6b07` with 26 candidates and real public Umbra
  display imagery.
- Assessment persistence: pass. A synthetic-bundle event with note
  `Container restart persistence evidence.` remained current and visible in
  History after the workbench container restarted and the page reloaded.
- Production dependency audit: `npm audit --omit=dev --audit-level=high` reported
  zero vulnerabilities. Lockfiles remain the canonical complete inventories.

## Existing interaction evidence

- [Global place search](evidence/eat-018-global-place-search.jpg)
- [Accessible pair review](evidence/eat-018-desktop-pair-review.jpg)
- [Comparability review](evidence/eat019-comparability-review.png)
- [Explore-to-Analyze handoff](evidence/eat019-analyze-handoff.png)
- [Mobile results](evidence/eat-018-mobile-results.jpg)
- [200% viewport equivalent](evidence/eat-018-200-percent-viewport-equivalent.jpg)
- [Prepared container desktop](evidence/eat015-container-desktop.png)
- [Prepared container tablet](evidence/eat015-container-tablet.png)
- [Prepared container mobile](evidence/eat015-container-mobile.png)

The source commit and pull request are added to the ticket evidence at delivery.
CI must remain green before merge and EAT-015 completion.
