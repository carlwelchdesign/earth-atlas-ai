# EAT-027 — Nepal source gate

Status: **go with material cloud limitation**

The prepared case uses a bounded upper Bhote Koshi–Trishuli corridor in
Rasuwa, Nepal. The approved display extent is `85.3000,28.0800,85.4200,28.2800`
in WGS 84. This keeps the investigation focused on one navigable corridor and
inside the common footprint of the two verified Sentinel-2 acquisitions.

## Pinned acquisitions

| Role   | Earth Search item          | UTC acquisition               | Product                                                             | Grid                            | SHA-256                                                            |
| ------ | -------------------------- | ----------------------------- | ------------------------------------------------------------------- | ------------------------------- | ------------------------------------------------------------------ |
| Before | `S2C_45RUM_20260812_0_L2A` | `2026-08-12T05:10:48.070000Z` | `S2C_MSIL2A_20260812T045701_N0512_R119_T45RUM_20260812T100317.SAFE` | EPSG:32645, 10 m, 10980 × 10980 | `d87a9f98b759ff52ca6781ed1403828eaf5743fb662604e6b65d343cdfbb0ab0` |
| After  | `S2B_45RUM_20260827_0_L2A` | `2026-08-27T05:10:45.885000Z` | `S2B_MSIL2A_20260827T045659_N0512_R119_T45RUM_20260827T084453.SAFE` | EPSG:32645, 10 m, 10980 × 10980 | `7b98c0d9d0164be5f329073227dd2bd2966518b5c3bc9b1769e37dc903d21b8e` |

Both true-colour COGs have the same affine transform
`[10, 0, 300000, 0, -10, 3200040]`, CRS, dimensions, band count, data type,
and nodata value. Five distributed WGS 84 control coordinates are round-tripped
through the shared grid during preparation. The accepted display tolerance is
one source pixel (10 m); the measured grid residual is 0 m at all controls.
This establishes grid consistency for geographic comparison. It does not
measure the absolute orthorectification accuracy of either satellite product.

The after acquisition reports 78.471315% scene cloud cover. The bounded
corridor still contains usable visible sections, but cloud and shadow obscure
parts of the event area. The interface must retain transparent nodata, show the
coverage boundary, and disclose that obscured areas cannot support a visual
conclusion.

## Source-reported overlay

UNOSAT's preliminary flood, mudflow, and rockflow extent is used as a cited
reference overlay. It was derived from Sentinel-2 imagery acquired 27 August
2026 and PlanetScope imagery acquired 26 August 2026. UNOSAT states that the
result has not been field validated. EchoAtlas does not present this layer as
its own detection or as confirmed damage.

- Dataset DOI: `10.63253/1y26ihdq`
- Source CRS: EPSG:32645
- Source archive SHA-256:
  `867b5bebb4881d1b8f88af31df7f784f5db612fa651c911d81d7304bf5be0dda`
- Analysis-extent archive SHA-256:
  `7487b21cd2239cdb8c4913e31d3e08d1ce61462db032859bbfb853721e4424cb`

## Licensing and access

Copernicus Sentinel data are used under the Copernicus Sentinel Data Terms and
Conditions. Earth Search supplies public STAC metadata and Cloud Optimized
GeoTIFF access for the pinned products. The UNOSAT dataset page and DOI remain
the citation of record for the preliminary reference geometry. The access and
preparation commands are recorded in
[`docs/data/nepal-flood-2026-dataset-card.md`](../docs/data/nepal-flood-2026-dataset-card.md).

The published ESA comparison is discovery and narrative context only. Its JPEG
is not used as a georeferenced analytical layer.
