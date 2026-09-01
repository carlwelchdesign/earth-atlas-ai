# Repository instructions

## Delivery

- Read `plans/README.md`, the active `EAT-*` ticket, and current Asana state before changing code.
- Use one dedicated feature branch per ticket. Keep commits and pull requests limited to that ticket.
- Update the Asana ticket at start, for material blockers or decisions, and at completion with verification evidence.
- Run `make check` before requesting review.
- Preserve unrelated local changes and never bypass a failing gate without documenting an approved decision.

## Product boundaries

- Treat detections as machine-generated **candidates**, never confirmed change, damage, identity, intent, or operational truth.
- Keep deterministic geospatial processing independent of UI, AI providers, and deployment vendors.
- Keep provider payloads behind adapters and validate all untrusted runtime data.
- AI may only explain structured evidence after the deterministic workflow and evaluation gates exist.
- Do not add military target tracking, person-level surveillance, autonomous actions, or public deployment without an explicit planning decision and owner approval.

## Data and security

- Never commit raw SAR imagery, local caches, provider credentials, secrets, or generated large artifacts.
- Preserve source identity, checksums, parameters, license, access date, and provenance for every data-derived artifact.
- Allowlist remote hosts and validate paths, types, dimensions, and size limits before downloads or archive extraction.
- Keep source-data licenses separate from the MIT software license.
