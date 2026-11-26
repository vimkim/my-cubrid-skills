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

General `cubrid-tcc` CLI syntax, filters, exit codes, and flakiness/evidence semantics live in the standalone `cubrid-tcc` skill (`cubrid-tc-chronicle/skills/cubrid-tcc/SKILL.md`). This section defines the `cubrid-ci-analyze` integration rules.

Use `cubrid-tcc` to find earlier failures of a validated testcase in retained `gha-ci` SQL, medium, or shell results. History pays off when the failure is old, such as an identical failure on other PRs or older Engines; it rarely helps for a testcase added by the PR. If `cubrid-tcc` is unavailable or fails, record the limitation and continue the CI analysis. Always record `cubrid-tcc --version`.

Each `history` query prints a few hundred KB of JSON. Project it with `jq` and reuse the result for the rest of the analysis.

### Select the testcase

Set `HISTORY_CASE` to the full testcase path, `HISTORY_RUN` to the run ID, and `HISTORY_SUITE` to the CI suite name (`test_sql`, `test_medium`, or `test_shell`). For `test_sql_by_cci`, `cubrid-tcc` returns `UNSUPPORTED_SUITE` (`suite_not_collected`); record history as unavailable instead of querying `sql`, whose CSQL debug results are a different execution.

### Index the current run once

The current run is usually not indexed when the analysis starts. Before the first query, sync it once per suite:

```bash
cubrid-tcc sync-data --run "$HISTORY_RUN" --suite "$HISTORY_SUITE" \
    --revisit-limit 0 --json
```

A run sync takes 13 to 40 seconds; `--revisit-limit 0` avoids revisiting queued runs. Reuse that sync for every testcase of the run and suite.

Run syncs are the only refresh during an analysis. When `freshness.suggested_sync` or a `cubrid-tcr` `sync_hint` names a date window (`--since`/`--until`) or `--missing`, record the gap in one line and continue instead of running it inline. If a run sync fails (for example HTTP 502), record the failure and query what is indexed.

### Query and interpret for the report

```bash
cubrid-tcc history "$HISTORY_CASE" --suite "$HISTORY_SUITE" --json | jq '{history_result, reasons,
  target: (.target | {id, run_id, shard, outcome, engine_sha, testcase_sha, completed_at, pr: .pull_request.number}),
  occurrences: (.occurrences | map({id, run_id, shard, outcome, engine_sha, testcase_sha, completed_at, pr: .pull_request.number}))}'
```

Match the current failure in `occurrences` by `run_id` and `shard` and verify its `engine_sha` and `testcase_sha` against the pinned revisions (note `attempt: null` in retained shared directories). When earlier failures matter for ancestry, pass `--ancestor-of <sha> --engine-repository <checkout>`. Before claiming matching symptoms, inspect retained bytes with `cubrid-tcc evidence --execution <id> --file <name>`.

In the `my-cubrid-docs` report, cite the CLI version, the query, the selected occurrence, earlier Engine and testcase SHAs, evidence execution IDs and digests, and all recorded gaps (`not_indexed_reason`, `suite_last_sync`, `UNKNOWN_HISTORY`). Keep Chronicle JSON and sync diagnostics separate from `cubrid-ci` bundles and exact merge-base classifications. Recurrence and matching symptoms do not establish identical root causes, PR causality, or exemption from CI requirements.

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
