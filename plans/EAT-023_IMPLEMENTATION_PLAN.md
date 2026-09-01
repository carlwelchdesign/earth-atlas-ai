# EAT-023 — Restore Analyze navigation and bound non-map results

Status: complete

Asana: [EAT-023](https://app.asana.com/1/9789386902387/project/1217790716964797/task/1218038867181516)

Branch: `fix/eat-023-navigation-scroll`

## Outcome

Restore the visible Explore/Analyze navigation contract across every Analyze state and keep the equivalent non-map acquisition path usable without allowing its result cards to make the whole Explore page excessively tall.

## Acceptance

- [x] Analyze shows the same primary Explore/Analyze navigation model as Explore, with Analyze identified as the current mode and Explore always actionable.
- [x] Analyze loading and rejected-bundle states preserve the Explore return path.
- [x] The acquisition results list is a named, keyboard-focusable scroll region with a bounded height at desktop and mobile breakpoints.
- [x] The result summary, provider status, and warnings remain visible outside the scrolling card list.
- [x] Regression tests fail before the fix and pass afterward.
- [x] Focused tests, `make check`, and public Vercel browser verification pass.
- [x] [PR #55](https://github.com/carlwelchdesign/earth-atlas-ai/pull/55) is merged; production deployment `dpl_6x6f7cLcyG9XDLEyAKmBAxNZPLrB` is Ready and Asana completion evidence is recorded.

## Verification

- Focused App and Explore regression suite: 38 tests passed.
- `make check`: 114 backend tests, 76 frontend tests, formatting, lint, mypy, TypeScript, production build, and secret scan passed.
- GitHub: Backend, Workbench, and Vercel checks passed on PR #55.
- Public browser: Analyze marked current in the restored primary navigation and Explore returned to the global discovery view.
- Public browser: 17 acquisitions rendered inside a 476 px scroll viewport with 3,601 px of scroll content; the containing panel remained bounded at 626 px and no production console errors were recorded.

## Non-goals

- Changing catalog providers, SAR processing, pair-selection policy, or scientific interpretation.
- Reworking the approved Explore layout beyond the requested navigation and height constraints.
