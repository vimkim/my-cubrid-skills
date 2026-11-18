# Check for reusable CUBRID functions

## Before adding a function

1. Search the owning module, its headers, and related modules for functions that perform the intended operation. Search by operation, parameter type, or a function the new code would call. Use `clangd` symbol and reference search when available. Use `rg` for text searches.
2. Read each plausible definition and a representative caller. Check that the interface, build mode, error handling, and relevant lock or resource ownership match the new caller. Reuse a function when its contract fits. If a close candidate has a different contract, record that difference in the handoff.

## After committing a change that adds a function

1. Use a `cubrid-static-check` report for the same merge base and source commit if one exists. Otherwise, run `cubrid-static-check <base-ref> HEAD` from the source worktree. Use the task's integration branch or the pull request's base as `<base-ref>`.
2. Review the `Duplicated code` findings against both code locations. A matching token sequence is a candidate for reuse. Report confirmed duplication and any incomplete analysis in the handoff. If the command is unavailable, report the coverage gap.
