# EAT-029 Nepal map comparison evidence

Verified locally on 2026-09-07 at 1440 × 900 using Chromium and the prepared
20 MB static Nepal asset package.

![Synchronized Sentinel-2 before and after maps](./images/eat-029-nepal-map-synced.png)

Observed browser evidence:

- the addressable `/investigate/nepal-flood-2026` route loaded a validated case;
- two MapLibre canvases rendered the fixed August 12 and August 27 XYZ sources;
- the north-up coverage boundary remained aligned across both panels;
- zooming the before map propagated the camera to the after map;
- switching to swipe retained two maps, exposed the keyboard-operable reveal
  slider, and reported that acquisition dates remain fixed;
- page content was non-empty and no Vite error overlay appeared;
- the static comparison remains available through the explicit no-WebGL path.

This verifies browser wiring and user-visible geographic behavior. It is not a
scientific validation of UNOSAT interpretation or Sentinel-2 absolute accuracy.
