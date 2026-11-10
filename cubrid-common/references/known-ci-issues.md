# Known CI issues

Temporary failures that are not caused by the PR under analysis. Each entry has an expiry date.

Before attributing a CI failure, check whether it matches an entry here. Then apply these rules:

- **Unexpired entry.** Label the failure "known issue, not caused by this PR" and cite the entry. Do not analyze its root cause or propose a fix for it. Still list it in the failure inventory, and still analyze any other failure in the same job.
- **Expired entry.** Do not apply it. Tell the user that the entry has expired and should be deleted or extended.

Delete an entry when its issue is fixed. Extend an entry only with a new date and a reason.

## Entries

### `sql_by_cci` job fails on every branch

- **Expires:** 2026-12-09
- **Added:** 2026-11-09
- **Scope:** every gha-ci job whose name contains `sql_by_cci`, for example `shard sql_by_cci 01`. The job is new in gha-ci.
- **Status:** it also fails on `develop`. On `feature/oos-merge`, run 42763653366 after the 2026-11-10 develop sync had 0 failures unique to that branch (my-cubrid-docs `cbrd-oos-sql-by-cci/report.md`).
- **Not covered:** `test_sql` and other suites. A failure there is not this issue.
