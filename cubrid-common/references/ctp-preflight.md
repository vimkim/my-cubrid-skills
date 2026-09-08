# CTP preflight

Shared by focused shell and SQL/medium runners. Read before executing CTP against a local CUBRID worktree.

## Preparation and installation identity

Run from the intended CUBRID Git worktree. Use `cubrid-build` to prepare missing local tooling and verify the selected preset. Before CTP execution:

```bash
git submodule update --init cubrid-jdbc
direnv exec . just configure-build
direnv exec . sh -c 'command -v cubrid; cubrid_rel; printf "CUBRID=%s\n" "$CUBRID"'
```

Inspect the actual local `just --list`/recipe definitions if names differ. The current canonical shell recipe is `ctp::shell-debug` (hyphen), with a root `shell-debug` compatibility wrapper. `just test` is ctest-only; it is not SQL/medium replay. After engine changes use `direnv exec . just build` and appropriate `just build-test` checks, then rerun the affected CTP case.

Record build/install paths, source SHA plus local patch identity, preset, testcase revision/patch, and relevant configuration. Parent `command -v` and version output are necessary but insufficient: inspect CTP child invocation/logs and executable paths. Some CTP wrappers source shell profiles, which can replace CUBRID, PATH and library settings; resolve that mismatch before treating the run as evidence of this build. Do not repoint a shared installation to hide it.

Inspect process and database ownership before running. The installed SQL/isolation scripts can kill broadly named CUBRID processes and recreate databases; a unique result directory or port alone does not isolate them. Use a dedicated environment with no unrelated CUBRID processes/databases subject to cleanup, or stop and arrange one. Do not terminate unrelated work to make room for a test.
