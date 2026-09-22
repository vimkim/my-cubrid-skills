---
name: cubrid-build
description: Prepare, configure, build, install, and run configured ctest tests in a CUBRID worktree through its live preset-aware just interface. Use for new worktree setup, compilation after engine changes, ctest verification, or an explicitly requested build preset. Not for SQL, medium, shell, or isolation regression runs.
---

# CUBRID Build & Test

Use the shared justfile workflow for every CUBRID build. New agent-created worktrees are not ready until the stowed environment files, a valid CMake preset, configuration, and an initial build are present.

## 1. Locate the worktree

Run commands from the Git root returned by:

```bash
git rev-parse --show-toplevel
```

Confirm it is a CUBRID source tree by checking for `CMakeLists.txt` and `src/`.

## 2. Choose the preset

Use the preset requested by the user. Otherwise use:

- `debug_gcc` for normal development, debugging, fixes, and tests.
- `release_gcc` only for an explicitly requested performance measurement or benchmark.
- Another preset only when the user or task explicitly requires it.

The preset must appear in `cmake --list-presets=configure`. Never invent a preset name.

## 3. Prepare a worktree

Before building, check that all preparation files exist at the worktree root:

- `justfile`
- `.envrc`
- `CMakeUserPresets.json`

If any are missing, or if this is a newly-created worktree, use the global preparation recipe from the worktree root:

```bash
just -f "$HOME/my-cubrid/cubrid-justfiles/justfile" -d . prepare-build
```

This stows the live personal just modules, prepares the environment, and selects `debug_gcc`. If another preset was explicitly requested, select it after preparation:

```bash
just preset release_gcc
```

Replace `release_gcc` with the requested preset. Then finish the initial configuration and build:

```bash
direnv exec . just configure
direnv exec . just build
```

Inspect `just --list` and `just --show <recipe>` after preparation. The worktree's live just interface is authoritative; do not copy recipe implementations into this skill.

## 4. Verify the loaded environment

For an already-prepared worktree, inspect `.env` before building:

```bash
sed -n 's/^[[:space:]]*PRESET_MODE[[:space:]]*=[[:space:]]*//p' .env
direnv exec . sh -c 'printf "PRESET_MODE=%s\nCUBRID_BUILD_DIR=%s\nCUBRID=%s\n" "$PRESET_MODE" "$CUBRID_BUILD_DIR" "$CUBRID"'
```

If the preset is missing, invalid, or differs from the required mode, select the required preset with `just preset <mode>`, then run `direnv exec . just configure` and `direnv exec . just build`. Use `direnv exec .` when the current non-interactive shell has not reloaded `.env`.

## 5. Build after every code change

Always compile and install after modifying CUBRID code:

```bash
direnv exec . just build
```

This is the required verification step even for a small edit. The build is normally fast because the preset uses ccache. Do not invoke `cmake --build` directly.

If CMake files changed or a selected preset has not yet been configured:

```bash
direnv exec . just configure
direnv exec . just build
```

## 6. Run tests appropriate to the change

Run the configured ctest tests (this recipe does not run CTP SQL/medium regression suites):

```bash
direnv exec . just test
```

Build and then test:

```bash
direnv exec . just build-test
```

Run ctest only:

```bash
direnv exec . just ctest
```

For CTP replay, initialize JDBC and configure/build before running the selected test:

```bash
git submodule update --init cubrid-jdbc
direnv exec . just configure-build
```

Shared worktree preparation initializes CCI and does not replace JDBC initialization. Use `cubrid-test-shell-run` for shell, `cubrid-isolation-test` for isolation, and `cubrid-test-sql-run` for focused SQL execution. There is no specialized medium runner in this collection. These personal just recipes are local tooling; use standard build/test terminology in organization-facing documentation.

## 7. Handle failures

Read the first relevant configure, compiler, linker, or test error before changing code. Do not hide errors, bypass the justfile, or switch away from the requested preset merely to obtain a passing build.
