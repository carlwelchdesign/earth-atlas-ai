# EAT-024 — Constrain Analyze workspace and scroll candidate queue

Status: complete

Asana: [EAT-024](https://app.asana.com/1/9789386902387/project/1217790716964797/task/1218039358769570)

Branch: `fix/eat-024-analyze-viewport-queue`

## Corrective finding

EAT-023 constrained the Explore acquisition results, but owner testing identified the remaining defect in Analyze. The 26-row candidate list owns the CSS Grid row height, which stretches the comparison and evidence panels and forces the document to scroll through a large empty workspace.

## Staff design decision

Keep the semantic ordered review queue and existing visual system. MUI/DataGrid is not warranted: a component library cannot repair the missing parent-height contract, and a data grid would weaken the ranked-list semantics while adding a large dependency. On wide desktop Analyze layouts, the application owns the viewport height; the candidate rows and long evidence content own their local overflow. Narrow layouts retain normal document flow to avoid nested-scroll traps at mobile widths or high zoom.

## Acceptance

- [x] At desktop Analyze widths and supported viewport heights, the document height does not grow with 26 candidate rows.
- [x] Queue title, count, filters, and sort rule remain visible while only candidate rows scroll.
- [x] The candidate list is a named keyboard-focusable scroll region with visible focus, contained overscroll, and a stable scrollbar gutter.
- [x] The comparison stage consumes available workspace height without stretching the grid; long evidence scrolls inside its panel.
- [x] Mobile/narrow layouts restore normal document flow and do not force an undersized nested queue scroller.
- [x] Selecting a row remains synchronized with the comparison and evidence panels.
- [x] Component regression coverage fails before the markup fix; Playwright verifies document height and scroll ownership with the 26-row public bundle.
- [x] `make check`, GitHub checks, and live public Vercel verification pass before Asana completion.

## Responsive boundary

- Wide desktop: viewport-owned application shell with independently scrolling work areas.
- Below 1200 CSS pixels or at short viewport heights: content-driven document layout and normal page scrolling.
- At 200% browser zoom, the reduced CSS viewport naturally uses the non-desktop layout.

## Non-goals

- Adding MUI, virtualization, or table semantics.
- Changing candidate ranking, assessment state, SAR processing, or scientific interpretation.
- Redesigning Explore.

## Local verification

- Component regression: 77 frontend tests passed, including keyboard scrolling for the named candidate queue region.
- Browser regression: at 1280 x 720, document height remained 720 px while the queue measured 208 px viewport / 1,789 px content; Page Down and wheel input moved the queue without moving the page.
- Responsive check: at 390 x 844, the layout returned to normal document flow with no horizontal overflow.
- Repository gate: `make check` passed with 114 backend tests, format, lint, type checks, build, and secret scanning.
- GitHub: [PR #57](https://github.com/carlwelchdesign/earth-atlas-ai/pull/57) merged after Backend, Workbench, and Vercel checks passed.
- Public release: Vercel deployment `dpl_AQCZDLTSN85m1EWTDRcT7GU3CreP` reached Ready, and the Analyze viewport/queue Playwright regression passed against [earth-atlas-ai.vercel.app](https://earth-atlas-ai.vercel.app).
