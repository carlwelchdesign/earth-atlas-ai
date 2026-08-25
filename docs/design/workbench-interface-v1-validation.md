# EchoAtlas workbench v1 design validation

Status: design artifact verification complete and approved by Carl Welch on 2026-08-24; independent user testing remains open.

Date: 2026-08-24

Artifacts:

- [Implementation specification](workbench-interface-v1.md)
- [Review prototype](../../prototypes/eat-des-001/index.html)
- [EAT-DES-001](https://app.asana.com/1/9789386902387/project/1217790716964797/task/1217792507769764)

## Method and evidence boundary

The artifact received a sequential staff product-design pass covering product strategy, information architecture, engineering feasibility, frontend interaction, backend state, UX writing, AI trust boundaries, accessibility, analytics, and QA. These were not independent subagents or external participants. The pass is a structured heuristic and implementation-readiness review, not evidence that real analysts find the workflow usable.

The clickable prototype was evaluated in the local in-app browser against the synthetic Bingham Canyon story. It contains no Umbra imagery, backend data, persistence, remote permission, AI, or production React behavior.

## Core walkthrough result

| Step                         | Evidence                                                                                                                               | Result                                             |
| ---------------------------- | -------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------- |
| Orient to bundle and warning | Header exposes before/after dates, validated state, freshness, progress; persistent banner names the interpretation boundary           | Pass                                               |
| Select without map           | `C-001` queue button sets `aria-current`, selected geometry, evidence heading, and polite status                                       | Pass                                               |
| Compare time states          | Two-up desktop and explicit Before/After `aria-pressed` controls; compact layouts use one view                                         | Pass                                               |
| Inspect evidence             | Review, Provenance, Processing, and History tabs expose metrics, score limitation, license, IDs, parameters, commit, and artifacts     | Pass                                               |
| Record assessment            | No default choice; Save stays disabled until a decision; note and evidence context remain visible                                      | Pass                                               |
| Verify audit behavior        | Saved “Needs context” appears as a separate analyst event; candidate remains distinct; correction action is visible                    | Pass                                               |
| Required bundle states       | State selector verified loading, empty, invalid, degraded, partial, stale, and permission-placeholder title/action/status behavior     | Pass                                               |
| Save failure                 | Spec defines preserved draft, retry, cancel, alert association; prototype includes the error surface but does not simulate persistence | Spec pass; implementation test deferred to EAT-009 |

## Responsive and accessibility evidence

| Check                | Evidence                                                                                                            | Result                                                                         |
| -------------------- | ------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------ |
| Desktop              | 1440×1000 default, selected, and assessed states visually inspected                                                 | Pass                                                                           |
| Tablet               | 834×1112 selected state; comparison leads, queue/evidence follow; document width equals viewport width              | Pass                                                                           |
| Mobile               | 390×844 selected state; one-view comparison, 44px controls, read-only notice; document width equals viewport width  | Pass                                                                           |
| 200% zoom equivalent | 640 CSS-pixel viewport; one-column reflow, no horizontal page overflow, assessment action remains in document order | Pass                                                                           |
| Structure            | One `main`, one `h1`, no duplicate IDs, labeled dialog, three live/alert regions                                    | Pass                                                                           |
| Control names        | Zero unlabeled buttons and zero unlabeled input/select/textarea controls in the inspected selected state            | Pass                                                                           |
| Non-map selection    | Complete candidate button list with identity, area, pixels, score, and warning count                                | Pass                                                                           |
| Dialog focus         | Initial programmatic focus moves to the dialog heading; close behavior uses native dialog semantics                 | Pass in prototype                                                              |
| Reduced motion       | CSS removes meaningful transition/animation duration under `prefers-reduced-motion: reduce`                         | Pass by inspection                                                             |
| Contrast             | Core token pairings range from 6.98:1 to 16.91:1; focus on canvas is 15.87:1                                        | Pass for declared core pairs; implementation must retest every component state |

Keyboard control semantics were inspected through the accessible DOM and role-based activation. The browser automation surface did not yield a reliable raw Tab-sequence trace, so full keyboard-only traversal remains a required EAT-008 exploratory check rather than a claimed automated pass.

## Findings and resolutions

### Resolved in this artifact

| Severity | Finding                                                                             | Why it mattered                                                       | Resolution                                                                                            |
| -------- | ----------------------------------------------------------------------------------- | --------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------- |
| P1       | Interactive map controls were initially nested inside an ARIA `img` region          | Interactive descendants can be flattened or hidden by image semantics | Comparison is now a named `region`; vector texture remains presentational                             |
| P1       | The initial read-only breakpoint treated a 1280px desktop at 200% zoom like a phone | Assessment would disappear at required zoom                           | Read-only mobile is limited to widths below 480 CSS pixels; 640px reflow retains assessment           |
| P1       | Tablet header and toolbar content overflowed at 834px                               | Violated the no-horizontal-scroll requirement and hid actions         | Header, banner, comparison controls, and footer now wrap below 900px; measured width matches viewport |
| P1       | Invalid, stale, partial, and permission states retained a validated check icon      | Icon contradicted the visible state label                             | Each state now has matching icon, language, and semantic color treatment                              |
| P2       | Compact comparison initially displayed Before while Two-up remained selected        | Visible and announced state diverged                                  | Match-media synchronization selects Before on compact layouts and restores Two-up on desktop          |

### Open risks and follow-up

| Risk                                                                            | Owner/ticket                                   | Required evidence                                                                       |
| ------------------------------------------------------------------------------- | ---------------------------------------------- | --------------------------------------------------------------------------------------- |
| No external analyst participated in this pass                                   | Product research / EAT-008 validation          | 3–5 moderated first-use sessions using the core walkthrough                             |
| Synthetic texture cannot prove overlay legibility on real licensed SAR previews | Frontend and accessibility / EAT-008           | Screenshot regression and contrast/shape inspection using approved local derivatives    |
| Prototype state transitions are not durable backend behavior                    | Backend/frontend / EAT-008 and EAT-009         | Typed bundle state tests, idempotent assessment append, save-failure draft preservation |
| Tablist arrow-key behavior is specified but not implemented in the prototype    | Frontend / EAT-008                             | Adopt a complete tabs pattern and automated keyboard tests                              |
| Mobile review is intentionally read-only                                        | Product / post-MVP                             | Validate whether field users need assessment at phone widths before expanding scope     |
| Analytics are proposed and local-only                                           | Product/privacy / later instrumentation ticket | Event schema review and explicit privacy decision before collection                     |

## Design-team synthesis

- **Staff product design:** keep the single-workspace hierarchy and persistent interpretation warning; do not add a global navigation rail until more than one core route exists.
- **Product:** ship comparison and selection first, assessment second, full provenance third; activation is correct understanding and evidence inspection, not number of assessments.
- **Engineering:** derive one typed view model from validated bundle v1 and model degraded, partial, stale, and save-error states explicitly rather than as arbitrary strings.
- **UX writing and trust:** preserve “machine candidate,” “heuristic change score,” and “analyst assessment” as distinct labels; avoid confidence, detection, damage, and target language.
- **Accessibility:** keep queue selection fully equivalent to the map, retain explicit time toggles, use a named comparison region, and recheck real-component keyboard/focus behavior at every breakpoint.
- **QA:** use the state selector and viewport matrix as the minimum regression story, then replace prototype-only checks with React tests and browser screenshots in EAT-008/EAT-009.

## Approval gate

Carl explicitly approved the direction and implementation handoff in the EAT-DES-001 Codex task on 2026-08-24; the approval was recorded in Asana. The approved handoff covers:

1. the quiet analytical-instrument visual direction;
2. the three-region desktop workspace and compact reflow;
3. machine-candidate versus analyst-assessment separation;
4. phone-width read-only inspection;
5. implementation sequencing across EAT-008, EAT-009, and EAT-010.
