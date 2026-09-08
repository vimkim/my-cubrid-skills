# Choose faithful focused local test runners

Type: research
Label: wayfinder:research
Status: resolved
Assignee: codex/audit_runners
Parent: ../map.md
Blocked by: none

## Question

Which actual local recipes and CTP commands run a selected shell, SQL, or medium TC faithfully, what preparation do they require, and what evidence proves the intended binary and TC executed successfully? Which existing build/test skill instructions are stale or unsafe, and is a new framework necessary?

## Answer

Use the current `just ctp::shell-debug` helper for shell, and CTP SQL/medium with a temporary suite-specific configuration selecting a single scenario file. Basic single-case capability already exists; setup caching and runtime parity have not been demonstrated. The helper and CTP summaries require case identity/count checks beyond exit status. `just test` is ctest-only. JDBC initialization is separate from shared CCI preparation. Actual runners contain broad process cleanup, requiring an execution environment isolated from unrelated CUBRID work.

The [local runner audit](../research/local-runners.md) cites source locations and enumerates corrections for cubrid-build, cubrid-shell-run, create-testcases, and cubrid-isolation-test. No runtime tests were executed. Whether to build a new framework remains the user's scope decision.

Research branch: `research/cubrid-ci-fix-runners`, base `ad163a3`, isolated worktree `/tmp/cubrid-ci-fix-research-runners`. A research-only commit `562ba31dbd63e3a0bdd1ed89aef8f9c1cd69b37b` was made after an erroneous parent instruction, before the correction to leave it uncommitted arrived. No push occurred and shared main was not changed by that commit. The durable audit copy above is uncommitted in the map directory.
