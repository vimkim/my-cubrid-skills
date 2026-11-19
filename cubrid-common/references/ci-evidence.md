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

Use `cubrid-tcc` to find earlier failures of a validated testcase in retained `gha-ci` SQL, medium, or shell results. History pays off when the failure is old, such as an identical failure on other PRs or older Engines. It rarely helps for a testcase that the PR adds. If the command is unavailable or a query fails, record the limitation and continue the CI analysis. Record `cubrid-tcc --version`.

Each query takes about 1 second and prints a few hundred KB of JSON, most of it full occurrence records. Read it through the projection below, and reuse each result for the rest of the analysis.

### Select the testcase

Set `HISTORY_CASE` to the full testcase path, `HISTORY_RUN` to the run ID, and `HISTORY_SUITE` to the CI suite name (`test_sql`, `test_medium`, or `test_shell`). Chronicle accepts the CI names. For `test_sql_by_cci` it answers `UNSUPPORTED_SUITE` with the reason `suite_not_collected`; record that as unavailable history instead of querying `sql`, whose CSQL debug results are a different execution.

### Index the current run once

The current run is usually not indexed when the analysis starts. Before the first query, sync it once for each suite you will query:

```bash
cubrid-tcc sync-data --run "$HISTORY_RUN" --suite "$HISTORY_SUITE" \
    --revisit-limit 0 --json
```

A run sync takes 13 to 40 seconds. `--revisit-limit 0` keeps it to this run; the default also revisits up to 20 queued runs. Reuse the sync for every testcase of that run and suite.

Run syncs are the only refresh during an analysis. When `freshness.suggested_sync` or a tcr `sync_hint` names a date window (`--since` and `--until`), record the gap in one line and continue. A suggestion that names `--run` IDs is a run sync; run it once. A `--missing` suggestion drains runs that discovery listed but never imported, at about 10 seconds per run; it is maintenance for the user, so record it as a gap too. Window syncs outlast the agent's command time limit. If the run sync fails, for example with HTTP 502, record the failure and query what is indexed.

### Query history

```bash
cubrid-tcc history "$HISTORY_CASE" --suite "$HISTORY_SUITE" --json | jq '{history_result, reasons,
  target: (.target | {id, run_id, shard, outcome, engine_sha, testcase_sha, completed_at, pr: .pull_request.number}),
  occurrences: (.occurrences | map({id, run_id, shard, outcome, engine_sha, testcase_sha, completed_at, pr: .pull_request.number}))}'
```

With `--json`, every outcome is one JSON document on stdout. Exit `0` includes unknown and empty results. Exit `2` is an error with `error` and `message`. Exit `3` means the path matched several testcases; report `candidate_count` and the first `candidates`, and stop.

`history` anchors `target` to the latest indexed failure, which may differ from the current failure. Find the current failure in `occurrences` by `run_id` and `shard`, and compare its `engine_sha` and `testcase_sha` with the pinned revisions. Retained data has `attempt: null`, which means unresolved. A same-run occurrence is context and does not prove that it is the selected CI attempt.

Search across PRs and Engine revisions for recurrence. Add PR or Engine filters only for a deliberately narrower question. An earlier execution time does not prove Git ancestry; when ancestry matters, add `--ancestor-of <sha> --engine-repository <checkout>`, and keep ancestry unknown when local objects are missing.

### Interpret and retain history

- `SEEN_BEFORE` establishes an earlier failure of the same testcase identity. Before you claim the same symptom, compare the retained failure text. `cubrid-tcc evidence --execution <id> --json` lists the retained files under `files`, an object keyed by file name. `--file <name>` prints the hash-verified bytes.
- `FIRST_OBSERVED_IN_WINDOW` applies only to the reported window. It does not identify the introducing commit.
- `UNKNOWN_HISTORY` and an absent occurrence leave earlier failures unknown. Write one report line with `not_indexed_reason` and `suite_last_sync`, and end the history step for that testcase. `suite_failures_only` means the suite's evidence lists failures only, so a testcase that passed leaves no record; `never_observed` and `observed_outside_window` name the other cases.
- Shell evidence lists failures only, so Chronicle records no shell passes. Missing passes say nothing about stability.
- Suspected flakiness needs comparable PASS and FAIL/ERROR observations in different runs with the same `engine_sha` and `testcase_sha`. Mixed outcomes across revisions are insufficient.
- Recurrence and matching symptoms do not establish identical root causes, PR causality, or exemption from CI requirements.

Cite the CLI version, the query, the selected occurrence, earlier Engine and testcase SHAs, evidence execution IDs and digests, and the gaps you recorded. Keep query JSON and sync diagnostics separate from `cubrid-ci` bundles. Historical observations stay separate from the current inventory and the exact merge-base classifications.

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
