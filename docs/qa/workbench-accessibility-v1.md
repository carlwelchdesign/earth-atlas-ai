# EchoAtlas workbench accessibility and recovery verification

Status: EAT-011 verification complete for the local deterministic workbench.

Date: 2026-08-24

Scope: the React workbench using the synthetic Bingham Canyon demonstration bundle. This is implementation verification, not an external usability study or certification.

## Automated evidence

- The populated review workflow passes `axe-core` with no reported violations. The jsdom run excludes the color-contrast rule because it cannot calculate rendered styles reliably; contrast was checked separately from the rendered token pairs below.
- Component tests cover named landmarks and controls, queue and map selection parity, live selection and save announcements, evidence-tab keyboard behavior, dialog focus management, save recovery, stale acknowledgement, partial data, missing artifacts, permission denial, and compact-layout assessment availability.
- Bundle parsing rejects stale and permission-denied states that omit a human-readable reason.

## Manual interaction checklist

| Check | Evidence | Result |
| --- | --- | --- |
| Keyboard-equivalent candidate selection | Every map candidate has a matching queue button with candidate identity, measurements, score, and warning count. | Pass |
| Evidence tabs | Arrow keys move and select the adjacent tab; Home and End select the first and last tab; focus remains visible. | Pass |
| Visible focus | Browser inspection of the evidence tabs showed a solid 3px focus outline using the high-contrast focus token. | Pass |
| Assessment dialog | Opening moves focus into the dialog; focus is trapped; Escape closes a clean draft and returns focus to the invoking button. | Pass |
| Destructive close | Escape or Cancel on a changed draft opens a discard confirmation; `Continue editing` receives focus; Escape does not discard; explicit discard is required. | Pass |
| Landmarks and labels | The page exposes a skip link, named main workspace, named comparison region, labeled controls, one dialog title, and labeled tab panels. | Pass |
| Status announcements | Candidate selection, assessment save/error, stale acknowledgement, warnings, and invalid-bundle states use polite status or assertive alert semantics as appropriate. | Pass |
| Reduced motion | Meaningful transitions and animations are suppressed under `prefers-reduced-motion: reduce`. | Pass by stylesheet inspection |

This pass verified DOM semantics and live-region behavior but did not include a native VoiceOver or other screen-reader session. That remains a release-level manual check and must not be represented as complete assistive-technology certification.

## Responsive visual inspection

| CSS viewport | Layout | Assessment | Horizontal page overflow | Result |
| --- | --- | --- | --- | --- |
| 1280px | Three-region desktop; two-up comparison available | Available | None | Pass |
| 768px | Tablet reflow; comparison and review remain usable | Available | None | Pass |
| 640px | Single-column, one-up comparison; 200% desktop-zoom equivalent | Available | None | Pass |
| 390px | Phone-width read-only evidence workflow | Intentionally unavailable with explanation | None | Pass |
| 320px | Narrow phone-width read-only evidence workflow | Intentionally unavailable with explanation | None | Pass |

The below-480px restriction is intentional. At 480px and wider, including a 1280px display at 200% zoom, assessment remains available in document order.

## Contrast evidence

Rendered token pair calculations:

| Pair | Ratio | WCAG AA result |
| --- | ---: | --- |
| Primary text | 16.40:1 | Pass |
| Muted text | 7.60:1 | Pass |
| Accent text | 7.05:1 | Pass |
| Warning text | 8.01:1 | Pass |
| Danger text | 9.83:1 | Pass |
| Focus ring | 13.70:1 | Pass |

## Recovery-state matrix

| State | Verified behavior | Result |
| --- | --- | --- |
| Invalid bundle | Blocks the workbench, identifies validation failure, and exposes a functional retry action. | Pass |
| Save failure | Preserves the assessment draft, announces the error, and offers retry. | Pass |
| Partial bundle | Names unavailable optional output while retaining valid evidence. | Pass |
| Missing artifact | Names the missing required comparison artifact while retaining available evidence; no dead-end action is presented. | Pass |
| Stale bundle | Shows the evaluated timestamp and reason, requires an explicit session acknowledgement, and announces continuation. | Pass |
| Permission denied | Removes assessment mutation while retaining evidence inspection and a plain-language reason. | Pass |
| Dirty draft close | Requires an explicit destructive confirmation and defaults focus to the safe action. | Pass |

## Evidence boundary

- The checked imagery remains a deterministic synthetic fixture and contains no Umbra pixels.
- Actual licensed SAR-preview legibility is not established by this pass.
- No external analyst or assistive-technology user participated.
- Public deployment, authentication, provider permissions, container delivery, and release operations remain separate gates.
