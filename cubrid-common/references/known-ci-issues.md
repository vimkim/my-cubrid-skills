# Known CI issues

Temporary failures that are not caused by the PR under analysis. Each entry has an expiry date.

Before attributing a CI failure, check whether it matches an entry here. Then apply these rules:

- **Unexpired entry.** Label the failure "known issue, not caused by this PR" and cite the entry. Do not analyze its root cause or propose a fix for it. Still list it in the failure inventory, and still analyze any other failure in the same job.
- **Expired entry.** Do not apply it. Tell the user that the entry has expired and should be deleted or extended.
- **Entry with a tracking issue.** Before you apply it, run its **Check on match** steps and report their result with the failure. These steps decide whether the entry still applies.

Delete an entry when its issue is fixed. Extend an entry only with a new date and a reason.

## Entries

### `sql_by_cci` job fails on every branch

- **Expires:** 2026-12-09
- **Added:** 2026-11-09
- **Scope:** every gha-ci job whose name contains `sql_by_cci`, for example `shard sql_by_cci 01`. The job is new in gha-ci.
- **Status:** it also fails on `develop`. On `feature/oos-merge`, run 42763653366 after the 2026-11-10 develop sync had 0 failures unique to that branch (my-cubrid-docs `cbrd-oos-sql-by-cci/report.md`).
- **Not covered:** `test_sql` and other suites. A failure there is not this issue.

### `cbrd_27179` shell case: vacuum fixes a deallocated heap page

- **Expires:** 2026-12-11
- **Added:** 2026-11-11
- **Tracking issue:** [CBRD-28018](https://jira.cubrid.org/browse/CBRD-28018), owned by another team.
- **Scope:** debug `test_shell` failure of `shell/_37_elderberry/cbrd_23842_cdc/bug/cbrd_27179/cases/cbrd_27179.sh` whose core stack is `pgbuf_fix_debug` (`page_buffer.c`, deallocated-page assertion, `OLD_PAGE`) called from `vacuum_heap_page` with `was_interrupted=false`, under `vacuum_heap` and `vacuum_process_log_block`. The `vacuum.c` line differs by branch (1678 on `develop`, 1776 on `feature/oos-merge` at `cd24a21`).
- **Status:** intermittent, about 2% of runs. Seen on `develop` PRs #8469 and #8404, and on `feature/oos-merge` PR #8299 run 42868959374. Not OOS-specific.
- **Check on match:**
  1. Read the issue state: `curl -fsS --max-time 30 'https://jira.cubrid.org/rest/api/2/issue/CBRD-28018?fields=status,resolution,fixVersions'`.
  2. If it is not resolved, apply the entry as a known issue.
  3. If it is resolved, find its fix commits with `git log --oneline --grep='CBRD-28018' <develop>` and test each with `git merge-base --is-ancestor <fix> <tested engine commit>`.
  4. Fix absent from the tested commit: apply the entry, and tell the user the branch lacks the fix (for `feature/oos-merge`, a develop sync is needed).
  5. Fix present in the tested commit: do not apply the entry. Analyze the failure as new, and tell the user that CBRD-28018 may need to be reopened, citing the run and the core stack.
  6. If the issue cannot be read, apply the entry and report the issue state as unknown.
- **Not covered:** a different stack in this case, the same assertion in another testcase, and the RQG `dead_data_03_big_record` cores (a build without CBRD-27151, plus index-scan reader cores). Analyze those separately.
