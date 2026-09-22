---
name: cubrid-common
description: Shared helper scripts for CUBRID skill preflight checks, PR metadata validation, CUBRID source-tree detection, build preset validation, and canonical CUBRID remote detection. Use when updating or debugging CUBRID skills that source common shell helpers; this is primarily an implementation dependency for other CUBRID skills.
---

# CUBRID Common Helpers

This skill provides shared shell helpers used by other CUBRID skills in this collection.

Do not invoke it as a user-facing workflow. Source `scripts/cubrid-common.sh` from sibling skills when a task needs reusable CUBRID preflight logic.

```bash
common="<current-skill-dir>/../cubrid-common/scripts/cubrid-common.sh"
source "$common"
```

Keep skill-specific policy in the calling skill. This helper owns reusable checks only: git worktree detection, CUBRID source-tree detection, CMake preset validation, PR metadata validation, and canonical CUBRID remote detection.

Before executing focused shell or SQL tests with CTP, read [CTP preflight](references/ctp-preflight.md) for shared JDBC/build preparation, child-process installation identity, and execution isolation. The specialized runner skills own configuration and result handling.

For a focused replay of a CI failure, read [CI evidence and testcase identity](references/ci-evidence.md) to bind runtime evidence to the exact engine and testcase revisions before execution.
