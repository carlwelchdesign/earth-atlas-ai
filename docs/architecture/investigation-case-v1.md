# Investigation case contract 1.0.0

`InvestigationCase` is a separate runtime contract for prepared, evidence-first
investigations. It does not extend or reinterpret the SAR analysis-bundle
`1.0.0` contract.

The browser loads `/generated-nepal/case.json`, validates the complete record,
and renders nothing from a rejected manifest. Local assets must remain under
`/generated-nepal/` without traversal. External references must use HTTPS and
one of the explicit WHO, ESA, UNESCO IHP-WINS, Element 84 Earth Search,
Copernicus Data Space, or Sentinel COG hosts declared in the parser.

The contract contains:

- immutable case identity and version;
- event context and cited sources;
- WGS 84 AOI and prepared coverage geometry;
- ordered before and after acquisitions with exact source identities,
  timestamps, quality facts, checksums, local XYZ templates, and thumbnails;
- immutable source-reported observations with geometry, focus point, citation,
  evidence reference, and limitations;
- attribution, case-wide quality limits, five grid residual measurements, and
  the preparation command and source-manifest path.

User assessments are deliberately absent. They use the assessment event store
and are namespaced by case ID and case version. The boundary prevents a user
conclusion from becoming source evidence when the case is exported or reloaded.

## Preparation

Run after downloading and hashing the four pinned files documented in the
[dataset card](../data/nepal-flood-2026-dataset-card.md):

```bash
~/.local/bin/uv run --group processing python scripts/prepare_nepal_case.py
```

The command fails closed on a missing or changed source. It confirms the common
source grid, measures five grid-control residuals against the 10 m tolerance,
creates transparent Web Mercator PNG tiles for zooms 8–14, prepares before and
after thumbnails, extracts three bounded navigation geometries from the pinned
UNOSAT source, and writes the runtime case and checksum manifest.

Raw sources and generated assets remain outside Git. A local deployment must
prepare them before the Vite build. The browser does not download, process, or
search for satellite scenes.
