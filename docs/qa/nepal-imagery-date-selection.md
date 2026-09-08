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
Other selections use release-prepared image overlays generated from the public
Earth Search visual COG for the same fixed AOI. Source observations and user
assessments are unchanged. Keeping raster preparation out of the request path
also avoids a native GDAL dependency in the public serverless function.

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

## Production evidence

The first deployment attempted request-time Rasterio rendering. Vercel built
the function but Python 3.13 could not import Rasterio because the runtime did
not provide `libexpat.so.1`; every API invocation failed before route handling.
The release was corrected by moving all raster work into the reproducible
preparation step and restoring the lightweight serverless dependency set.

Deployment `dpl_BEWvi5DktdnSofyLETTb7VozsGVb` is Ready and aliased to the public
site. The deployed API health check returned 200, the acquisition manifest
returned 21 records and `maximum_range_days: 60`, and the selected 3 September
asset returned a 720 × 960 RGBA PNG. A 61-day Umbra catalogue request returned
422 with the 60-day contract error. All four public Playwright workflows passed
in 8.1 seconds.

Release merge-back: [PR #73](https://github.com/carlwelchdesign/earth-atlas-ai/pull/73).
