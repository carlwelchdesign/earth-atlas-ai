# EchoAtlas Explore v1 design validation

Status: prototype walkthrough verification complete and approved by Carl Welch on 2026-08-25.

Date: 2026-08-25

Artifacts:

- [Implementation specification](explore-interface-v1.md)
- [Review prototype](../../prototypes/eat-des-002/index.html)
- [EAT-DES-002](https://app.asana.com/1/9789386902387/project/1217790716964797/task/1217846797595944)

## Evidence boundary

This is a structured product-design and implementation-readiness review using synthetic records. It is not external usability research, production MapLibre behavior, live provider evidence, or proof that a selected pair is scientifically suitable. EAT-018 must replace prototype checks with React/browser accessibility and performance evidence.

## Walkthroughs

Desktop, 1440 × 1000:

1. Confirm the coverage boundary before map interaction.
2. Inspect the AOI and exact extent.
3. Search and distinguish Sentinel-1 completion from Umbra status.
4. Select Before and After entirely from the list.
5. Open pair review and confirm retained AOI/source identities and warning.
6. Return to Explore without losing selection.

Mobile, 390 × 844:

1. Search by place or coordinates.
2. Edit the AOI using ordinary controls without map gestures.
3. Reach results before the optional map.
4. Inspect provenance and assign both slots.
5. Open and close pair review without the tray covering actions.

State review uses the selector for loading, no coverage, partial provider, stale, rate limit, invalid AOI, offline, and permission-limited states. Each state must preserve attributable provider meaning and never turn a missing provider into `0 coverage`.

## Acceptance evidence

| Requirement                                                      | Evidence                                                   | Status           |
| ---------------------------------------------------------------- | ---------------------------------------------------------- | ---------------- |
| Explore/Analyze separation and retained state                    | Mode model, navigation rules, pair tray, handoff dialog    | Ready for review |
| Navigation, search, AOI, footprints, filters, pair, mobile       | Workflow, interaction contract, responsive prototype       | Ready for review |
| Truthful states                                                  | Required-state table and prototype selector                | Ready for review |
| Equivalent non-map actions                                       | Results-first mobile order and list actions                | Ready for review |
| Civilian use, sensitivity, provenance, license, machine boundary | Persistent copy and per-record contract                    | Ready for review |
| Desktop/mobile walkthrough and Carl approval                     | Responsive walkthrough passed; Carl approved on 2026-08-25 | Pass             |

## Browser walkthrough evidence

The standalone prototype was served locally and inspected in the in-app Chromium browser. The preferred `agent-browser` executable was unavailable, so verification used the Browser plugin's Playwright surface instead.

| Check               | Evidence                                                                                | Result |
| ------------------- | --------------------------------------------------------------------------------------- | ------ |
| Desktop             | 1440 × 1000; three-region workspace and pair tray visible; document width equals 1440   | Pass   |
| Mobile              | 390 × 844; results before map; pair tray in flow; document width equals 390             | Pass   |
| Narrow mobile       | 320 × 800; results before map; document width equals 320                                | Pass   |
| Tablet / 200% proxy | 768 × 900 reflow with full-width results; document width equals 768                     | Pass   |
| List-only selection | `S1-0612` Before plus `UM-0718` After enables review and reports `pair retained`        | Pass   |
| Handoff focus       | Dialog retains identities, focuses `handoff-title`, and shows the invalid-pair boundary | Pass   |
| Required states     | Loading, empty, partial, stale, rate, invalid, offline, and permission copy inspected   | Pass   |
| Partial provider    | Two Sentinel-1 cards, zero Umbra cards, and attributable sample-limit language          | Pass   |
| Accessible names    | Zero unlabeled buttons/fields; repeated result actions include acquisition ID           | Pass   |
| Runtime             | Meaningful DOM, no error overlay, and zero captured console warnings/errors             | Pass   |

The synthetic map is design evidence only. It does not establish MapLibre quality, real imagery contrast, or provider coverage.

## Findings resolved in the prototype

- The initial mobile sticky pair tray covered filter content; it now stays in document flow below 720 px.
- A four-pixel mobile overflow was removed; document width now equals the 320 px and 390 px viewports.
- Partial, rate-limit, and permission states initially retained contradictory Umbra fixture cards; they now show only successful public-provider records.
- Repeated list actions now include acquisition IDs in their accessible names.

## EAT-018 follow-up gates

- Test actual MapLibre names, focus, reduced motion, and canvas fallback.
- Verify 320/390/768/1440 px and 200% zoom with screenshots and overflow measurements.
- Test keyboard-only search, exact AOI, filters, list selection, pair replacement, and dialog return focus.
- Test provider announcements and card identity with VoiceOver/Safari.
- Define and measure a map/result performance budget.
- Validate real licensed preview/raster contrast; synthetic texture cannot prove it.

## Approval gate

Carl explicitly approved the Explore design in the EAT-DES-002 Codex task on 2026-08-25. The approval covers:

1. separate Explore and Analyze modes with retained AOI, query, and pair state;
2. a MapLibre navigation surface plus an equivalent results-first non-map workflow;
3. explicit AOI, filter, footprint, provider, provenance, license, and failure-state behavior;
4. responsive desktop, tablet, zoomed-desktop, and phone layouts; and
5. the visible boundary that availability and pair selection do not establish scientific suitability.

The approval unlocks EAT-018 implementation. It does not approve production deployment, paid provider access, automated pair validation, or any relaxation of the civilian-use and sensitivity boundaries.
