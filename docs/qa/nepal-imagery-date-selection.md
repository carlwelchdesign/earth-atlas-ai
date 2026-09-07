# EAT-034 Nepal imagery date selection

Verified locally: 2026-09-07

## Product behavior

The Nepal investigation now loads a bounded Sentinel-2 acquisition list for
the prepared corridor and exposes editable Before and After selectors. Before
options precede the 26 August event; After options follow it. Selecting an
acquisition replaces the corresponding georeferenced MapLibre image source,
retains the camera, updates the visible acquisition label and quality summary,
and carries the exact selected pair into both brief formats.

The initial 12 and 27 August pair still uses the prepared static tile pyramid.
Other selections are rendered from the public Earth Search visual COG for the
same fixed AOI. Source observations and user assessments are unchanged.

## Quality finding

The public catalogue returned 21 acquisitions in the 27 July through 24
September case window at verification time. Available post-event full-tile
cloud values included 78.5% on 27 August and 69.5% on 3 September. Visual AOI
inspection showed that the 3 September image crosses the source swath edge and
is mostly nodata over the corridor. It is therefore available for inspection
but is not promoted as a clearer default. Full-tile cloud metadata remains
explicitly labeled and is never presented as an AOI-only measurement.

## Contract and safety verification

- Shared Umbra and Sentinel-1 catalogue requests reject ranges over 60 days.
- Explore prevents and validates an inclusive range over 60 calendar days
  before any provider request.
- The Nepal service accepts only the fixed AOI, fixed case window, Sentinel-2
  tile `45RUM`, Earth Search metadata host, and public Sentinel COG host.
- Dynamic imagery is georeferenced and rendered as a transparent Web Mercator
  overlay; comparison JPEGs are not used as analytical map inputs.
- Copernicus and Earth Search attribution stays visible for static and dynamic
  sources.

## Verification evidence

- `make check`: 120 backend tests and 103 frontend tests passed, with formatting,
  lint, strict type checks, production build, and secret scan.
- Local Playwright: editable-date investigation, assessment reload, and brief
  export passed against the Vite and API development servers.
- Desktop and 390 px captures show the selectors, status, attribution, selected
  dates, and responsive MapLibre comparison.

Artifacts:

- `evidence/eat-034/local-desktop.png`
- `evidence/eat-034/local-narrow.png`

Production deployment and public-alias evidence are recorded after release.
