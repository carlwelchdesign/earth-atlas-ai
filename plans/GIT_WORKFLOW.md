# Git and ticket workflow

## Branches

- `main` is the integration branch.
- Use one `feature/<ticket>-<slug>` or `fix/<ticket>-<slug>` branch per Asana ticket.
- Do not mix unrelated planning, generated data, or another ticket's work into the branch.

## Ticket lifecycle

1. Confirm prerequisites and current repository/Asana state.
2. Add an Asana start comment with branch, scope, and planned evidence.
3. Implement ticket behavior and tests in reviewable increments.
4. Run focused checks and `make check`.
5. Review the diff for scope, secrets, generated files, and accidental complexity.
6. Commit with the `EAT-*` identifier, push, and open a meaningful pull request.
7. Wait for required checks, resolve failures, and merge only after acceptance is satisfied.
8. Add completion evidence and remaining risks to Asana, then mark the task complete.
9. Switch to `main`, pull the merged result, and verify a clean working tree before the next ticket.

## Completion evidence

- branch, commit SHA, and pull-request URL;
- focused and full check results;
- runtime, visual, data, or accessibility evidence appropriate to the change;
- migrations, screenshots, artifacts, or runbooks when required;
- unresolved risks and explicit gates that remain outside the ticket.

Local success, CI success, deployment, provider activation, Palantir enrollment, operational readiness, and public release are distinct states.
