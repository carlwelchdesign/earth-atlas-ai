# Contributing

## Before coding

1. Read `AGENTS.md`, `plans/README.md`, and the active backlog ticket.
2. Confirm the ticket is unblocked in Asana.
3. Create one branch named `feature/<ticket>-<slug>` or `fix/<ticket>-<slug>`.
4. Add a start comment to the Asana ticket with scope and planned evidence.

## Local workflow

```sh
make setup
make check
```

Focused commands are available as `make format`, `make lint`, `make typecheck`, `make test`, `make build`, and `make secrets`.

## Pull requests

- Keep the diff within ticket scope.
- Include outcome, verification, risks, and screenshots or runtime evidence when relevant.
- Do not merge until CI passes and the acceptance checklist is satisfied.
- Record the commit, pull request, verification, and remaining risk in Asana.
- After merge, synchronize local `main` before starting the next ticket.

Never commit source imagery, caches, credentials, or secrets.
