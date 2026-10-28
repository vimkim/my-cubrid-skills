---
name: cubrid-common
description: Shared helpers for CUBRID worktree, focused native testkit, PR metadata, build preset, remote checks, and links in shared material. Use when updating or debugging CUBRID skills that depend on common preflight, configuration, evidence verification, or publication checks; this is primarily an implementation dependency for other CUBRID skills.
---

# CUBRID Common Helpers

This skill provides shared helpers and workflow references used by other skills in this collection.

Do not invoke it as a user-facing workflow. Source `scripts/cubrid-common.sh` from sibling skills when a task needs reusable CUBRID preflight logic.

```bash
common="<current-skill-dir>/../cubrid-common/scripts/cubrid-common.sh"
source "$common"
```

Keep skill-specific policy in the calling skill. This helper owns reusable checks only: git worktree detection, CUBRID source-tree detection, native testkit preflight/configuration/result verification, CMake preset validation, PR metadata validation, canonical CUBRID remote detection, and known personal viewing URLs in shared material.

Before executing focused SQL, medium, or shell tests, read [Native testkit focused-run contract](references/testkit-focused.md). Use `scripts/testkit-focused.py` for its source/install identity gate, attempt configuration, and artifact verdict. The specialized runner skills own case selection and suite-specific interpretation.

For a focused replay of a CI failure, read [CI evidence and testcase identity](references/ci-evidence.md) to bind runtime evidence to the exact engine and testcase revisions before execution.

For PR failure attribution or historical Engine CI lookup, read [Merge-base comparison](references/ci-baseline.md). It defines the shared collector, validation, comparison, and missing-baseline contract.

For earlier testcase failures, recurring symptoms, or suspected flakiness, read [Testcase history with Chronicle](references/ci-evidence.md#testcase-history-with-chronicle). It defines `cubrid-tcc` lookup, bounded refresh, and the limits of historical conclusions.

Before writing persistent reports, issue drafts, or planning sheets, read [Document Git workflow](references/document-git-workflow.md). It applies the user's Git workflow to each document repository and resolves artifact paths from the selected task checkout.

Before preparing or publishing material for other readers, read [Links in shared material](references/shared-links.md). Use `scripts/check-shared-links.py` for its known personal-host check; the calling skill owns the review and publication steps.
