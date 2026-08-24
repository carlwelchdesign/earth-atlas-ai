# Third-party data and attribution

The MIT software license does not grant rights to third-party imagery, metadata, basemaps, event reports, or derived artifacts.

The first pinned data source is the Umbra Synthetic Aperture Radar Open Data Program under CC BY 4.0. The approved Bingham Canyon selection manifest records the provider, exact item and object identities, source URLs and keys, access date, sizes, ETags, and full-object CRC64NVME checksums. A successful local acquisition copies that manifest and a compact attribution record into the Git-ignored provenance workspace for offline use.

No raw or large source imagery belongs in Git. Event-context sources and basemaps require independent license and sensitivity review before publication.

The EAT-007 contract fixture generator creates only deterministic synthetic pixels and metadata, marked `CC0-1.0`; it does not copy or derive from Umbra imagery. Generating a valid synthetic fixture proves the portable file contract, not the licensing or release readiness of real derived imagery.
