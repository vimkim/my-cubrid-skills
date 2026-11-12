---
name: cubrid-common
description: Shared CUBRID workflow policy, user context, and helpers for worktrees, focused native testkit, PR metadata, build presets, remotes, and shared links. Use before interpreting issue assignments or recommending PR, CI, or testcase integration actions, and when maintaining skills that depend on common checks. This is a shared dependency rather than a standalone workflow.
---

# CUBRID Common Helpers

This skill provides shared helpers and workflow references used by other skills in this collection.

## Workflow policy

Apply the user's current instructions and applicable repository policies before this collection's defaults. A helper's result supplies evidence, not permission to publish or merge.

On entering this workflow policy, establish the current user's identity once per task from explicit conversation or account context. If unavailable, inspect `gh api user --jq .login`. A shared or bot account leaves the user's identity unknown. Repository ownership, PR authorship, issue assignees, and filesystem usernames do not identify the user.

When the user is `vimkim`, read [vimkim's CUBRID context](references/cubrid-vimkim.md). For another or unknown user, continue with shared policy and that user's instructions without loading this profile.

Before recommending or performing PR, CI, or testcase integration actions, read [Testcase lifecycle](references/testcase-lifecycle.md). It separates ongoing review and CI from the final TC and engine merge handoff.

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

For earlier testcase failures, recurring symptoms, or suspected flakiness, read [Testcase history with Chronicle](references/ci-evidence.md#testcase-history-with-chronicle). It defines `cubrid-tcc` lookup, bounded refresh, and the limits of historical conclusions.

Before writing persistent reports, issue drafts, or planning sheets, read [Document Git workflow](references/document-git-workflow.md). It applies the user's Git workflow to each document repository and resolves artifact paths from the selected task checkout.

Before preparing or publishing material for other readers, read [Links in shared material](references/shared-links.md). Use `scripts/check-shared-links.py` for its known personal-host check; the calling skill owns the review and publication steps.
