---
name: cubrid-build
description: Prepare, configure, build, and test CUBRID worktrees with the preset-aware justfile workflow. Use for new or existing CUBRID worktrees and after engine code changes. Triggers on phrases like 'build CUBRID', 'prepare this worktree', 'compile this change', 'run CUBRID tests', or 'use release_gcc'.
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

## 3. Prepare and bootstrap a worktree

Before building, check that all preparation files exist at the worktree root:

- `justfile`
- `.envrc`
- `CMakeUserPresets.json`

If any are missing, or if this is a newly-created worktree, run the non-interactive bootstrap script. It performs the shared `just prepare`, validates and writes `.env`, runs configuration, and finishes with `just build`:

```bash
cubrid-worktree-bootstrap.sh \
  --preset debug_gcc \
  --worktree "$(git rev-parse --show-toplevel)"
```

Replace `debug_gcc` with the explicitly selected preset when necessary. This command is non-interactive; do not use `cmake-preset-mode-select.sh` or `fzf` in an autonomous agent workflow.

The canonical script is `$HOME/my-cubrid/bin/cubrid-worktree-bootstrap.sh` and is available on `PATH`. Verify it with `command -v cubrid-worktree-bootstrap.sh` rather than copying it into a worktree or skill directory.

## 4. Verify the loaded environment

For an already-prepared worktree, inspect `.env` before building:

```bash
sed -n 's/^[[:space:]]*PRESET_MODE[[:space:]]*=[[:space:]]*//p' .env
direnv exec . sh -c 'printf "PRESET_MODE=%s\nCUBRID_BUILD_DIR=%s\nCUBRID=%s\n" "$PRESET_MODE" "$CUBRID_BUILD_DIR" "$CUBRID"'
```

If the preset is missing, invalid, or differs from the required mode, rerun the bootstrap script with the correct `--preset`. Use `direnv exec .` when the current non-interactive shell has not reloaded `.env`.

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

Shared worktree preparation initializes CCI and does not replace JDBC initialization. Use `cubrid-shell-run` for shell, `cubrid-isolation-test` for isolation, and `cubrid-sql-run` for single-file CTP replay. These personal just recipes are local tooling; use standard build/test terminology in organization-facing documentation.

## 7. Handle failures

Read the first relevant configure, compiler, linker, or test error before changing code. Do not hide errors, bypass the justfile, or switch away from the requested preset merely to obtain a passing build.
