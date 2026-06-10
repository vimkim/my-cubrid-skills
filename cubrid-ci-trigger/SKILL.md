---
name: cubrid-ci-trigger
description: "Trigger CUBRID CI tests on a GitHub PR by posting a `/run` chatops comment — `/run sql medium` launches the SQL and medium suites, `/run all` launches sql, medium, and shell. Use for one-shot CI triggering when working on a CUBRID PR: after pushing new commits, when checks never started, or before requesting review. For hands-off fix-until-green iteration use cubrid-loop-pr instead. Triggers on phrases like 'trigger ci', 'run ci on this pr', 'kick off ci tests', 'run sql medium', 'run all tests on the pr', 'rerun ci', 'post the /run comment', 'start ci for the pr'."
argument-hint: "[pr-url-or-number] [sql medium | all]"
---

# Trigger CUBRID CI on a PR

Post a `/run ...` comment on a CUBRID GitHub PR. The CI bot parses the comment body and launches the named CircleCI suites against the PR's **current head commit** — not your local working tree.

## Suite selection

| Comment body | Suites launched |
|---|---|
| `/run sql medium` | `ci/circleci: test_sql`, `ci/circleci: test_medium` |
| `/run all` | sql, medium, and shell suites |

These two bodies are the **verified, known-good forms** — both are in production use on CUBRID PRs. The grammar appears to be `/run` plus space-separated suite tokens, so combos like `/run shell` may work, but they are unverified: prefer mapping the user's request to one of the two known-good forms, and if you do post an unverified combo, watch pickup closely (Step 5) and fall back to a known-good form if the suites never start.

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

A duplicate `/run` comment wastes CI compute and confuses maintainers. Before posting, check whether the requested suites are already pending for this head:

```bash
gh pr checks <pr-url> --json name,state,bucket --jq \
  '.[] | select(.name | test("test_sql|test_medium|test_shell"; "i")) | {name, bucket}'
```

If a comment already contains the same `/run` line (check with `gh pr view <pr-url> --json comments --jq '.comments[] | select(.body | test("^/run ")) | {author: .author.login, body, createdAt}'`) **and** the matching suites show `bucket: pending`, report "already triggered, suites pending" and stop. Only re-post when the user explicitly asks to re-trigger.

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

After a minute or two the suites should appear as pending:

```bash
gh pr checks <pr-url> --json name,state,bucket --jq \
  '.[] | select(.name | test("test_"; "i")) | {name, bucket}'
```

Notes:

- `gh pr checks` is the right tool: CUBRID's suites are CircleCI **commit statuses**, which raw `gh api .../check-runs` silently omits.
- `gh pr checks` exits non-zero (code 8) while checks are pending — that is expected, the JSON output is still valid; don't chain it with `&&` or run it under `set -e`.
- Check names vary (`ci/circleci: test_sql`, `test_sql_long`) — match case-insensitive substrings, and report the full matched name.
- If the suites are still not visible ~20 minutes after the comment, the trigger likely wasn't picked up; re-post once and say so.

Hand off depending on what the user wants next: `gh pr checks <pr-url> --watch` to wait inline, `/cubrid-loop-pr` for autonomous fix-until-green iteration, or `/analyze-ci-failures` once results come back red.
