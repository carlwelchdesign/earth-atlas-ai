# EAT-030 Nepal guided investigation evidence

Verified locally on 7 September 2026 with Chromium at 1280 × 900 and 390 × 844.

Observed browser evidence:

- `/` presents the prepared Nepal case and makes **Start investigation** the primary action.
- `/investigate/nepal-flood-2026` exposes the Context, Compare, Review, and Brief steps while leaving the map navigable.
- Selecting **Needs context**, entering a note, and recording the assessment changes the observation state without changing the source observation.
- Reloading restores the assessment and note from the case-and-version-specific browser key.
- The narrow layout uses one map, retains the fixed-date controls, and preserves the assessment draft.

Artifacts:

- `images/eat-030-nepal-overview.png`
- `images/eat-030-nepal-guided.png`
- `images/eat-030-nepal-narrow.png`

The automated browser's ref-based click did not activate an off-screen submit button. A DOM click exercised the same native button and confirmed the resulting local-storage record and reload behavior. Unit tests independently cover the button event, append-only correction, storage failure, and version isolation.
