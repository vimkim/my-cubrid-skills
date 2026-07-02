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
