# EchoAtlas analyst workbench interface v1

Status: approved by Carl Welch for implementation on 2026-08-24 in EAT-DES-001.

Ticket: [EAT-DES-001](https://app.asana.com/1/9789386902387/project/1217790716964797/task/1217792507769764)

Prototype: [`prototypes/eat-des-001/index.html`](../../prototypes/eat-des-001/index.html)

## Product frame

### Target user and job

The primary user is a technically literate civilian imagery analyst or product reviewer evaluating a prepared SAR comparison. Their job is to understand the data quality, inspect machine-generated change candidates, review the evidence behind one candidate, and record a reversible assessment without mistaking a heuristic score for a finding.

Entry: a validated local analysis bundle is selected or finishes loading.

Exit: the analyst understands the bundle state and either records an assessment, requests more context, or leaves without changing the audit trail.

### Product outcome

A first-time reviewer can correctly explain what changed in the system state—not what changed in the world—select a candidate without relying on the map, trace its evidence, and record a reversible assessment.

Initial success measures:

- at least 90% of moderated participants distinguish “candidate” from “confirmed change” after one workflow;
- at least 90% find the highest-severity quality warning before assessment;
- median time from loaded bundle to opening candidate evidence is under two minutes;
- zero assessments are submitted without an explicit candidate and visible interpretation warning;
- 100% of tested tasks can be completed with keyboard only and at 200% zoom.

These are proposed validation targets, not current measured results.

### Automation level

M2 is manual review of deterministic candidates. AI is off. The UI does not generate conclusions, interpret raw pixels, or recommend an assessment. A later draft explanation must remain non-authoritative and evidence-linked, but it has no control or placeholder in this interface version.

### Non-goals

- production React implementation or backend integration;
- calibrated confidence, damage classification, identity, cause, intent, or operational status;
- account management, live subscriptions, alerts, collaboration, or publication;
- final marketing identity, public deployment, Palantir, or AI assistance.

## Design direction: quiet analytical instrument

The interface should feel like a rigorous review tool rather than a military command center. It uses dark neutral surfaces to support imagery inspection, restrained typography, fine structural rules, and high-salience state language. Saturated color is sparse and semantic.

- Teal means validated system state or an active neutral control.
- Amber means a machine-generated candidate or interpretation caution.
- Blue means analyst-authored “needs context.”
- Green and red appear only with explicit supported/rejected assessment labels; neither is used for raw change score.
- Map and imagery stay neutral so overlays remain legible.
- No crosshairs, threat language, radar sweeps, target icons, or urgency theater.

## Information architecture

One workspace route contains four persistent regions and one transient assessment surface:

1. **Mission header** — identity, timestamps, bundle health, freshness, review progress, and highest-severity warning.
2. **Candidate queue** — non-map entry to deterministic candidates, filters, stable sorting, status, area, score, and warnings.
3. **Temporal comparison** — synchronized before/after imagery, AOI/candidate overlay, time toggle, optional pointer reveal, legend, and view controls.
4. **Evidence inspector** — selected-candidate measurements, evidence artifacts, acquisition provenance, processing parameters, limitations, and assessment history.
5. **Assessment sheet** — deliberate supported/rejected/needs-context choice, optional note, consequences, and save/recovery state.

Navigation is workspace-local. The MVP has no global sidebar because there is one primary workflow. A compact product mark and “Open bundle” control may become global navigation when multiple bundles are implemented.

## Primary workflow

1. Load a validated bundle.
2. Read bundle status, freshness, candidate count, review progress, and the highest-severity quality warning.
3. Choose a candidate from the queue or map; both update the same selection state.
4. Compare before and after using the two-up view or accessible time toggle.
5. Inspect measurements, artifacts, provenance, score limitations, and assessment history.
6. Choose **Record assessment**.
7. Select **Supported**, **Rejected**, or **Needs context** and optionally add a note.
8. Review the explicit “analyst assessment” consequence and save.
9. See the append-only event in history; corrections use **Record correction** and supersede the prior event.

No step converts the machine candidate itself into a different object. The analyst adds a separate assessment event.

## Screen inventory

| Screen/state           | Purpose                                       | Primary action           |
| ---------------------- | --------------------------------------------- | ------------------------ |
| Workspace default      | Orient to the bundle before selection         | Select a candidate       |
| Candidate selected     | Compare imagery and inspect evidence          | Record assessment        |
| Assessment sheet       | Make a deliberate, attributable judgment      | Save assessment          |
| Assessment recorded    | Confirm append-only result and expose history | Record correction        |
| Loading                | Preserve layout while bundle validates        | Cancel or wait           |
| Empty bundle           | Explain no candidates or no pair              | Open another bundle      |
| Invalid bundle         | Fail closed with stage and safe details       | Choose another bundle    |
| Degraded               | Keep trustworthy evidence usable              | Inspect missing evidence |
| Partial success        | Separate completed and failed outputs         | Retry failed output      |
| Stale bundle           | Keep review possible with visible freshness   | Refresh or continue      |
| Disabled action        | Explain unmet prerequisite                    | Complete prerequisite    |
| Permission placeholder | Explain future capability boundary            | Return to local bundle   |

## Information hierarchy

Priority 1: bundle validity, quality limitations, freshness, and current selection.

Priority 2: before/after evidence, candidate geometry, measurements, score components, and provenance.

Priority 3: analyst assessment actions and audit history.

Priority 4: secondary processing parameters, checksums, and artifact metadata.

System validation, machine candidate, and analyst assessment never share the same badge component or color treatment.

## Low-fidelity wireframes

### Desktop, 1280 pixels and wider

```text
┌ Product ─ Mission/AOI ─ timestamps ─ bundle state ─ progress ─ Open bundle ┐
├ Highest-severity warning · interpretation boundary · Inspect details       ┤
├──────── Candidate queue ────────┬──────── Temporal comparison ─────┬──────── Evidence ────────┤
│ Filter  Sort                    │ Before / After / Reveal          │ Candidate 007             │
│ ○ C-001 pending        2 flags  │ ┌───────────┬───────────┐        │ Measurements              │
│ ● C-007 selected       1 flag   │ │ before    │ after     │        │ Evidence artifacts        │
│ ✓ C-012 supported               │ │           │ overlay   │        │ Limitations               │
│                                  │ └───────────┴───────────┘        │ Provenance                │
│ Review progress 4 / 26          │ legend · zoom · reset view      │ [Record assessment]       │
└──────────────────────────────────┴───────────────────────────────────┴───────────────────────────┘
```

The center comparison receives the most width. The queue is 18–22rem; the evidence inspector is 22–26rem. Either side panel may collapse, but its content remains available through labeled controls.

### Assessment sheet

```text
┌ Record analyst assessment ─ Candidate C-007 ─ close ┐
│ This records a separate append-only analyst event.   │
│ ( ) Supported  ( ) Rejected  ( ) Needs context      │
│ Notes (optional)                                     │
│ [                                                     ]│
│ Evidence referenced: before · after · score preview  │
│ [Cancel]                              [Save assessment]│
└───────────────────────────────────────────────────────┘
```

The sheet is a modal dialog on desktop and a full-screen dialog below 48rem. Focus is trapped only while open and returns to the invoking button on close.

### Tablet and compact desktop, 480–1279 pixels

```text
┌ Mission header + warning ┐
├ Comparison               ┤
├ Queue / Evidence tabs    ┤
└ Selected action bar      ┘
```

The comparison remains first. Queue and evidence become mutually exclusive tabs beneath it. The selected candidate and review action stay visible in a non-overlapping sticky footer.

### Mobile inspection, 320–479 pixels

```text
┌ Mission summary          ┐
├ State + warning          ┤
├ Before / After toggle    ┤
├ Single image viewport    ┤
├ Candidate list           ┤
├ Evidence accordions      ┤
└ Read-only notice         ┘
```

Mobile is an inspection path. New assessments are not offered below 480 CSS pixels in v1 because imagery comparison and judgment context cannot be kept simultaneously visible. Existing assessment history remains readable. This narrow breakpoint intentionally distinguishes common phone widths from a 1280-pixel desktop at 200% zoom: at the resulting 640 CSS pixels, controls reflow but assessment remains available in document order.

## High-fidelity desktop states

### Default

- Mission header shows “Bingham Canyon synthetic demonstration,” before/after timestamps, `Validated bundle`, freshness, `0 of 1 reviewed`, and the highest-severity interpretation warning.
- Candidate queue is visible with deterministic “Highest score, then ID” sorting.
- Comparison shows two synchronized neutral synthetic views with AOI boundary and legend.
- Evidence inspector shows an orientation prompt: “Select a candidate to inspect measurements and evidence.”
- Assessment is disabled with adjacent text explaining that a candidate must be selected.

### Candidate selected

- Queue row, map geometry, comparison caption, and evidence heading all repeat the candidate ID.
- Amber candidate geometry receives a two-pixel solid outline and a white inner keyline; selection adds corner handles without animation.
- Evidence opens to **Review**, showing status `Machine candidate · Pending`, area, pixels, score components, warnings, and evidence artifacts.
- The score label is “Heuristic change score,” never confidence or probability.
- **Record assessment** becomes available after candidate selection; evidence inspection is encouraged but not falsely recorded as completed.

### Assessment recorded

- A polite status announcement says: “Assessment saved. Candidate C-001 marked needs context.”
- The candidate remains a machine candidate; a separate blue analyst-assessment badge appears.
- Review progress updates.
- History shows timestamp, analyst identity, note, evidence references, and “Current event.”
- **Record correction** opens the same sheet with a notice that the new event will supersede the current assessment.

## Required state specifications

| State                  | Header                                                        | Workspace                                                                         | Action and recovery                                                          |
| ---------------------- | ------------------------------------------------------------- | --------------------------------------------------------------------------------- | ---------------------------------------------------------------------------- |
| Loading                | `Validating bundle` with progress text, not a fake percentage | Skeletons preserve all three desktop columns; no candidate values appear          | Cancel returns to bundle picker; live region announces stage changes         |
| Empty: no pair         | `No comparison loaded`                                        | Empty comparison illustration and plain explanation                               | **Open bundle** is primary                                                   |
| Empty: no candidates   | `Validated · 0 candidates`                                    | Before/after remains usable; queue explains that thresholding produced none       | Inspect run parameters or open another bundle                                |
| Invalid bundle         | `Bundle rejected`                                             | No artifacts render; show failed stage and safe diagnostic ID                     | Choose another bundle; copy details is secondary                             |
| Degraded               | `Validated with warnings`                                     | Valid artifacts remain; missing ones use labeled placeholders                     | **Inspect missing evidence** opens manifest details                          |
| Partial success        | `Partial output`                                              | Completed output listed separately from failed optional output                    | Retry only failed output; do not rerun completed work by default             |
| Stale                  | `Validated · stale`                                           | Review remains available, with captured-at and loaded-at dates                    | Refresh bundle or **Continue with stale data**; continuing is logged locally |
| Disabled               | Normal bundle state                                           | Disabled control remains focusable only when explanation is otherwise unreachable | Adjacent reason and linked prerequisite; no tooltip-only explanation         |
| Permission placeholder | `Remote capability unavailable`                               | Never reveal remote object names or metadata                                      | Return to local bundle; no sign-in dead end in M2                            |
| Save error             | Bundle and draft remain intact                                | Assessment sheet stays open with note and decision preserved                      | Retry or cancel; error is announced and associated with form                 |

`Degraded` means the bundle is structurally valid but has quality limitations. `Partial success` means a declared optional output failed. The labels are not interchangeable.

## Interaction annotations

### Comparison

- Default is two-up synchronized views.
- **Before** and **After** buttons provide the baseline single-view toggle and use `aria-pressed`.
- Pointer reveal is optional, never the only comparison method, and is disabled for reduced motion or coarse pointers.
- Pan/zoom applies to both views. The visible caption announces the extent change only after interaction settles.
- **Reset view** restores approved AOI extent and selected-candidate fit if a candidate is active.
- Overlay visibility is an explicit checkbox; selection persists when the overlay is hidden.

### Queue and map synchronization

- Selecting a queue row selects and fits the map geometry without moving keyboard focus.
- Selecting a map geometry updates the queue's `aria-current` row and evidence inspector; it does not auto-scroll until pointer interaction ends.
- `J`/`K` shortcuts may move through candidates only when focus is in the workspace and no text field/dialog is active. Arrow-key list navigation remains the documented baseline.
- Sorting is deterministic and its full rule is visible. Filtering never changes the underlying assessment state.

### Evidence

- Tabs: **Review**, **Provenance**, **Processing**, **History**.
- The Review tab contains decision-adjacent quality warnings and score limitations.
- Artifact links name the artifact, type, availability, and size. Missing artifacts are text, not broken thumbnails.
- Checksums are visually truncated but fully available to copy and to assistive technology.
- External source links include provider and open in a new tab only after explicit activation.

### Assessment

- No decision is preselected.
- Save stays disabled until a decision is selected; the reason is visible.
- Supported means the analyst judges that available evidence supports the candidate as a meaningful observable difference. It does not assert cause, damage, intent, or operational state.
- Rejected means evidence does not support retaining the candidate for this review.
- Needs context means evidence is insufficient or conflicting.
- Cancel preserves no draft after a confirmation only when a non-empty note or decision exists.
- Correction creates a new append-only event; it never edits or deletes history.

## Design tokens

Tokens are semantic and should map to CSS custom properties in EAT-008.

### Color

| Token         | Value     | Use                                                 |
| ------------- | --------- | --------------------------------------------------- |
| `canvas`      | `#070B10` | viewport background                                 |
| `surface-1`   | `#0D141C` | primary panels                                      |
| `surface-2`   | `#121C26` | raised controls and selected rows                   |
| `surface-3`   | `#192633` | hover and secondary emphasis                        |
| `rule`        | `#2A3947` | borders and dividers                                |
| `text-strong` | `#F2F5F7` | headings and key values                             |
| `text`        | `#C8D2DA` | body copy                                           |
| `text-muted`  | `#91A1AE` | secondary metadata; never essential text below 14px |
| `system`      | `#65D4C2` | validated state and active neutral control          |
| `candidate`   | `#F0B45A` | machine candidate and caution                       |
| `context`     | `#79A8FF` | needs-context analyst assessment                    |
| `supported`   | `#67C587` | supported analyst assessment only                   |
| `rejected`    | `#FF8585` | rejected analyst assessment and destructive error   |
| `focus`       | `#D6F36B` | universal focus ring                                |

Critical text uses tested pairings at or above WCAG 2.2 AA. `text-muted` is not used on `surface-3` for small text without verification. Status never relies on color alone.

### Typography

- UI sans: `Inter`, system fallback. Body 14/20; supporting 12/18; control 13/18.
- Display/data mono: `IBM Plex Mono`, `SFMono-Regular`, fallback. Candidate IDs, timestamps, measurements, and checksums only.
- Mission title: 18/24, weight 650. Panel title: 13/18, weight 650.
- No uppercase body copy. Uppercase 11/16 with 0.08em tracking is reserved for short region labels.
- Minimum interactive-label size is 13px; mobile body becomes 15/22.

### Spacing and geometry

- Base unit: 4px. Scale: 4, 8, 12, 16, 24, 32, 48.
- Minimum target: 44 by 44 CSS pixels on coarse pointers; 32 by 32 on precise pointers with 8px separation.
- Panel radius: 8px. Control radius: 6px. Badges use 999px only for compact status labels.
- Borders are 1px; selected candidate outline is 2px plus inner keyline.
- Shadow is reserved for dialogs and detached menus; panels use rules, not floating cards.

### Iconography and map styling

- Use a single 16/20/24px outline icon set with 1.75px stroke and visible text labels for primary actions.
- Candidate shapes use amber outline plus a numbered label and pattern-ready interior.
- AOI uses a dashed teal boundary labeled “Approved review boundary.”
- Basemap is low-saturation gray with labels at reduced contrast. No roads or points of interest beyond what the task requires.
- Before/after imagery uses the same display treatment and includes acquisition date in the viewport, not only in the header.

### Motion

- Default transitions: 120ms for control color, 180ms for panel reveal; no spring or ambient motion.
- Map fit is 250ms only when initiated by selection; never loop or pulse.
- `prefers-reduced-motion: reduce` removes smooth pan, panel slide, and opacity interpolation while preserving immediate state change.
- Loading uses a static skeleton under reduced motion.

## Component inventory

| Component            | Responsibility                                            | Required variants                               |
| -------------------- | --------------------------------------------------------- | ----------------------------------------------- |
| `MissionHeader`      | mission identity, timestamps, health, freshness, progress | validated, degraded, partial, stale, invalid    |
| `QualityBanner`      | highest-severity warning and recovery link                | caution, error, information                     |
| `CandidateQueue`     | filter, sort, non-map selection, progress                 | loading, empty, populated, filtered-empty       |
| `CandidateRow`       | candidate identity, status, metrics, warnings             | default, hover, focus, selected, reviewed       |
| `TemporalComparison` | synchronized evidence views and overlay                   | two-up, before, after, reveal, missing-artifact |
| `MapLegend`          | non-color explanation of AOI/candidate/assessment         | expanded, collapsed                             |
| `EvidenceInspector`  | review, provenance, processing, history                   | orientation, selected, missing, error           |
| `ArtifactRecord`     | artifact availability and inspection                      | available, missing, failed                      |
| `AssessmentBadge`    | analyst-authored status only                              | supported, rejected, needs-context, superseded  |
| `AssessmentDialog`   | deliberate append-only event creation                     | new, correction, saving, save-error             |
| `StateNotice`        | loading/empty/error/degraded recovery pattern             | named state variants                            |
| `StatusAnnouncement` | polite or assertive live-region messages                  | progress, success, error                        |

## Data, API, and permission dependencies

EAT-008 through EAT-010 need a view model derived only from validated bundle v1:

- bundle identity, status, created time, source/change run IDs, warnings, and artifact availability;
- AOI geometry and label;
- before/after acquisition identity, timestamps, provider, quality, source, and license;
- candidate ID, geometry, measurements, score components, evidence references, warnings, and pending status;
- append-only assessment events and supersession link;
- optional draft summary is ignored in M2.

The UI must receive an explicit stale calculation, not infer freshness from formatted strings. Permission state is a future typed placeholder. Assessment saving requires idempotent append semantics, preserved client draft on error, and an explicit returned event ID.

## Accessibility contract

### Landmarks and order

1. Skip link.
2. Product/mission header.
3. Highest-severity warning.
4. Candidate queue.
5. Temporal comparison.
6. Evidence inspector.
7. Assessment dialog when open.

Desktop visual placement may put comparison before the queue, but DOM order follows the sequence above so selection precedes detail. CSS grid places regions without changing reading order.

### Keyboard and focus

- Every action is reachable by Tab with visible `focus` ring, 2px solid plus 2px offset.
- Candidate rows use a single-select listbox or conventional button list; implementation must choose one semantic pattern and follow it completely. The recommended pattern is a list of buttons with `aria-current` because rows contain supporting text.
- Selection does not steal focus. Dialog open moves focus to its heading; close returns focus to the invoker.
- Escape closes menus/dialogs only after draft-loss confirmation rules are applied.
- Map controls follow DOM order and do not capture arrow keys unless their control has focus.

### Screen readers and non-map alternative

- The map is an image-like region labeled with AOI, active acquisition, visible candidate count, and selected candidate. It is not exposed as hundreds of unlabeled vector nodes.
- Candidate queue is the complete non-map selection and measurement alternative.
- Status changes use a polite live region. Bundle rejection and assessment-save failure use an assertive alert.
- Before/after buttons announce active state. Viewport captions name acquisition time and selected candidate.
- Charts or score graphics require text values and plain-language interpretation; no inaccessible canvas-only evidence.

### Zoom, contrast, and motion

- At 200% zoom on a 1280px-wide browser, layout becomes a one-column document with sticky behavior removed; all review actions remain reachable.
- No two-dimensional page scrolling. Imagery can pan inside its clearly labeled viewport.
- Text and UI component contrast meet WCAG 2.2 AA; focus indication meets 2.4.11 expectations.
- Reduced-motion behavior follows the token rules above. There is no essential timed interaction.

## Analytics and evaluation events

Telemetry remains local until a separate privacy decision. Proposed event names contain IDs/status categories, never raw notes, imagery, source URLs, or coordinates.

- `bundle_load_started`, `bundle_load_completed`, `bundle_load_failed`;
- `quality_warning_opened`;
- `candidate_selected` with source `queue` or `map`;
- `comparison_mode_changed`;
- `evidence_tab_opened`;
- `assessment_started`, `assessment_saved`, `assessment_save_failed`, `assessment_cancelled`;
- `assessment_correction_started`;
- `recovery_action_used`.

Measure task completion, time to evidence, warning discovery, queue/map selection parity, assessment save errors, and stale/degraded continuation. Do not optimize for assessment volume.

## Walkthrough validation protocol

Use the synthetic Bingham Canyon contract fixture and ask the participant to:

1. Explain the bundle's current state and one limitation.
2. Select candidate C-001 without using the map.
3. Compare before and after and explain what the score does not establish.
4. Find the source/license and processing commit.
5. Record **Needs context** with a note.
6. Find the new audit event and explain how they would correct it.
7. Repeat selection and evidence inspection with keyboard only.
8. Inspect the default, degraded, partial, stale, invalid, and save-error states.

Evidence checklist:

- desktop screenshots at 1440×1000 for default, selected, and recorded;
- tablet screenshot at 834×1112;
- mobile inspection screenshot at 390×844;
- 200% zoom or equivalent 640px CSS viewport screenshot with assessment action present;
- DOM/accessible-name inspection for landmarks, buttons, dialog, status, and alert;
- reduced-motion inspection;
- recorded defects with severity, resolution, or follow-up ticket.

## Implementation sequencing

1. EAT-008 implements mission header, quality banner, queue shell, temporal comparison, and bundle states using fixture data.
2. EAT-009 implements assessment dialog, append-only history, correction, draft preservation, and save recovery.
3. EAT-010 implements full evidence/provenance/processing inspection and attribution.
4. EAT-011 may add non-authoritative AI explanations only after deterministic evidence paths and evaluations exist.

The prototype is design evidence only. Production components must be rebuilt in the React workbench with tests rather than copied as an unreviewed parallel application.

## Approval gate

Carl approved this design direction and implementation handoff in EAT-DES-001 on 2026-08-24 after reviewing the prototype and walkthrough findings. EAT-008 may begin after PR #9 merges and local `main` is synchronized.
