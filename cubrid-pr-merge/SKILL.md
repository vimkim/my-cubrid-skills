---
name: cubrid-pr-merge
description: "Show the squash commit messages for a CUBRID engine PR and its tc/pr-N testcase PRs, then on confirmation merge the changed TC PRs, close the unchanged ones, refresh the TC gate, and merge the engine PR."
argument-hint: "<engine PR number>"
disable-model-invocation: true
---

# CUBRID PR Merge

Run the final merge handoff of one `CUBRID/cubrid` PR with squash commit messages that the user reads and confirms first. `pr-final-merge-handoff` performs every GitHub change; this skill writes the messages, shows the whole plan, and runs `execute` only after the user's confirmation in this session.

Take the engine PR number from `$ARGUMENTS`. If it is missing, ask for it.

## 1. Load the policy

Read [Workflow policy](../cubrid-common/SKILL.md#workflow-policy), [Testcase lifecycle](../cubrid-common/references/testcase-lifecycle.md#complete-one-final-merge-handoff), and [Squash commit message convention](../cubrid-common/references/squash-message.md). Require `pr-final-merge-handoff` with the `lint-message` subcommand (`pr-final-merge-handoff lint-message --help`). If it is missing, stop and tell the user to run `just sync` in `~/gh/my-cubrid-workflow/automations/pr-final-merge-handoff`.

## 2. Inspect the handoff

```bash
pr-final-merge-handoff plan --pr "$PR" --json
```

Read `data.steps`, `data.testcases`, `data.approvals`, `data.ci_evidence`, `data.review_threads`, and `data.blockers`. Two blocker kinds are handled here:

- `squash message required (--message KEY=FILE)` names one pull that the handoff merges and the `KEY` for its message. Step 3 writes it.
- `unresolved review thread(s)` means GitHub will refuse that merge (`All comments must be resolved`). Resolve this before any testcase PR changes, because the handoff merges the TC PRs first. For each entry in `data.review_threads`, show the user its PR, path, first author, URL, and whether the latest reply addresses it:

  ```bash
  gh api graphql -f query='query($id: ID!) { node(id: $id) { ... on PullRequestReviewThread { comments(last: 3) { nodes { author { login } body } } } } }' -f id="$THREAD_ID"
  ```

  Resolve only the threads that the user approves in this session, then run the plan again:

  ```bash
  gh api graphql -f query='mutation($id: ID!) { resolveReviewThread(input: {threadId: $id}) { thread { isResolved } } }' -f id="$THREAD_ID"
  ```

  A thread without an answer goes back to the user; the skill ends until it is addressed.

Every other blocker stops the skill: report it with the approval checker output and end. A reviewer waiver (`--waive-reviewer LOGIN`) is used only when the user names that reviewer in this session.

## 3. Write the messages

For each required `KEY`, write one message file (title line, blank line, body) in a new temporary directory, following the convention reference. Use the PR title, the PR body, `gh pr diff`, and the JIRA issue as sources:

| KEY | Pull |
|---|---|
| `engine` | `CUBRID/cubrid#<PR>` |
| `cubrid-testcases` | the changed TC PR in `CUBRID/cubrid-testcases` |
| `cubrid-testcases-private-ex` | the changed TC PR in `CUBRID/cubrid-testcases-private-ex` |

Check each file until it passes:

```bash
pr-final-merge-handoff lint-message "$FILE" --pr "$PULL_NUMBER" --ticket "$KEY_OF_ENGINE_PR"
```

## 4. Show the plan and ask once

Run the plan again with every message:

```bash
pr-final-merge-handoff plan --pr "$PR" --message engine="$ENGINE_FILE" --message cubrid-testcases="$TC_FILE"
```

Pass only the keys from step 2. Require `ready` with no blockers and an empty `review_threads`. Show the user, in this order:

1. The approval checker output for every PR.
2. Each squash message exactly as it will land, labeled with its repository and PR number.
3. The steps: each TC merge, each TC close (0 changed files), the `TC Merge Gate / Check TC PRs` rerun, and the engine merge.

Ask the user to confirm. When the user asks for a change, edit the file, run `lint-message` and the plan again, and show the changed message before asking again. The confirmation covers the messages and steps shown; a changed engine head, TC content, approval, or blocker needs a new plan and a new confirmation.

## 5. Execute

After the user confirms, run once:

```bash
pr-final-merge-handoff execute --pr "$PR" --yes --message engine="$ENGINE_FILE" --message cubrid-testcases="$TC_FILE"
```

Use the same `--message` and `--waive-reviewer` arguments as the confirmed plan. The tool reruns the approval checker before each change, merges with the confirmed title and body, waits for a passing gate rerun, and stops on any change since the plan.

## 6. Report

Report each journal entry (`merged` with its squash SHA, `closed`, gate `passed`) and confirm the engine PR state with `gh pr view "$PR" --repo CUBRID/cubrid --json state,mergeCommit`. On failure, report which TC changes already landed and the remaining blocker from the tool output; keep the remaining branches and run a new plan before any retry.

Then show the cleanup preview:

```bash
pr-final-merge-handoff cleanup --pr "$PR"
```

Apply it (`--apply`, `--jira-comment`, `--jira-to`) only when the user asks.
