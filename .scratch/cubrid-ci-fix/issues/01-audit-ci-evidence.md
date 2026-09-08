# Choose reliable CI evidence and testcase identity sources

Type: research
Label: wayfinder:research
Status: resolved
Assignee: codex/audit_ci
Parent: ../map.md
Blocked by: none

## Question

Which existing skills and tools reliably identify all runtime and miscellaneous PR CI failures at a fixed commit, map failed tests to exact testcase revisions and configured local Git roots, and preserve a complete failure inventory? What source-backed corrections and API fallback contracts are needed?

## Answer

Reuse cubrid-ci's exact runtime job/commit checks and sequential snapshot collection. Extend the workflow with provenance-preserving read-only API collection for missing capabilities and GitHub miscellaneous checks. Preserve Actions merge-tree identity separately from PR head. Inspect abnormal raw results and job-level failures beyond normalized failed-test lists. Validate testcase repository/revision/path per test; the summary revision is merely the first message match and cannot prove a suite-wide revision.

Correct cubrid-ci-trigger's nonexistent REST timeline synchronize lookup and implicit push instruction. Trigger permission does not authorize pushing. Preserve complete comment/check pagination, exact-head trigger receipts, and uncertainty when prior trigger association is unprovable.

The [CI evidence audit](../research/ci-evidence.md) provides source and official API citations, fallback requirements, and a recommended durable repair ledger. These research findings inform implementation; retry policy and post-push authorization remain unresolved human decisions.

Research branch: `research/cubrid-ci-fix-evidence`, base `ad163a3c174deaf62c2585106a6020a4ee03db41`, isolated worktree `/tmp/cubrid-ci-fix-evidence`. Findings are uncommitted; no API mutations, live CI runs, or pushes occurred.
