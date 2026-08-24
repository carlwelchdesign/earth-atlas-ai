# Analysis-bundle contract fixtures

The fixture generator creates a self-contained 32-by-32-pixel Bingham Canyon demonstration story using deterministic synthetic data. No satellite measurement, Umbra pixel, person, vehicle, equipment, operational status, or confirmed physical change is represented. Generated source data and bundle content are marked `CC0-1.0`.

Generate a valid fixture:

```sh
uv run echoatlas-generate-demo-bundle \
  --output data/fixtures/eat007-valid \
  --case valid \
  --software-commit aaaaaaa
```

Validate it from the repository root:

```sh
uv run echoatlas-validate-bundle --bundle data/fixtures/eat007-valid
```

The generator refuses to overwrite an existing output directory and removes a newly created directory if generation fails. Outputs under `data/` are intentionally Git-ignored.

Supported cases:

| Case | Expected result | Purpose |
| --- | --- | --- |
| `valid` | accepted | complete, internally consistent v1 bundle |
| `stale-version` | rejected | unsupported version fails before dispatch |
| `missing-artifact` | rejected | required available artifact is absent |
| `partial-success` | accepted as degraded | optional overlay is explicitly missing with a warning |
| `malicious-path` | rejected | traversal path cannot leave the bundle root |

Tests also cover byte-for-byte reproduction, unexpected fields, tampered checksums, broken evidence references, JSON size limits, and symlink escapes.
