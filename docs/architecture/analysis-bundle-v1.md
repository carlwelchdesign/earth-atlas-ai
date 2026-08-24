# Analysis bundle v1

## Boundary

The analysis bundle is the provider-neutral handoff between deterministic processing, the standalone workbench, tests, and optional future adapters. Version `1.0.0` uses JSON Schema Draft 2020-12 and is validated before any bundle content is trusted.

The root contains `manifest.json`, `aoi.geojson`, `acquisitions.json`, `candidates.geojson`, `assessments.json`, optional `summary.json`, and declared evidence artifacts. The manifest records every component and artifact by canonical relative path, SHA-256 checksum, and byte size.

The schema permits only declared fields. The runtime validator additionally enforces:

- exact supported version dispatch before component loading;
- JSON and artifact size bounds;
- canonical POSIX-relative paths with no traversal, URI, backslash, absolute path, or symlink escape;
- file existence, checksums, byte sizes, and PNG/PDF signatures where applicable;
- one before and one after acquisition with unique identifiers;
- consistent bundle and run linkage across documents;
- valid candidate, assessment, summary, and evidence references;
- append-order rules for superseded assessments;
- AOI geometry checksum and closed polygon rings; and
- internally consistent `succeeded` or `partial` state.

Required artifacts cannot be marked missing. A partial bundle is valid only when at least one optional artifact is declared missing and a warning explains the degraded state. Documents may reference only available artifacts.

## Trust and interpretation

Schema-valid means structurally and internally consistent; it does not mean scientifically validated, operationally current, or analyst-confirmed. Change candidates remain pending review items. An optional summary must set `authoritative` to `false`, identify its generator, cite bundle candidate and evidence identifiers, and carry a warning.

The checked-in generator emits only deterministic synthetic pixels and metadata under `CC0-1.0`. It does not redistribute the approved CC BY 4.0 Umbra imagery. Real derived artifacts retain the source attribution and sensitivity requirements recorded in the approved selection manifest.

## Compatibility policy

The validator currently supports exactly `1.0.0`. An unknown exact version is rejected before component schema dispatch; consumers must not guess compatibility.

- Corrections that do not change valid instances or their meaning may update documentation or validator diagnostics without changing the contract version.
- A future minor contract such as `1.1.0` may add optional capabilities, but it requires a separate schema directory and explicit validator support. A `1.0.0` consumer will continue to reject it fail-closed.
- A future major contract may rename, remove, reinterpret, or require fields and therefore requires an explicit migration.
- Published schemas are immutable. Changes that affect accepted instances create a new version rather than silently editing v1.

## Migration rules

Migration never mutates the source bundle in place. A migrator must write a new directory, assign a new bundle identity, preserve the source bundle identity and checksums in the target version's provenance model, recompute all component and artifact records, validate the completed target, and promote it atomically. Failed or partially written migrations are not valid bundles.

No automatic migration exists in v1. Until a versioned migrator is implemented and tested, the correct response to an unsupported bundle is to retain it unchanged and use a compatible reader.

## Fixture evidence

`echoatlas-generate-demo-bundle` produces bounded `valid`, `stale-version`, `missing-artifact`, `partial-success`, and `malicious-path` cases. `echoatlas-validate-bundle` validates any v1 directory. The fixture is generated rather than committed so checksum behavior and deterministic construction are continuously exercised without adding binary source data to Git.
