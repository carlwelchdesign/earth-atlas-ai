# Data evidence

This directory stores small, reviewable metadata reports rather than source imagery or local indexes.

`umbra-catalog-smoke-2026-08-24.json` was generated from the public Umbra STAC catalog and S3 listing API on the recorded access timestamp. The run was deliberately bounded. `catalog_limit_reached` and `item_limit_reached` mean the counts describe sampled coverage, not the size of the full provider catalog.

`catalog-search-smoke-2026-08-25.json` records metadata-only EAT-017 searches over the approved Bingham Canyon AOI. The Sentinel-1 search uses the official Copernicus Data Space `sentinel-1-grd` STAC collection. The Umbra search deliberately starts at the June 2025 month catalog. Counts are access-time evidence, not promises of current coverage or scientifically suitable pairs.

The report preserves warning counts and a capped warning sample. Candidate AOIs are coarse metadata groupings for subsequent pair-selection work and are not verified change locations.
