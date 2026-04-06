---
name: cubrid-build
description: CUBRID build and test workflow using justfile. Use when building, compiling, or testing CUBRID source code in any CUBRID worktree or source directory.
---

# CUBRID Build & Test

Build and test CUBRID using the justfile workflow.

## When to Use

- User says "build", "compile", "test", "run tests", "빌드", "테스트"
- After code edits, to verify compilation or run tests
- When you need to check if changes compile or pass tests
- Any time you're working in a CUBRID source directory (contains `src/storage/`, `src/parser/`, etc.)

## Prerequisites

- Working directory must be a CUBRID source tree (or worktree)
- `justfile` must exist in the project root
- Environment variables `$CUBRID_BUILD_DIR` and `$PRESET_MODE` must be set (typically via direnv)

## Commands

### Build

```bash
just build
```

Build and install. **Use this to verify code edits compile.** Do not use `cmake --build` directly — the justfile handles preset modes, env vars (`$CUBRID_BUILD_DIR`, `$PRESET_MODE`), and the full pipeline.

### Test

```bash
just test
```

Run **all** tests: ctest (unit tests + sql-level integration tests) + sql regression tests.

### Build + Test

```bash
just build-test
# or the alias:
just nt
```

Build then run all tests. **This is the standard edit-compile-test cycle.**

### ctest Only

```bash
just ctest
```

Run ctest only (unit tests + sql-level integration tests). Faster than `just test` when you don't need sql regression tests.

### Configure

```bash
just configure
```

Run the cmake configure step. Needed after CMakeLists.txt changes or fresh checkouts.

### Full Reconfigure + Build

```bash
just configure-build-prepare-oos
```

Configure, build, and prepare OOS server config. Use after switching presets or major cmake changes.

## Typical Workflow

1. Edit code
2. `just build` — verify it compiles
3. `just test` — verify all tests pass
4. Or combine: `just build-test` (alias `just nt`)

## Important

- **Always use `just` commands**, never raw `cmake --build` or `ctest` directly.
- Run build commands with `run_in_background` when they may take a while.
- If build fails, read the error output carefully before attempting fixes.
