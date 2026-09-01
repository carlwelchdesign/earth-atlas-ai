# EAT-023 — Restore Analyze navigation and bound non-map results

Status: in progress

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
- [ ] Focused tests, `make check`, and public Vercel browser verification pass. Local focused and full checks pass; public verification follows merge.
- [ ] The PR is merged and Asana is moved to Complete with evidence.

## Non-goals

- Changing catalog providers, SAR processing, pair-selection policy, or scientific interpretation.
- Reworking the approved Explore layout beyond the requested navigation and height constraints.
