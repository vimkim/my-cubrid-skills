# CI evidence and testcase identity

## Runtime collector and fallback

Prefer `cubrid-ci-analyze` and its `cubrid-ci` collector for runtime snapshots. Preserve its SHA/job validation, exit handling and sequential shared-manifest updates. The collector's normalized failure inventory covers `result=failure`; inspect raw tests for errors/unknowns and failed jobs with no test records.

Direct read-only API collection is allowed when the collector is unavailable, unsupported or incomplete, and for miscellaneous GitHub checks. Record the reason and store an API bundle separately from collector schema output. An integrity mismatch must be resolved, never bypassed by silently trusting the same suspect evidence through another endpoint.

Resolve variables from validated PR metadata, not user-supplied shell fragments. Example GitHub GET collection after setting `PR_URL`, `REPO` (owner/repo), `PR_NUMBER`, `SOURCE_COMMIT` and a dedicated `EVIDENCE_DIR`:

```bash
gh pr view "$PR_URL" --json url,number,state,headRefOid,baseRefOid,headRefName,baseRefName > "$EVIDENCE_DIR/pr.json"
gh api --paginate --slurp "repos/$REPO/commits/$SOURCE_COMMIT/statuses?per_page=100" > "$EVIDENCE_DIR/status-pages.json"
gh api --paginate --slurp "repos/$REPO/commits/$SOURCE_COMMIT/check-runs?per_page=100&filter=all" > "$EVIDENCE_DIR/check-pages.json"
gh api --paginate --slurp "repos/$REPO/actions/runs?event=pull_request&per_page=100" > "$EVIDENCE_DIR/action-run-pages.json"
```

Restrict Actions results to the requested PR and proven head linkage; do not accept all runs returned by the repository query. Record run ID, run_attempt, head SHA, event, PR association, base/merge tree when applicable, timestamps and check app/context. A `pull_request` workflow can test a synthetic merge tree: preserve its relation to the pinned PR head, rather than requiring its tested tree to equal that head or merging evidence from unrelated heads.

For a validated Actions run/attempt:

```bash
gh api --paginate --slurp "repos/$REPO/actions/runs/$RUN_ID/attempts/$ATTEMPT/jobs?per_page=100" > "$EVIDENCE_DIR/action-job-pages.json"
gh run view "$RUN_ID" --repo "$REPO" --attempt "$ATTEMPT" --log-failed > "$EVIDENCE_DIR/action-failed.log"
```

Enumerate required checks using PR/check metadata and accessible branch/ruleset requirements; record missing permissions. Include discovered optional failures and prerequisite build failures. Select the latest relevant attempt per context while retaining older attempts as history. A successful old attempt cannot supersede a newer failure.

For CircleCI fallback, derive the project and job number from the pinned GitHub status target and verify them against job metadata before reading tests. The legacy collector uses GET `/api/v1.1/project/github/{owner}/{repo}/{job}`, plus `/tests` and `/artifacts`. Use an authenticated client with the token in its request header, never a query string or report. For v2, consult the actual response schema and validate the job → workflow → pipeline VCS revision relationship; follow `next_page_token` on paginated test/artifact/workflow endpoints. Save job identity, node and attempt alongside raw results. Verify repository, full VCS revision, job name and number; status labels alone do not establish identity.

Follow GitHub Link pagination. Check every request exit/status, use bounded backoff for transient/rate-limit responses and honor retry guidance. Record permanent authentication/access failures and truncation as incomplete coverage. Empty tests, missing artifacts and missing checks are not success. Keep only relevant bounded text artifacts by default; ask before downloading large cores/binaries unless already authorized. Do not POST reruns, cancels or comments during collection.

Primary API references when an endpoint or schema needs verification: [GitHub checks](https://docs.github.com/en/rest/checks/runs), [Actions jobs](https://docs.github.com/en/rest/actions/workflow-jobs), [Actions runs](https://docs.github.com/en/rest/actions/workflow-runs), [CircleCI API](https://circleci.com/docs/api/v2/index.html).

## Map each TC to its repository

Use `CUBRID_TESTCASES_DIR` for SQL/medium, `CUBRID_TESTCASES_PRIVATE_EX_DIR` for shell. Record each root's Git identity and local changes. CI engine and testcase commits are independent. Current CI can select each testcase repository's own `tc/pr-N` branch or a fallback; inspect the actual tested configuration and checkout logs instead of assuming the branch name or revision.

The collector's `summary.json.testcase_revision` is a first matching message SHA, not proof that all tests used that revision. Prefer per-file `sources/index.json` owner/repo/revision/path records and actual CI checkout evidence. Flag contradictions or unproven revisions. Source downloads for abnormal non-failure results may need separate lookup.

Find the evidence-relative path using `rg --files` and confirm it is Git-tracked. When only a basename is available, enumerate matches and disambiguate using suite, message, configuration and source content. Reject path traversal and paths outside the intended repository. For a validated repository-relative `TC_PATH` and proven `TC_SHA`:

```bash
git -C "$TC_ROOT" ls-files --error-unmatch -- "$TC_PATH"
git -C "$TC_ROOT" cat-file -e "$TC_SHA:$TC_PATH"
git -C "$TC_ROOT" show "$TC_SHA:$TC_PATH"
git -C "$TC_ROOT" status --short -- "$TC_PATH"
```

Compare local content to exact evidence, including answers and fixtures; equal HEAD alone does not rule out dirty changes. If the revision differs, inspect Git objects or create an isolated worktree, preserving the user's checkout. Fetch only when necessary and authorized by the read-only investigation; do not reset, merge, pull or push test repositories as discovery. Unresolved revision identity limits attribution and must be settled before claiming faithful reproduction.
