# Nepal guided investigation v1

Status: approved for implementation by Carl Welch on 2026-09-07

## Product promise

EchoAtlas opens on one prepared Nepal flood case. A reviewer can move through
geographically aligned before/after imagery, inspect immutable cited
observations, record a separate assessment, and export a deterministic brief
without logging in. The imagery dates stay fixed while the map moves.

The experience does not compute new observations, summarize with AI, imply
live satellite access, or hide unavailable coverage. Explore and the Bingham
Canyon analysis remain available as secondary tools.

## Navigation and information hierarchy

Primary routes are addressable:

- `/` — Nepal case overview and the primary **Start investigation** action.
- `/investigate/nepal-flood-2026` — guided Context → Compare → Review → Brief
  workspace with free map navigation.
- `/explore` — existing global catalog.
- `/analyze` — existing prepared SAR analysis.

The investigation shell gives most of its desktop width and height to imagery.
The compact header retains product identity, routes, civilian-use status, and
visible acquisition dates. A left rail presents the current guided step and a
right evidence panel appears only when an observation is selected.

## Core walkthrough

1. **Overview:** read the investigation question, event summary, sources, and
   material cloud limitation. Start the investigation.
2. **Context:** see the case extent and fixed acquisition dates. Open the
   quality summary when detail is needed.
3. **Compare:** pan or zoom either map; the paired camera follows. Switch to a
   draggable swipe or a single-date view without changing the camera.
4. **Review:** choose a source-reported observation on the map or accessible
   list. The map centers it and the evidence panel opens its citation and
   limitations. Record Supported by cited evidence, Not supported, or Needs
   context with optional notes. A correction appends a new event.
5. **Brief:** inspect unresolved items and download printable HTML or JSON.

The step controls never lock free navigation. Returning to an earlier step
preserves camera, selected observation, and the current draft.

## Desktop comparison

The default is two synchronized, north-up MapLibre maps. Rotation and pitch are
disabled. Both maps use the same fixed WGS 84 bounds, zoom limits, coverage
line, observation geometry, and selected-observation state. Camera propagation
uses an explicit guard so one map update cannot loop back into the other.

Comparison controls:

- **Side by side** — equal before/after panels with independent pointer entry
  and one shared camera.
- **Swipe** — two maps occupy the same frame; a range input clips the after
  map. The keyboard changes the divider in deterministic increments.
- **Before / After** — one map and one fixed-date layer.
- **Return to case extent** — restores the bounded AOI without resetting work.

Nodata stays transparent. The coverage boundary remains visible above imagery.
Panning beyond coverage exposes the neutral basemap and a visible “outside
prepared coverage” status. Missing tiles show the same status and the static
comparison fallback.

## Narrow screens and zoom

Below 760 px, one map is shown by default with a Before/After segmented control.
The selected date, camera, observation, and assessment draft survive layout
changes. The observation list follows the map. Evidence opens inline instead
of taking over the map. At 200% browser zoom the same single-map layout applies
without horizontal page scrolling.

## Observations and assessments

A source observation is immutable and always presents:

- publisher and title;
- direct source URL and evidence reference;
- source-reported wording;
- mapped geography;
- publication or access date;
- material limitations.

The assessment panel uses first-person reviewer language and sits under a clear
“Your assessment” heading. Source wording is never rewritten from the
assessment. Saving adds an append-only event. Recording a correction names the
event it supersedes and keeps both in history. Browser storage is namespaced by
case ID and version; if storage is unavailable, the current in-memory events
remain exportable and a status message explains that reload persistence is off.

## Brief

The Brief step contains the question, event and acquisition dates, selected
observations, latest assessment plus correction history, unresolved items,
citations, attribution, limitations, case version, and prepared before/after
thumbnails. User notes are escaped as text. The HTML has print styles and the
JSON uses a versioned export contract. Neither format calls a model or places
notes in the URL.

## Failure and recovery states

| State               | Visible behavior                                               | Recovery                                    |
| ------------------- | -------------------------------------------------------------- | ------------------------------------------- |
| Case loading        | Reserved map frame and validation status                       | completes or becomes rejected               |
| Invalid manifest    | No case imagery or observations render                         | retry; Explore and Analyze remain available |
| WebGL unavailable   | Static before/after comparison and accessible observation list | retry map after browser/device change       |
| Tile missing        | Basemap/transparent area plus prepared-coverage notice         | return to extent; static comparison remains |
| Outside coverage    | Coverage line and explicit location status                     | return to case extent                       |
| Storage unavailable | In-memory draft and export remain active                       | download brief before reload                |
| No assessment       | Observation remains clearly unresolved                         | assess or include as unresolved in brief    |

## Accessibility and acceptance

- Every map observation has a matching list button.
- The list and map share selection state; list selection moves the camera.
- Segmented controls expose pressed/current state and work by keyboard.
- Swipe exposes a labeled range input and never requires dragging.
- Status changes use a polite live region; errors use an alert.
- Focus returns to the observation control after closing evidence.
- Dates, layer identity, attribution, and the central cloud limitation stay
  visible without relying on color.
- Reduced motion disables animated camera changes.

Implementation acceptance includes desktop and narrow-screen browser evidence,
an automated accessibility scan, the existing Explore/Analyze regression suite,
and a permanent regression for duplicated warnings and geographic camera sync.
