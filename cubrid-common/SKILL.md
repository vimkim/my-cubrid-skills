---
name: cubrid-common
description: Shared helpers for CUBRID worktree, focused native testkit, PR metadata, build preset, and remote checks. Use when updating or debugging CUBRID skills that depend on common preflight, configuration, or evidence verification; this is primarily an implementation dependency for other CUBRID skills.
---

# CUBRID Common Helpers

This skill provides shared shell helpers used by other CUBRID skills in this collection.

Do not invoke it as a user-facing workflow. Source `scripts/cubrid-common.sh` from sibling skills when a task needs reusable CUBRID preflight logic.

```bash
common="<current-skill-dir>/../cubrid-common/scripts/cubrid-common.sh"
source "$common"
```

Keep skill-specific policy in the calling skill. This helper owns reusable checks only: git worktree detection, CUBRID source-tree detection, native testkit preflight/configuration/result verification, CMake preset validation, PR metadata validation, and canonical CUBRID remote detection.

Before executing focused SQL, medium, or shell tests, read [Native testkit focused-run contract](references/testkit-focused.md). Use `scripts/testkit-focused.py` for its source/install identity gate, attempt configuration, and artifact verdict. The specialized runner skills own case selection and suite-specific interpretation.

For a focused replay of a CI failure, read [CI evidence and testcase identity](references/ci-evidence.md) to bind runtime evidence to the exact engine and testcase revisions before execution.
