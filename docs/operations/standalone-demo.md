# Standalone demo runbook

EchoAtlas has a prepared Nepal investigation plus two secondary local operating
modes. All keep the deterministic backend and workbench independent of Palantir,
ontology, and AI providers.

## Prepared Nepal investigation

Download the four exact source files from the
[Nepal dataset card](../data/nepal-flood-2026-dataset-card.md), then run:

```sh
uv run --group processing python scripts/prepare_nepal_case.py
uv run --group processing python scripts/verify_nepal_case.py
docker compose -f compose.yaml -f compose.prepared.yaml up --detach --wait
```

Open <http://127.0.0.1:8080>. The read-only overlay mounts both
`generated-nepal` and the secondary `generated-demo`. Verify that the root shows
the Nepal overview, `/investigate/nepal-flood-2026` loads imagery tiles as the
map moves, and `/analyze` retains the real-derived Umbra demonstration.

## Fast owner review: synthetic fallback

Requirements: Docker Desktop with Compose v2 and 4 GB of free working space.

```sh
docker compose build
docker compose up --detach --wait
```

Open <http://127.0.0.1:8080/analyze>. The backend health endpoint is available directly
at <http://127.0.0.1:8000/health> and through the workbench origin at
<http://127.0.0.1:8080/health>.

The fallback bundle is intentionally synthetic and labeled as such. It verifies
the interface and review workflow; it is not satellite evidence.

Stop the application without deleting the named data volume:

```sh
docker compose down --remove-orphans
```

## Secondary prepared public Umbra demonstration

First follow the acquisition, preview, candidate, and staging commands in the
repository README. They download the pinned public inputs into `data/` and stage
only validated display derivatives in
`apps/workbench/public/generated-demo/`. The source download is about 524 MB;
all source and generated files remain ignored by Git.

Then start the same images with a read-only prepared-data mount:

```sh
docker compose -f compose.yaml -f compose.prepared.yaml up --detach --wait
```

Open <http://127.0.0.1:8080>. Confirm that the mission header says
`Real satellite-derived demonstration`, both acquisitions identify Umbra, and
the queue reports 26 machine-generated candidates. These candidates are pending
human review and are not confirmed change or damage.

## Persistence and recovery

Assessment events are append-only and stored in browser local storage, scoped to
the exact bundle ID and browser origin. Reloading the page or restarting the
containers preserves them. A correction supersedes an earlier event; it never
deletes history. This is owner-review convenience storage, not a multi-user audit
database. Clearing site data removes it.

The backend's named `echoatlas-data` volume is explicit but current assessment
history does not use it. Never use `docker compose down --volumes` unless deleting
local application data is deliberate.

## Automated container check

```sh
make container-check
```

Set `ECHOATLAS_VERIFY_PREPARED=1` to test the prepared mount. The script validates
Compose, builds clean images, waits for health, checks API and web routes, prints
container state, and shuts down without deleting volumes.

## Native development

Native development remains the fastest edit loop:

```sh
make setup
make dev-api
make dev-web
```

Run `make check` before review. No OpenAI, Umbra, or MapTiler credential
is required for the default owner-review path. Place search uses the bounded
OpenStreetMap Nominatim fallback when no private MapTiler token is configured.

## Troubleshooting

- If port 8080 or 8000 is occupied, set `ECHOATLAS_WEB_PORT` or
  `ECHOATLAS_API_PORT` before Compose.
- If the prepared bundle falls back to synthetic, verify that `bundle.json` is
  present in the prepared directory and inspect the visible load notice.
- If the Nepal root rejects the case, prepare `generated-nepal` and use the
  prepared Compose overlay; raw and generated imagery are intentionally absent
  from Git and the default image.
- If stored assessment history is invalid or exceeds its bounds, the workbench
  shows a warning and leaves evidence inspection available.
- A healthy container proves startup, not scientific validity, public-release
  readiness, or availability of imagery everywhere on Earth.
