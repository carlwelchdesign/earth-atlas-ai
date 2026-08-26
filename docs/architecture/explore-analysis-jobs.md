# Explore-to-Analyze selection and job contract

EAT-019 connects normalized catalog metadata to the existing analysis-bundle contract without moving provider, rendering, or scientific policy into the UI.

## Boundary

`POST /v1/analysis/selections` accepts an AOI plus normalized before/after catalog records. The backend rejects reversed timestamps, non-overlapping footprints, forged provider hosts, and invalid source metadata. It returns a frozen manifest containing:

- the exact normalized acquisition identities, timestamps, licenses, source URLs, and footprints;
- a canonical AOI geometry hash;
- deterministic overlap and metadata-comparability evidence;
- versioned processing inputs and interpretation limits; and
- a SHA-256 over the complete manifest content.

Comparability is descriptive evidence. `scientific_validity` is always `not_determined`; the contract cannot certify a pair or a change candidate.

## Bounded jobs

`POST /v1/analysis/jobs` queues an injected deterministic runner. `GET` reads state, `DELETE` requests cooperative cancellation, and `/retry` creates a new job linked to a failed or cancelled predecessor after verifying the original manifest hash. The in-memory coordinator keeps at most 32 records and exposes only `queued`, `running`, `succeeded`, `failed`, and `cancelled`.

The default `PreparedBundleRunner` reads only the explicitly configured `ECHOATLAS_PREPARED_BUNDLE_PATH`, caps the JSON at 10 MB, requires bundle contract `1.0.0`, and requires exact before/after acquisition IDs. It does not download imagery or silently substitute a fixture. An unconfigured or mismatched pair fails with a safe message.

## Frontend trust boundary

Explore validates every untrusted manifest and job response before retaining it. The first dialog action creates comparability evidence; a distinct second action starts preparation. A successful job is validated through the existing bundle parser before Analyze renders it. Returning to Explore does not mutate the loaded bundle or the immutable selection.

MapLibre remains a navigation renderer. Palantir remains an optional downstream adapter. AI remains outside selection, processing, job state, and bundle validation.

## Catalog integration correction

Umbra publishes a static hierarchy rather than a spatial Item Search API. For the default public catalog, the adapter now derives only the calendar-month roots intersecting the requested time window, distributes the existing total catalog/item budgets across those roots, and traverses at most four month roots concurrently. Custom fixture roots retain their exact configured behavior. This keeps metadata requests bounded while avoiding a whole-catalog walk for every Explore search; partial sampling remains explicit.
