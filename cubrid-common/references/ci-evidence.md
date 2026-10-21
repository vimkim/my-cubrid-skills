# CI evidence and testcase identity

## Runtime collector and fallback

Prefer `cubrid-ci-analyze` and its `cubrid-ci` collector for runtime snapshots. Preserve exact Engine and testcase identity, schema/observation validation, raw-file digests, and acquisition states. Current suite summaries include failures and errors; a job-level failure without trustworthy testcase records has no testcase verdict.

For PR failure attribution, use [exact merge-base comparison](ci-baseline.md). The `cubrid-ci collect-base` and `collect-commit` commands own exact-commit baseline and historical Engine CI acquisition; status-only requests need no baseline. Use [Chronicle](#testcase-history-with-chronicle) for broader testcase failure history.

Separate read-only API evidence is allowed for unavailable or unsupported collector capabilities, incomplete acquisition, and miscellaneous GitHub checks. First use the supported CLI path; API evidence cannot upgrade an incomplete collector report or stand in for a validated baseline. Record missing CLI support as an unknown baseline in the analyzer. Record the reason and store an API bundle separately from collector schema output. An integrity mismatch must be resolved, never bypassed by silently trusting the same suspect evidence through another endpoint.

Resolve variables from validated PR metadata, not user-supplied shell fragments. Example GitHub GET collection after setting `PR_URL`, `REPO` (owner/repo), `PR_NUMBER`, `SOURCE_COMMIT` and a dedicated `EVIDENCE_DIR`:

```bash
gh pr view "$PR_URL" --json url,number,state,headRefOid,baseRefOid,headRefName,baseRefName > "$EVIDENCE_DIR/pr.json"
gh api --paginate --slurp "repos/$REPO/commits/$SOURCE_COMMIT/statuses?per_page=100" > "$EVIDENCE_DIR/status-pages.json"
gh api --paginate --slurp "repos/$REPO/commits/$SOURCE_COMMIT/check-runs?per_page=100&filter=all" > "$EVIDENCE_DIR/check-pages.json"
gh api --paginate --slurp "repos/$REPO/actions/runs?per_page=100" > "$EVIDENCE_DIR/action-run-pages.json"
```

Treat repository-wide Actions results as discovery candidates only; record search coverage. For exact Engine comparison, prove the tested revision from plan/build/shard evidence. Dispatch runs and reused builds are eligible; workflow `head_sha`, run titles, and PR linkage alone do not prove the tested Engine. Record run ID, run_attempt, head SHA, event, PR association, base/merge tree when applicable, timestamps and check app/context. A `pull_request` workflow can test a synthetic merge tree: preserve its relation to the pinned PR head, rather than requiring its tested tree to equal that head or merging evidence from unrelated heads.

For a validated Actions run/attempt:

```bash
gh api --paginate --slurp "repos/$REPO/actions/runs/$RUN_ID/attempts/$ATTEMPT/jobs?per_page=100" > "$EVIDENCE_DIR/action-job-pages.json"
gh run view "$RUN_ID" --repo "$REPO" --attempt "$ATTEMPT" --log-failed > "$EVIDENCE_DIR/action-failed.log"
```

Enumerate required checks using PR/check metadata and accessible branch/ruleset requirements; record missing permissions. Include discovered optional failures and prerequisite build failures. Select the latest relevant attempt per context while retaining older attempts as history. A successful old attempt cannot supersede a newer failure.

For a `release/11.x` PR or historical evidence whose pinned status actually targets CircleCI, derive the project and job number from that status target and verify them against job metadata before reading tests. Do not use CircleCI as a fallback for current `develop` or `feature/**` gha-ci evidence. The legacy collector uses GET `/api/v1.1/project/github/{owner}/{repo}/{job}`, plus `/tests` and `/artifacts`. Use an authenticated client with the token in its request header, never a query string or report. For v2, consult the actual response schema and validate the job → workflow → pipeline VCS revision relationship; follow `next_page_token` on paginated test/artifact/workflow endpoints. Save job identity, node and attempt alongside raw results. Verify repository, full VCS revision, job name and number; status labels alone do not establish identity.

Follow GitHub Link pagination. Check every request exit/status, use bounded backoff for transient/rate-limit responses and honor retry guidance. Record permanent authentication/access failures and truncation as incomplete coverage. Empty tests, missing artifacts and missing checks are not success. Keep only relevant bounded text artifacts by default; ask before downloading large cores/binaries unless already authorized. Do not POST reruns, cancels or comments during collection.

Primary API references when an endpoint or schema needs verification: [GitHub checks](https://docs.github.com/en/rest/checks/runs), [Actions jobs](https://docs.github.com/en/rest/actions/workflow-jobs), [Actions runs](https://docs.github.com/en/rest/actions/workflow-runs), and, only for the scoped legacy path above, [CircleCI API](https://circleci.com/docs/api/v2/index.html).

## Testcase history with Chronicle

Use `cubrid-tcc` to investigate earlier failures of a validated testcase in retained `gha-ci` SQL, medium, or shell results. Its queries read local evidence offline. If the command is unavailable or a query fails, record the limitation and continue the independently validated CI analysis. Record `cubrid-tcc --version` when available.

### Select the testcase and occurrence

Set `HISTORY_CASE` to the full testcase path and `HISTORY_RUN` to the run ID from the validated failure's suite. Map the suite to `HISTORY_SUITE`:

| CI suite | Chronicle suite |
|---|---|
| `test_sql` | `sql` |
| `test_medium` | `medium` |
| `test_shell` | `shell` |

```bash
cubrid-tcc status "$HISTORY_CASE" --suite "$HISTORY_SUITE" --json
cubrid-tcc explain --run "$HISTORY_RUN" --case "$HISTORY_CASE" \
    --suite "$HISTORY_SUITE" --json
```

Read `status`, `flakiness.assessment`, `freshness`, and coverage separately. `status` defaults to a recent window; use `history` or `explain` for older evidence. Exit `0` includes unknown, failing, and empty results. Exit `2` reports an operational error. For exit `3`, select a returned path/suite/variant candidate; use a returned `--execution` ID instead of `--run`, and `--ordinal` when needed to identify a repeated record. Execution IDs belong to the queried local index.

Match the selected occurrence to the pinned Engine SHA, testcase SHA, path, suite, variant, and available run/attempt/job identity. Shared result directories can leave attempt attribution unresolved: a same-run occurrence then supplies context, without proving it is the selected CI attempt. Preserve that uncertainty.

When the current occurrence is not indexed, inspect broader retained history with:

```bash
cubrid-tcc history "$HISTORY_CASE" --suite "$HISTORY_SUITE" --json
```

`history` anchors its summary to the latest ordered indexed failure, which may differ from the current failure. Label that target explicitly. Search across PRs and Engine revisions for recurrence; add current-PR or current-Engine filters only for a deliberately narrower question. An earlier execution time does not prove Git ancestry; use `--ancestor-of` with `--engine-repository` when ancestry matters, and retain unknown ancestry when local objects are missing.

### Refresh a bounded scope when needed

If relevant evidence is missing or stale and history would inform the analysis, group the needed coverage by run or window and choose one bounded refresh: selected runs, or an explicit UTC run-creation window covering the historical question. Set both window endpoints before using `--since` and `--until`. Select only relevant suites and use `--revisit-limit 0` so the refresh excludes unrelated queued runs. Retain the CLI's request-budget limit or lower it. Reuse the refreshed evidence across testcase queries.

```bash
cubrid-tcc sync-data --run "$HISTORY_RUN" --suite "$HISTORY_SUITE" \
    --revisit-limit 0 --json
```

Capture the exit and JSON, inspect `coverage --json` for the selected suite/window, then repeat the affected queries once. Report remaining gaps rather than polling or expanding the search until a match appears. A successful sync does not establish complete history. Stale discovery limits claims about recent or absent results; it does not erase an earlier retained failure.

### Interpret and retain history

`SEEN_BEFORE` establishes an earlier failure of the same testcase identity. Compare retained messages, diffs, or stacks before claiming the same failure signature. `FIRST_OBSERVED_IN_WINDOW` applies only to the reported complete window; it does not identify the introducing commit. `UNKNOWN_HISTORY`, absent records, and incomplete coverage leave prior occurrence unknown.

Report the CLI's flakiness assessment with its supporting context and limitations. Suspected flakiness needs independent comparable PASS and FAIL/ERROR observations; mixed outcomes on different Engine or testcase revisions alone are insufficient. Recurrence and matching signatures do not establish identical root causes, PR causality, or exemption from CI requirements.

Use `cubrid-tcc evidence --execution <id> --json` to list retained files, then `--file <returned-name>` to read hash-verified bytes. Keep query JSON and refresh diagnostics separate from `cubrid-ci` bundles. Cite the CLI version, query scope, selected occurrence, earlier Engine/testcase SHAs, ordering, source/evidence locators and digests, and freshness/coverage limitations, marking unavailable fields unknown. Historical observations remain separate from the current inventory and exact merge-base classifications.

## Map each TC to its repository

Use `CUBRID_TESTCASES_DIR` for SQL/medium, `CUBRID_TESTCASES_PRIVATE_EX_DIR` for shell. Record each root's Git identity and local changes. CI engine and testcase commits are independent. Current CI can select each testcase repository's own `tc/pr-N` branch or a fallback; inspect the actual tested configuration and checkout logs instead of assuming the branch name or revision.

For current suite-summary v2, use each matching shard's `testcases.sha` and `testcases.branch`, reconciled with the plan by the collector. Use the shard's `build.sha`, producing run and attempt for Engine provenance. Historical formats need their own schema-specific identity validation; never assume a first message SHA proves all shards.

Find the evidence-relative path using `rg --files` and confirm it is Git-tracked. When only a basename is available, enumerate matches and disambiguate using suite, message, configuration and source content. Reject path traversal and paths outside the intended repository. For a validated repository-relative `TC_PATH` and proven `TC_SHA`:

```bash
git -C "$TC_ROOT" ls-files --error-unmatch -- "$TC_PATH"
git -C "$TC_ROOT" cat-file -e "$TC_SHA:$TC_PATH"
git -C "$TC_ROOT" show "$TC_SHA:$TC_PATH"
git -C "$TC_ROOT" status --short -- "$TC_PATH"
```

Compare local content to exact evidence, including answers and fixtures; equal HEAD alone does not rule out dirty changes. If the revision differs, inspect Git objects or create an isolated worktree, preserving the user's checkout. Fetch only when necessary and authorized by the read-only investigation; do not reset, merge, pull or push test repositories as discovery. Unresolved revision identity limits attribution and must be settled before claiming faithful reproduction.
