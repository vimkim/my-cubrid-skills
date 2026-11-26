---
name: cubrid-common
description: Shared CUBRID workflow policy, user context, and helpers for worktrees, focused native testkit, PR metadata, build presets, remotes, and shared links. Use before interpreting issue assignments or recommending PR, CI, TC-only PR, or testcase integration actions, and when maintaining skills that depend on common checks. This is a shared dependency rather than a standalone workflow.
---

# CUBRID Common Helpers

This skill provides shared helpers and workflow references used by other skills in this collection.

## Workflow policy

Apply the user's current instructions and applicable repository policies before this collection's defaults. A helper's result supplies evidence, not permission to publish or merge.

On entering this workflow policy, establish the current user's identity once per task from explicit conversation or account context. If unavailable, inspect `gh api user --jq .login`. A shared or bot account leaves the user's identity unknown. Repository ownership, PR authorship, issue assignees, and filesystem usernames do not identify the user.

When the user is `vimkim`, read [vimkim's CUBRID context](references/cubrid-vimkim.md). For another or unknown user, continue with shared policy and that user's instructions without loading this profile.

Before recommending or performing PR, CI, TC-only PR, or testcase integration actions, read [Testcase lifecycle](references/testcase-lifecycle.md). Before reporting merge readiness, requesting merge permission, or merging a GitHub PR, apply the [PR approval gate](#pr-approval-gate). Write every squash commit message by the [Squash commit message convention](references/squash-message.md). Final engine PR merges (and their linked `tc/pr-<N>` PRs) run only through the user-invoked `/cubrid-pr-merge <PR>` skill (`pr-final-merge-handoff`): outside `/cubrid-pr-merge`, direct the user to run `/cubrid-pr-merge <PR>` once `pr-final-merge-handoff plan --pr <PR> --json` reports `data.review_ready: true` (no blockers other than squash messages, covering engine and changed TC PR reviews) rather than proposing manual close/merge steps or running `gh pr merge` directly.

### Dev2 team membership

Use `cubrid-dev2-members` to identify members of the [GitHub CUBRID/dev2 team](https://github.com/orgs/CUBRID/teams/dev2/members). The command is distributed by `my-cubrid` and refreshes its local cache after 30 days. Add `--json` for a JSON array or `--refresh` to fetch current membership. If the command is unavailable, run `gh api orgs/CUBRID/teams/dev2/members --paginate --jq '.[].login'`. Use the approval checker for merge decisions. It reads requested team membership live.

### PR approval gate

Apply this gate to each PR in `CUBRID/cubrid`, `CUBRID/cubrid-testcases`, and `CUBRID/cubrid-testcases-private-ex`. Run the checker immediately before reporting merge readiness, before asking for merge permission, and again immediately before each merge, including an already-authorized merge. Show its full output to the user at both points. Set `CUBRID_COMMON_DIR` to the directory containing this skill file.

```bash
"$CUBRID_COMMON_DIR/scripts/cubrid-pr-approval-check" --repo "$REPO" --pr "$PR_NUMBER"
```

The checker includes each user with a review request that has not since been explicitly removed, plus members of currently requested teams. It excludes the PR author, any repeatable `--exclude <LOGIN>` (case-insensitive), and bots. A PR with no enlisted reviewer is blocked. Each enlisted reviewer's latest non-`COMMENTED` GitHub review must be `APPROVED` and follow the latest active request. A direct request still pending blocks that reviewer. When `--head <SHA>` (40 hex) is passed, `APPROVED` also requires `commit_id == <SHA>`; stale approvals report `APPROVED (not at current head)` and block, and a moved live head exits `2`.

- Exit 0 satisfies the reviewer gate. Verify the other merge requirements and obtain any required merge permission.
- Exit 1 blocks the merge. Show each reviewer and their state. Proceed only if the user explicitly names every blocked reviewer and authorizes merging anyway. A general merge go-ahead does not waive the gate.
- Exit 2 means the checker could not establish the result. Resolve the evidence gap before treating the gate as passed or requesting merge permission.

Readiness reports count as merge decisions. Before calling an engine PR ready or suggesting `/cubrid-pr-merge <PR>`, run `pr-final-merge-handoff plan --pr <PR> --json` and require `data.review_ready` (`true`). Report every blocker other than the squash-message blockers (`data.message_blockers`). Every changed `tc/pr-<N>` PR (`changed_files > 0`) must be ready for review (not draft) and pass this gate with at least one `APPROVED` review at its current head from someone other than the engine PR author (`--head <TC_HEAD> --exclude <ENGINE_AUTHOR>`); waivers cannot replace that approval. Never call an engine PR ready from the engine PR's checker output alone.

Report final-handoff readiness or suggest `/cubrid-pr-merge <PR>` only for an engine PR that the current user both opened and is assigned to; the author merges anyone else's PR, and its TC PRs follow it. Outside `/cubrid-pr-merge`, do not request ad-hoc merge permission or run `gh pr merge` directly on a `CUBRID/cubrid` engine PR (TC-only CI-carrier PRs follow [testcase-lifecycle.md](references/testcase-lifecycle.md#tc-only-changes-ci-carrier-draft-engine-pr)). `pr-final-merge-handoff` enforces ownership with an `ownership` blocker that no waiver lifts.

Never use aggregate GitHub review or merge status (`reviewDecision`, `mergeStateStatus`, or mergeability) or approving language in a comment as evidence of an individual GitHub approval.

## Reusable helpers

Source `scripts/cubrid-common.sh` from sibling skills when a task needs reusable CUBRID preflight logic. Sourcing the shell helpers does not load the workflow policy.

```bash
common="<current-skill-dir>/../cubrid-common/scripts/cubrid-common.sh"
source "$common"
```

The calling skill chooses the intended test scope and interprets results. This helper owns reusable operations: git worktree detection, CUBRID source-tree detection, native testkit preflight/selection/configuration/result verification, CMake preset validation, PR metadata validation, canonical CUBRID remote detection, and known personal viewing URLs in shared material.

Before executing focused SQL, medium, or shell tests, read [Native testkit focused-run contract](references/testkit-focused.md). Use `scripts/testkit-focused.py` for its source/install identity gate, selection and attempt configuration, and artifact verdict.

For a focused replay of a CI failure, read [CI evidence and testcase identity](references/ci-evidence.md) to bind runtime evidence to the exact engine and testcase revisions before execution.

Before attributing or reporting a CI failure, read [Known CI issues](references/known-ci-issues.md). It checks each failure with `cubrid-tcr`, which holds known-issue rules and per-testcase history context.

For PR failure attribution or historical Engine CI lookup, read [Merge-base comparison](references/ci-baseline.md). It defines the shared collector, validation, comparison, and missing-baseline contract.

For earlier testcase failures, recurring symptoms, or suspected flakiness, read [Testcase history with Chronicle](references/ci-evidence.md#testcase-history-with-chronicle). It defines the one-run index refresh, the `cubrid-tcc history` query, and the limits of historical conclusions.

Before writing persistent reports, issue drafts, or planning sheets, read [Document Git workflow](references/document-git-workflow.md). It applies the user's Git workflow to each document repository and resolves artifact paths from the selected task checkout.

Before preparing or publishing material for other readers, read [Links in shared material](references/shared-links.md). Use `scripts/check-shared-links.py` for its known personal-host check; the calling skill owns the review and publication steps.
