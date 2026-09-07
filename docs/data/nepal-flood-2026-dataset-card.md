# Nepal flood prepared-case dataset card

Access verified: 2026-09-07

## Purpose

This dataset supports one login-free, evidence-first investigation of the
26 August 2026 Nepal flash flood. It supports geographic before/after viewing,
inspection of cited observations, and human-authored assessments. It does not
support arbitrary-area processing, automated damage claims, or live imagery.

## Event and evidence sources

- [WHO Nepal emergency overview](https://www.who.int/nepal/emergencies/2026-rasuwa-flash-floods)
- [ESA event overview](https://www.esa.int/Applications/Observing_the_Earth/Copernicus/Sentinel-2/Nepal_flash_flood_imaged_by_satellites)
- [ESA Sentinel-2 comparison lead](https://www.esa.int/ESA_Multimedia/Images/2026/08/Sentinel-2_captures_before_and_after_Nepal_flash_flood)
- [UNOSAT preliminary extent and DOI](https://ihp-wins.unesco.org/dataset/nepal-satellite-detected-mudflow-and-rockflow-extent-nepal)
- [Copernicus Sentinel data terms](https://dataspace.copernicus.eu/terms-and-conditions)

## Reproducible source access

The preparation command reads only the exact local files below. Downloading is
kept separate so a failed or changed source cannot silently alter a case build.

```bash
mkdir -p data/raw/nepal-2026
curl --fail --location --output data/raw/nepal-2026/before-tci.tif \
  https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/45/R/UM/2026/8/S2C_45RUM_20260812_0_L2A/TCI.tif
curl --fail --location --output data/raw/nepal-2026/after-tci.tif \
  https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/45/R/UM/2026/8/S2B_45RUM_20260827_0_L2A/TCI.tif
curl --fail --location --output data/raw/nepal-2026/unosat-flood-extent.zip \
  https://ihp-wins.unesco.org/dataset/054c3516-e2b8-49a4-a256-1de4b7431ec6/resource/9f9498b2-4b48-4e83-8c8c-b227d5938a08/download/floodextent_20260826_nepal.zip
curl --fail --location --output data/raw/nepal-2026/unosat-analysis-extent.zip \
  https://ihp-wins.unesco.org/dataset/054c3516-e2b8-49a4-a256-1de4b7431ec6/resource/11195e74-c0cb-4c18-b2c4-190eea71059c/download/unosat_analysis_extent_20260826_20260827.zip
shasum -a 256 data/raw/nepal-2026/*
```

Earth Search item records:

- `https://earth-search.aws.element84.com/v1/collections/sentinel-2-l2a/items/S2C_45RUM_20260812_0_L2A`
- `https://earth-search.aws.element84.com/v1/collections/sentinel-2-l2a/items/S2B_45RUM_20260827_0_L2A`

## Verified quality facts

| Fact               |        Before |         After |
| ------------------ | ------------: | ------------: |
| Scene cloud cover  |    18.746611% |    78.471315% |
| Scene cloud shadow |     0.655973% |     0.469819% |
| Scene nodata       |     9.007575% |     8.594341% |
| CRS                |    EPSG:32645 |    EPSG:32645 |
| Pixel size         |          10 m |          10 m |
| Raster size        | 10980 × 10980 | 10980 × 10980 |

The common grid supports map alignment. Cloud cover in the after image is the
main limitation and remains visible in the product. Source imagery, extracted
archives, and generated map tiles are ignored by Git. The generated case
manifest records the source hashes and preparation parameters.
