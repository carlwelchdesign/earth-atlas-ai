# EAT-DES-001 review prototype

This standalone prototype is design evidence for the EchoAtlas analyst workbench. It is intentionally separate from `apps/workbench` and does not load a real bundle, call the backend, persist assessments, contain Umbra pixels, or implement production behavior.

From the repository root:

```sh
uv run python -m http.server 4173 --directory prototypes/eat-des-001
```

Open `http://127.0.0.1:4173`, use the review-state selector to inspect required states, select candidate `C-001`, change comparison mode, inspect evidence tabs, and record a simulated assessment.

Synthetic textures are produced by inline SVG filters and simple vector shapes. They are illustrative UI material only.
