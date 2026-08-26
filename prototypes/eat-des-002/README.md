# EAT-DES-002 Explore review prototype

This standalone prototype is design evidence for the post-MVP EchoAtlas Explore experience. It is intentionally separate from `apps/workbench`: it does not load MapLibre, call catalog providers, download imagery, persist a pair, or run analysis.

From the repository root:

```sh
uv run python -m http.server 4174 --directory prototypes/eat-des-002
```

Open `http://127.0.0.1:4174`. Use the prototype state selector to inspect truthful failure states, select results from the list, assign a before/after pair, edit the AOI, and inspect the retained-selection handoff to Analyze.

The map is a labeled synthetic vector surface. Footprints and acquisition records are fabricated interface fixtures, not provider coverage evidence.
