# Schemas

`analysis-bundle/v1` is the fail-closed JSON Schema Draft 2020-12 contract shared by processing, the standalone workbench, tests, and future adapters.

The schema set covers:

- the manifest, file inventory, provenance, licensing, status, and warnings;
- the approved area of interest and its geometry checksum;
- normalized before/after acquisitions;
- pending change candidates and their evidence references;
- append-only analyst assessments; and
- an optional, explicitly non-authoritative draft summary.

Runtime validation adds integrity and reference checks that JSON Schema alone cannot express. Consumers must use the runtime validator rather than treating schema validation as sufficient. Compatibility and migration policy are in [Analysis bundle v1](../docs/architecture/analysis-bundle-v1.md).
