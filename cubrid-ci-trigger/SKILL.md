---
name: cubrid-ci-trigger
description: "Trigger CUBRID CI tests on a GitHub PR by posting a verified `/run` chatops comment — `/run sql medium` launches the SQL and medium suites, `/run all` launches sql, medium, and shell. Use for one-shot CI triggering on a new PR head with no active trigger, or before requesting review. For hands-off fix-until-green iteration use cubrid-loop-pr instead. Triggers on phrases like 'trigger ci', 'run ci on this pr', 'kick off ci tests', 'run sql medium', 'run all tests on the pr', 'rerun ci', 'post the /run comment', 'start ci for the pr'."
argument-hint: "[pr-url-or-number] [sql medium | all]"
---

# Trigger CUBRID CI on a PR

Post a `/run ...` comment on a CUBRID GitHub PR. The CI bot parses the comment body and launches the named CircleCI suites against the PR's **current head commit** — not your local working tree.

## Suite selection

| Comment body | Suites launched |
|---|---|
| `/run sql medium` | `ci/circleci: test_sql`, `ci/circleci: test_medium` |
| `/run all` | sql, medium, and shell suites |

These are the only verified, known-good forms. Post no other suite combination. In particular, `/run shell` was observed to instantly cancel a queued shell job on 2026-07-31 (PR #7588, job 142503), discarding its queue position.

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

- Local `HEAD` differs from `headRefOid` (unpushed commits) → CI would test stale code. Push, then re-read `headRefOid` before posting.
- Tree is dirty → never commit on the user's behalf; report that uncommitted changes won't be tested and let the user decide whether to commit first or trigger anyway.
- Skip this check entirely when the PR lives in a repo other than the current checkout.

## Step 3: Don't double-trigger

A duplicate `/run` comment can auto-cancel queued jobs from the previous pipeline, reset a 10+ hour shell queue position, and rerun suites that already finished. Before posting, inspect both existing comments and checks:

```bash
gh pr view <pr-url> --json headRefOid,createdAt,comments --jq \
  '{headRefOid, createdAt, runs: [.comments[] | select(.body | test("^/run ")) | {body, createdAt}]}'

gh pr checks <pr-url> --json name,state,bucket --jq \
  '.[] | select(.name | test("test_sql|test_medium|test_shell"; "i")) | {name, bucket}'
```

Determine whether each comment predates the current head push. Use the latest PR timeline `synchronize` event for `headRefOid` as the boundary; if there is no such event, use the PR's `createdAt`. If any `/run` comment exists at or after that boundary, treat the current-head trigger as **ACTIVE regardless of check visibility or state** and stop. A missing shell status means "possibly queued," never "not triggered." If the boundary cannot be established, fail closed and treat the trigger as active.

Conclude "not triggered" only when every existing `/run` comment predates the current head boundary, meaning a newer push invalidated those triggers. Never post a second `/run` for the same head for any reason, including "nothing visible yet," unless the user explicitly confirms the re-trigger in the current conversation.

## Step 4: Post the comment

```bash
gh pr comment <pr-url> --body "/run sql medium"
```

Keep the body to the bare `/run ...` line — that is the known-good format the bot parses. Post exactly one comment.

## Step 5: Verify pickup and report

Print what was posted, the PR, and the head SHA being tested:

```
Posted "/run sql medium" on PR #<number> (head <short-sha>).
```

Pickup expectations are suite-aware:

| Suite | Expected visibility and duration |
|---|---|
| `test_sql` / `test_medium` | Status usually appears within minutes; each job finishes in ≤1 hour. |
| `test_shell` | **No GitHub status exists while queued.** Queueing routinely takes 10+ hours; the job itself takes ≈1 hour after it starts. Absence of status is not evidence that the trigger was lost. |

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

Hand off depending on what the user wants next: `gh pr checks <pr-url> --watch` to wait inline, `/cubrid-loop-pr` for autonomous fix-until-green iteration, or `/cubrid-ci-analyze` once results come back red.
