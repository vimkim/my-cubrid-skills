---
name: cubrid-ci-trigger
description: Trigger or rerun GitHub Actions gha-ci for a CUBRID pull request targeting develop or feature/**, choose a full, subset, or failure-only run, prevent same-PR cancellation, and verify pickup. Use when the user asks to run, trigger, or rerun CI on a supported CUBRID PR; release/11.x CircleCI operation is outside this skill.
---

# Operate CUBRID gha-ci on a PR

Start or rerun `gha-ci` against the pushed head of one CUBRID PR. This skill applies only when the PR base is `develop` or `feature/**`; stop and report an unsupported base instead of operating legacy CircleCI.

Read [references/gha-ci-operations.md](references/gha-ci-operations.md) before choosing a recovery method, diagnosing missing or failed checks, or explaining run behavior. A clean first run can follow the workflow below directly.

## Stable merge-gate contract

Treat these gha-ci commit-status contexts as the stable contract:

| Context | Merge requirement | Meaning |
|---|---|---|
| `gha-ci: build (release)` | required | release build |
| `gha-ci: build (debug)` | optional | debug build used by the suites |
| `gha-ci: test_shell` | required | shell suite |
| `gha-ci: test_sql` | required | SQL suite |
| `gha-ci: test_medium` | required | medium suite |

Discover the complete current merge gate with `gh pr checks "$PR_URL" --required`; do not encode a fixed total count. A gha-ci context may be absent before the first `/run`, so also compare the observed contexts with the stable four-context required set above.

## Select one operation

| Request or state | Operation |
|---|---|
| Full CI, unspecified suites, a new PR head, or pre-review qualification | `/run all` |
| User explicitly names a subset | `/run shell`, `/run sql`, `/run medium`, or their supported combination |
| Flaky testcase failure or a shard that died before running any case | `/run rerun <run-id>` |
| Transient build or runner job failure | `gh run rerun <run-id> --failed --repo CUBRID/cubrid` |
| PR head moved, or a shard died after handling only part of its assignment | `/run all` |

A clear request to run CI authorizes one `/run all`. A request naming an exact supported operation authorizes that operation. For a vague rerun request, inspect the evidence, recommend one operation, and obtain the user's choice. A known current-head run or any active run for the same PR requires explicit supersede authorization because another `/run` cancels it.

## 1. Resolve and validate the PR

Resolve a supplied URL or number against `CUBRID/cubrid`. Always pass `--repo CUBRID/cubrid` for a bare number so the current checkout cannot redirect it to another repository:

```bash
gh pr view <pr-url-or-number> --repo CUBRID/cubrid \
  --json url,number,state,baseRefName,headRefName,headRefOid
```

With no supplied PR, discover the current branch's PR only from a CUBRID checkout by running the same command without the positional argument. Require an open PR in `CUBRID/cubrid` whose base is `develop` or `feature/**`.

When the current checkout is the PR branch, compare `git rev-parse HEAD` with `headRefOid` and inspect `git status --porcelain`. Report unpublished commits and uncommitted changes because gha-ci tests only the pushed PR head. Trigger authorization does not authorize a commit or push.

## 2. Snapshot current-head activity

Capture all issue comments and both the complete and required check views before mutating anything:

```bash
gh api --paginate --slurp "repos/CUBRID/cubrid/issues/$PR_NUMBER/comments?per_page=100"
gh pr checks "$PR_URL" --json name,state,bucket,link,workflow
gh pr checks "$PR_URL" --required --json name,state,bucket,link,workflow
```

Preserve JSON even when `gh pr checks` exits `8`; pending or failing checks are valid observations. Follow gha-ci status links to their Actions runs and inspect their state. Treat a pending current-head gha-ci status, an active linked run, or a saved same-head trigger receipt as an existing run.

All `/run ...` commands for one PR share a cancellation group. When a run is active, stop with its URL and ask whether to supersede it. When a completed same-head run already supplies the requested contexts, report it and require explicit same-head retrigger authorization before starting more compute.

## 3. Validate a rerun source

For `/run rerun <run-id>` or `gh run rerun <run-id> --failed`, require a positive integer run ID and inspect it:

```bash
gh run view "$RUN_ID" --repo CUBRID/cubrid \
  --json databaseId,name,workflowName,event,status,conclusion,url,attempt
```

Require a completed `gha-ci` run associated with this PR. For `/run rerun`, prefer a run linked from the current head's gha-ci statuses; the workflow also enforces that its tested engine commit equals the current PR head. For GitHub failed-job reruns, require the source run to be linked from the current head's gha-ci statuses because a rerun of an older head cannot satisfy the current merge gate. Warn that the same run ID gains a new workflow attempt and its reported evidence changes.

## 4. Execute exactly once

Immediately before the mutation, re-read `headRefOid`, issue comments, and linked gha-ci status/run state. If the head changed, discard the prior selection and reassess the new head. If a new `/run` comment appeared or another run became active since the snapshot, abort this mutation and report that run; do not cancel it implicitly.

Post one bare chatops line for comment-triggered operations:

```bash
gh pr comment "$PR_URL" --body "/run all"
```

Use the selected body verbatim. Preserve an explicitly requested trailing `testtools=<branch>` value; never invent one. Save the returned comment URL, body, time, PR URL, and head SHA. If the response is lost, reconcile comments before retrying.

For an explicitly selected GitHub failed-job rerun, execute only:

```bash
gh run rerun "$RUN_ID" --failed --repo CUBRID/cubrid
```

Never combine the two mechanisms or start another `/run` while either is active.

## 5. Verify pickup and report

Re-read the PR head and poll checks for up to two minutes. For a new `/run`, require both build contexts and every selected suite context to point to one new gha-ci run; they should first become pending. For a GitHub failed-job rerun, require the same run ID to show a higher attempt or active rerun state. If pickup is still absent at the deadline, inspect the matching issue-comment workflow once, report the unresolved state, and preserve the original receipt; never post again to test pickup.

`gh pr checks` includes these commit statuses; the raw check-runs endpoint alone does not. Report:

- the exact operation and receipt or run URL;
- the tested PR head SHA;
- selected suites and observed gha-ci contexts;
- any still-missing stable required gha-ci context;
- the live `gh pr checks --required` result without replacing it with a hard-coded total.

Do not wait for terminal results unless the user asks. Use `cubrid-ci status` for a later status-only request and `cubrid-ci-analyze` for failure analysis.
