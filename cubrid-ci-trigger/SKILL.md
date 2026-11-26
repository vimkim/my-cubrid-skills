---
name: cubrid-ci-trigger
description: Trigger, rerun, or wait on GitHub Actions gha-ci for a CUBRID pull request targeting develop or feature/**, prefer /run rerun <run-id> when an eligible same-head run suffices over full or suite runs, prevent same-PR cancellation, verify pickup, register with cubrid-ci-watch, and arrange event-driven monitoring or waiting. Use whenever posting /run, running CI after a PR push, rerunning CI, or waiting for a CUBRID PR CI run to finish; release/11.x CircleCI operation is outside this skill.
---

# Operate CUBRID gha-ci on a PR

Start or rerun `gha-ci` against the pushed head of one CUBRID PR. This skill applies only when the PR base is `develop` or `feature/**`; stop and report an unsupported base instead of operating legacy CircleCI.

Read [Workflow policy](../cubrid-common/SKILL.md#workflow-policy) before this workflow. It loads applicable user context and distinguishes ongoing CI from the final TC merge handoff.

Read [references/gha-ci-operations.md](references/gha-ci-operations.md) before choosing a recovery method, diagnosing missing or failed checks, or explaining run behavior. A clean first run can follow the workflow below directly.

## gha-ci status contract

Treat these gha-ci commit-status contexts as the stable contract:

| Context | Merge requirement | Meaning |
|---|---|---|
| `gha-ci: build (release)` | required | release build |
| `gha-ci: build (debug)` | optional | debug build used by the shell, SQL, and medium suites |
| `gha-ci: test_shell` | required | shell suite |
| `gha-ci: test_sql` | required | SQL suite |
| `gha-ci: test_medium` | required | medium suite |
| `gha-ci: test_sql_by_cci` | optional | SQL cases through CCI on the release build |

Discover the current required CI checks with `gh pr checks "$PR_URL" --required`. A gha-ci context may be absent before the first `/run`, so also compare the observed contexts with the stable four-context required set above. Use the [PR approval gate](../cubrid-common/SKILL.md#pr-approval-gate) for review readiness.

## Select one operation

**Check for an eligible same-head `/run rerun <run-id>` before choosing `/run all` or `/run <suite>`.** When the PR engine head SHA is unchanged, an eligible completed `gha-ci` run covers the needed suites, and no disqualifier applies, prefer `/run rerun <run-id>` over `/run all`, `/run shell`, `/run sql`, `/run medium`, or `/run sql_by_cci`: it reuses published builds, skips unchanged passing suites with 0 shards (carrying forward their `pass` status), and runs on 1 `cubrid-arc-light` shard per affected suite instead of claiming up to 71 `cubrid-arc` shards.

| Request or state | Operation |
|---|---|
| New/moved PR head, missing required suites, or pre-review full qualification with no eligible same-head source run | `/run all` |
| TC-only changes on the same engine head (`cases/` or `answers/` added, modified, renamed, or deleted in `tc/pr-<N>`, or `develop` merged into `tc/pr-<N>` **only** after Step 3 confirms engine-head parity and single-shard dir-unit sizing — even if the source run passed 100%) | `/run rerun <run-id>` |
| Verified flaky testcase failure (with history evidence), wholly dead shard (`found=no`, 0 handled), or chaining onto a prior `/run rerun` | `/run rerun <run-id>` |
| Transient `build (debug)` or `build (release)` failure | `gh run rerun <run-id> --failed --repo CUBRID/cubrid` (or `/run all` / `/run sql_by_cci` if `sql_by_cci` was left `nobuild` and needs 10 shards) |
| `develop` moved ahead of the engine PR head with engine changes paired to newly merged TCs, or merged `sql`/`medium`/`sql_by_cci` diffs exceed 1 light shard | Rebase engine PR onto `develop` (syncing `tc/pr-<N>`) + `/run all` |
| Any `/run rerun` disqualifier: engine commit moved, TC changes outside `cases/`/`answers/`, `develop` merged into `tc/pr-<N>` while engine head lacks paired engine changes, partial dead/timed-out shard (`rerun_short > 0`), `held` fault / provenance mismatch / `rerun_gone > 0`, changed build recipe, source run >30 days old / incomplete / `built by run` ID, new `testtools=<branch>` needing passing-case coverage, or oversized `sql`/`medium`/`sql_by_cci` rerun exceeding 1 light shard | `/run all` (or affected `/run <suite>`) |
| User explicitly needs a specific subset not covered by an eligible rerun source, or confirms full suite re-execution despite an eligible rerun | `/run shell`, `/run sql`, `/run medium`, `/run sql_by_cci`, or their supported combination |

Call an unchanged-testcase failure flaky only with history evidence: earlier failures of the same testcase on other PRs or Engine revisions, from the `history` counts of [Known CI issues](../cubrid-common/references/known-ci-issues.md) or `cubrid-tcc history`. Without that evidence, report the failure as unexplained and recommend analysis before a rerun. By contrast, TC fixes, additions, deletions, or renames in `tc/pr-<N>` (under `cases/` or `answers/`) and wholly dead shards (`found=no`) do **not** require flakiness history to use `/run rerun <run-id>`.

On a new PR head with no completed current-head run, a clear request to run CI authorizes one `/run all`. When a completed same-head run already exists, check `/run rerun <run-id>` eligibility first: for general or suite-named rerun requests (such as "CI 다시 돌려줘" or "TC 고쳤으니 sql/shell 돌려줘"), recommend `/run rerun <run-id>` when sufficient instead of `/run all` or `/run <suite>`. Even if the user asks for `/run all` or `/run <suite>` literally when `/run rerun <run-id>` suffices (and no disqualifier applies), briefly note that `/run rerun <run-id>` suffices and obtain confirmation before launching full compute; honor explicit confirmation if they still want a full run. A known current-head run or any active run for the same PR requires explicit supersede authorization because another `/run` cancels it.

When the loaded personal profile grants standing authorization for one bounded `/run rerun <run-id>` per `(PR, head_sha)`, execute that first rerun without asking only if zero prior `/run rerun` triggers exist on the current head, every red suite is explained by a `cubrid-tcr` `known` rule, verified flaky history, or a wholly dead shard (`found=no`) with no suspected PR defect or unexplained new failure, Step 3 finds no disqualifier, and no run is active on the PR. A second rerun on the same head, or any `/run all` or `/run <suite>`, still requires explicit user approval.

## 1. Resolve and validate the PR

Resolve a supplied URL or number against `CUBRID/cubrid`. Always pass `--repo CUBRID/cubrid` for a bare number so the current checkout cannot redirect it to another repository:

```bash
gh pr view <pr-url-or-number> --repo CUBRID/cubrid \
  --json url,number,state,baseRefName,headRefName,headRefOid
```

With no supplied PR, discover the current branch's PR only from a CUBRID checkout by running the same command without the positional argument. Require an open PR in `CUBRID/cubrid` whose base is `develop` or `feature/**`. If the user has only a standalone TC-repository PR or local TC-only changes targeting `develop` or `feature/**` with no `CUBRID/cubrid` PR yet, stop and direct them to the [TC-only CI-carrier draft engine PR](../cubrid-common/references/testcase-lifecycle.md#tc-only-changes-ci-carrier-draft-engine-pr) workflow so `TC Branch Sync` creates `tc/pr-<N>` for `gha-ci`.

When the current checkout is the PR branch, compare `git rev-parse HEAD` with `headRefOid` and inspect `git status --porcelain`. Report unpublished commits and uncommitted changes because gha-ci tests only the pushed PR head. Trigger authorization does not authorize a commit or push.

## 1a. Check the testcase baseline

A PR gha-ci run takes testcases from `tc/pr-<number>` in both testcase repositories and fails when either branch is missing. Those branches must contain the latest testcase baseline matching the engine PR's destination, including `develop` and `feature/<name>`. Run the check-only helper from `~/my-cubrid/bin`:

```bash
cubrid-pr-tc-base-check --pr "$PR_NUMBER"
```

Exit `0` means both branches contain the latest baseline. Exit `1` (stale, diverged, unrelated, or missing branch) or `2` (fetch or setup error) blocks the trigger: report the per-repository result and ask whether to trigger anyway. Under a user's standing one-time `/run rerun <run-id>` authorization on an unchanged engine head, a `stale` exit (`1`) may be bypassed without asking only if `origin/develop` moved after the source run started, the engine and TC PRs remain `MERGEABLE`, `tc/pr-<N>` still matches the engine PR's merge-base snapshot, and none of the failing testcase paths changed on upstream `develop` since `tc/pr-<N>`'s base; otherwise stop and ask. Do **not** merge `develop` into `tc/pr-<N>` alone and trigger `/run rerun` while the engine PR head lags behind `develop` without passing the Step 3 engine-head parity and dir-unit sizing gates; otherwise rebase the engine PR onto `develop` together with `tc/pr-<N>` and run `/run all`. Baseline ancestry does not prove CI success or readiness to finalize TC PRs. Trigger authorization does not authorize merging, rebasing, or pushing testcase branches.

A feature merge PR (base `develop`, head `feature/<name>` in `CUBRID/cubrid`) has the stricter rule: its `tc/pr-<number>` must have the same tip as `origin/feature/<name>` in both testcase repositories. Run instead:

```bash
cubrid-feature-tc-sync-check --check --pr "$PR_NUMBER" "$HEAD_REF_NAME"
```

Always pass `--check`; without it the helper prompts to push a fast-forward. Exit `0` means both repositories are synced. Any other exit blocks the trigger the same way: report the result, and if `tc/pr-<number>` is only behind, name `cubrid-feature-tc-sync-check-oos` (for `feature/oos-merge`) or `cubrid-feature-tc-sync-check` without `--check` as the user's sync step.

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

Require a completed `gha-ci` run associated with this PR.

For `/run rerun <run-id>`, verify all of the following before posting:

- **Valid completed `gha-ci` suite run**: `<run-id>` is a completed `gha-ci` run for this PR with `shard` or `status` jobs covering every needed suite — never a `built by run` ID, never a run still active/cancelled/dead before `collect` wrote `failed.list` (including a `debug` build failure where `plan` exited 1), and never missing a suite you need to add.
- **Same head, <30 days old, same build recipe**: the source run's tested engine commit equals current `headRefOid`, its internal `/home/ci/shared/runs/<id>` directory is not pruned (<30 days old and post-relayout/`tc_sha`), and `develop`'s build recipe (`image|args`) has not changed.
- **No unrecoverable `held` fault**: confirm the source summary/evidence has no `rerun_short > 0` (partial shard execution before timeout/death), no build or TC provenance `mixed`/`mismatch`, no unexplained `rerun_gone > 0`, no inherited `held`, and not a pre-`held` legacy failed run with 0 cases to rerun.
- **TC-only scope check**: if rerunning for TC-only updates in `tc/pr-<N>`, verify the changed paths are under `cases/` or `answers/`; shared helpers, scripts, configs, or data files outside `(cases|answers)/[^/]+$` are ignored by `/run rerun` and require `/run <suite>` or `/run all`.
- **`develop` merge into `tc/pr-<N>` parity and sizing gate**: when `develop` was merged into `tc/pr-<N>` since the source run's `tc_sha`, verify **both** conditions before choosing `/run rerun <run-id>`:
  1. **Engine-head parity**: check engine lag (`git rev-list --count "$HEAD_SHA..origin/develop"`) and inspect merged TC commits (`git log --oneline "$SOURCE_TC_SHA..HEAD"` in each testcase repo). If any newly merged TC pairs with an engine fix or feature commit on `origin/develop` absent from `headRefOid` (for example, merging `develop` into `tc/pr-8734` while the engine PR was 28 commits behind `develop` pulled 11 new shell TCs whose engine fixes were missing, causing `test_shell` failures), `/run rerun` is disqualified — rebase the engine PR onto `develop` (syncing `tc/pr-<N>`) and run `/run all`.
  2. **SQL/dir-unit single-shard sizing**: collect the distinct top-level `_...` directories under `sql/` (and `medium/`) from the union of source failures and `git diff --name-only "$SOURCE_TC_SHA..HEAD"` (`cases/`/`answers/`). Because `/run rerun` expands each changed or failed dir-unit case to its entire top-level `_...` directory on 1 `cubrid-arc-light` shard (120-min timeout, never scales out — unlike `shell`), verify the combined directory scope fits safely under 120 minutes (for example, a `develop` sync pulling multiple large top-level `sql/_*` dirs ran ~2h near timeout on 1 light shard); otherwise use `/run <suite>` / `/run all` (or rebase engine onto `develop` + `/run all`).
- **Single-shard capacity for dir-unit suites**: `sql`, `medium`, and `sql_by_cci` always run on 1 `cubrid-arc-light` shard (120-min timeout) and pull each failed or `tc_sha..HEAD` changed `cases/`/`answers/` case's entire top-level `_...` directory; count the distinct top-level `_...` directories from both source failures and `tc_sha..HEAD` diffs, and if the combined dir-unit load risks the 120-min limit (or `sql_by_cci` had `nobuild`), use `/run <suite>` or `/run all` instead.
- **`testtools=<branch>` provenance**: inspect `CTP provenance` or the suggested rerun command in the source summary and preserve any non-default `testtools=<branch>`. If a *new* `testtools=<branch>` must also retest previously passing cases, use `/run <suite> testtools=<branch>` or `/run all testtools=<branch>`.

For GitHub failed-job reruns (`gh run rerun <run-id> --failed`), require the source run to be linked from the current head's gha-ci statuses because a rerun of an older head cannot satisfy the current merge gate. Warn that the same run ID gains a new workflow attempt and its reported evidence changes.

## 4. Execute exactly once

Immediately before the mutation, re-read `headRefOid`, issue comments, and linked gha-ci status/run state. If the head changed, discard the prior selection and reassess the new head. If a new `/run` comment appeared or another run became active since the snapshot, abort this mutation and report that run; do not cancel it implicitly.

Post one bare chatops line for comment-triggered operations:

```bash
gh pr comment "$PR_URL" --body "/run all"
```

Use the selected body verbatim. Preserve an explicitly requested trailing `testtools=<branch>` value; never invent one. Save the returned comment URL, body, original trigger time, PR URL, and head SHA for CLI registration. If the response is lost, reconcile comments before retrying.

For an explicitly selected GitHub failed-job rerun, record its trigger time and intended next attempt before the mutation. Retain a stable operation receipt such as `github-rerun:<run-id>:<target-attempt>`. Then execute only:

```bash
gh run rerun "$RUN_ID" --failed --repo CUBRID/cubrid
```

Never combine the two mechanisms or start another `/run` while either is active.

## 5. Verify pickup and report

When the report names a failed job, check it with [Known CI issues](../cubrid-common/references/known-ci-issues.md) and apply the label for its verdict.

Re-read the PR head and poll checks for up to two minutes. For a new `/run`, require both build contexts and every selected suite context to point to one new gha-ci run; they should first become pending. For a GitHub failed-job rerun, require the same run ID to show a higher attempt or active rerun state. If pickup is still absent at the deadline, inspect the matching issue-comment workflow once and report pickup as unresolved. Preserve the original receipt for background monitoring even when no run has appeared. Never post again to test pickup.

`gh pr checks` includes these commit statuses; the raw check-runs endpoint alone does not. Report:

- the exact operation and receipt or run URL;
- the tested PR head SHA;
- selected suites and observed gha-ci contexts;
- any still-missing stable required gha-ci context;
- the live `gh pr checks --required` result without replacing it with a hard-coded total.

## 6. Arrange monitoring or wait for results

By default, register every triggered request with `cubrid-ci-watch`, including one whose pickup remains unresolved. Pass `--suite shell --suite sql --suite medium --suite sql_by_cci` for `/run all`, every suite present in the source run (including zero-shard carried-forward suites) for `/run rerun <run-id>`, or the explicitly selected suites for a subset, and include `--run-id` and `--attempt` once pickup is verified. On explicit user request to exclude optional suites (`sql_by_cci`), pass `--required-only` (or omit `--suite sql_by_cci`) at registration, or run `cubrid-ci-watch drop-suite "$REQUEST_ID" --suite sql_by_cci` on an already-active request. Record the `request_id`, receipt, head SHA, and last event ID in `work-tracker` when tracking long-running work. Honor an explicit user request to skip monitoring. Read [references/ci-monitoring.md](references/ci-monitoring.md) for the exact registration, polling, `wait`, and event commands.

Choose the post-trigger mode from the user's request:

- **Return the session (default)**: verify an existing shared poller (for example `cubrid-ci-watch.service` holding `poll.lock`, visible in `cubrid-ci-watch status`) or start one persistent `cubrid-ci-watch poll` process, verify whether an active out-of-session event consumer/delivery channel is running (for example `hermes-notify.service`, which routes Discord notifications on first `failure` and terminal `complete`/`deadline` with the Actions run URL and records terminal verdicts in `work-tracker` for standalone `cubrid-ci-watch` requests independently of `cubrid-pr-flow.service`), report registration, poller status, and delivery status, and return the session. For 1–24h CI runs, returning/closing the session is the standard path; a new session can inspect `cubrid-ci-watch status` or `show <id>` at any time. If persistent polling or event delivery is unavailable, retain the registration and report the missing part instead of claiming automatic monitoring or notification.
- **Wait in the current session (short in-session loops only)**: when the user explicitly asks to stay in the current session for a short run, launch `cubrid-ci-watch wait "$REQUEST_ID" --after "$LAST_EVENT_ID"` as one background shell task and yield the turn so the runtime wakes the session on the requested event class:
  - `--until required` whenever the condition is "all required checks pass/finish" or optional contexts (`sql_by_cci`, and `build (debug)` when optional) must not gate the wait;
  - `--until meaningful` (default) to wake on the first failure or any meaningful event;
  - `--until terminal` to wait until every registered suite finishes or the request closes.
  Always use `cubrid-ci-watch wait ... --until required` for required-only conditions; never hand-roll a `gh pr checks --required` or `gh run view` polling loop or `schedule` timer while `cubrid-ci-watch` is available. Fall back to a timer of at least 15 minutes only when `cubrid-ci-watch` is unavailable, and state why.

Use `cubrid-ci status` for a later status-only request and `cubrid-ci-analyze` for failure analysis, including its read-only exact merge-base comparison. Finding or lacking baseline evidence does not authorize another run or waive required CI contexts.
