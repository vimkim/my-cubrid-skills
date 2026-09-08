---
name: cubrid-ci-trigger
description: "Trigger CUBRID CI tests on a GitHub PR by posting a verified `/run` chatops comment — `/run sql medium` launches the SQL and medium suites, `/run all` launches sql, medium, and shell. Use for one-shot CI triggering on a new PR head with no active trigger, or before requesting review. Triggers on phrases like 'trigger ci', 'run ci on this pr', 'kick off ci tests', 'run sql medium', 'run all tests on the pr', 'rerun ci', 'post the /run comment', 'start ci for the pr'."
argument-hint: "[pr-url-or-number] [sql medium | all]"
---

# Trigger CUBRID CI on a PR

Post a `/run ...` comment on a CUBRID GitHub PR. The CI bot parses the comment body and launches the named CircleCI suites against the PR's **current head commit** — not your local working tree.

## Suite selection

| Comment body | Suites launched |
|---|---|
| `/run sql medium` | `ci/circleci: test_sql`, `ci/circleci: test_medium` |
| `/run all` | sql, medium, and shell suites |

These are the locally verified forms. Use them unless current bot documentation establishes another supported form. A `/run shell` comment coincided with a queued-job cancellation on PR #7588; that observation does not establish permanent bot behavior or causality.

When the user doesn't name suites, default to `/run sql medium`: shell is by far the slowest suite, so reserve `/run all` for when the user asks for it or the change touches shell-tested behavior.

## Step 1: Resolve the PR

If `$ARGUMENTS` contains a PR URL or number, use it; otherwise resolve from the current branch:

```bash
gh pr view <pr-url-or-number-if-given> --json url,number,state,headRefName,headRefOid
```

- No PR found → stop and report; this skill only acts on an existing PR (use `/cubrid-pr-create` first).
- `state` is not `OPEN` → stop and warn; triggering CI on a closed or merged PR wastes compute.
- A bare PR number resolves against the current checkout's repo — pass a full URL for a PR in any other repo.

## Step 2: Confirm the head commit is what you mean to test

CI runs against the pushed PR head. If the local checkout is the PR branch, compare:

```bash
git rev-parse HEAD          # local
git status --porcelain      # uncommitted changes
```

- Local `HEAD` differs from `headRefOid` → report which revision CI would test. Trigger authorization alone does not authorize a push. For a repair, follow cubrid-ci-fix's verified-diff push approval gate, then reread the remote head. If testing the already-pushed head was intended, proceed with that identified revision.
- Tree is dirty → never commit on the user's behalf; report that uncommitted changes won't be tested and let the user decide whether to commit first or trigger anyway.
- Skip this check entirely when the PR lives in a repo other than the current checkout.

## Step 3: Don't double-trigger

A duplicate trigger can cancel or supersede queued work. Inspect complete comment history and both checks and commit statuses before posting. Resolve REPO and PR_NUMBER from the validated PR identity:

```bash
gh api --paginate --slurp "repos/$REPO/issues/$PR_NUMBER/comments?per_page=100"
gh pr checks "$PR_URL" --json name,state,bucket,link
```

Capture nonzero `gh pr checks` status without discarding its JSON; pending or failing checks are not collection failures. Inspect exact-head CircleCI pipelines/workflows as needed.

Associate previous triggers using a saved head/comment receipt or trustworthy push/event evidence, plus job/pipeline revision checks. REST issue timelines do not expose a `synchronize` event: that is a webhook action. PR creation time and commit author/committer timestamps do not establish the current head's push time.

If a prior trigger is associated with the current head, do not post another without explicit same-head retrigger authorization. If association cannot be established, retain an unknown state and ask for that authorization rather than inventing a boundary. Missing shell status can mean queued work. A known current-head receipt remains relevant even when no check is visible.

## Step 4: Post the comment

```bash
gh pr comment <pr-url> --body "/run sql medium"
```

Require user authorization for posting, including authorization passed from an approved repair publication plan. Immediately recheck the PR head; if it changed, reassess the trigger against the new revision. Post one bare `/run ...` line and save the returned comment URL/ID, body, time and head SHA. If the response is lost, reconcile comments before retrying.

## Step 5: Verify pickup and report

Print what was posted, the PR, and the head SHA being tested:

```
Posted "/run sql medium" on PR #<number> (head <short-sha>).
```

Queue visibility and runtime vary. Absence of a status is not evidence that the trigger was lost; inspect the actual pipeline/job and record its state.

Check sql/medium pickup after a few minutes:

```bash
gh pr checks <pr-url> --json name,state,bucket --jq \
  '.[] | select(.name | test("test_"; "i")) | {name, bucket}'
```

Notes:

- `gh pr checks` is the right tool: CUBRID's suites are CircleCI **commit statuses**, which raw `gh api .../check-runs` silently omits.
- `gh pr checks` exits non-zero (code 8) while checks are pending — that is expected, the JSON output is still valid; don't chain it with `&&` or run it under `set -e`.
- Check names vary (`ci/circleci: test_sql`, `test_sql_long`) — match case-insensitive substrings, and report the full matched name.
- For shell, either wait or inspect the CircleCI pipeline list for the queued workflow. Never verify shell pickup by posting another comment.
- Never re-post without the user's explicit confirmation in the current conversation. A new pipeline can auto-cancel queued work, reset its queue position, and waste compute by rerunning completed suites.

Hand off depending on what the user wants next: `gh pr checks <pr-url> --watch` to wait inline, or `/cubrid-ci-analyze` once results come back red.
