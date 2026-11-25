# CUBRID `dev2` Disk Cleanup Catalog and Pitfalls

Reference catalog for `cubrid-disk-cleanup` on `dev2` (`/home/vimkim`).

## 1. Directory Taxonomy & Tier Classification

### Tier 0 — Build Artifacts (Reconstructible by rebuild)
- `~/gh/cb/*/build*` (`build_preset_debug_gcc`, `build_preset_release_gcc`, `build_preset_optdebug`, `build_preset_release_gcc_unit`, `cmake-build-*`). Note: `unit_tests/oos/` inside debug builds can grow to 3–7 GiB due to embedded test databases.
- Stale moved CMake build trees under `~/gh/cb/` (non-Git directories containing `CMakeFiles/`, `3rdparty/`, `sa/`, `cs/`).
- `~/temp/*/build` and `~/temp/*/source/build_preset_*` from packaging or PR checks.
- Rust `target/` under `~/gh/cubrid-ci`, `~/gh/dirpick`, `~/gh/work-tracker`, `~/gh/cubrid-rust/main` (installed binaries live in `~/.cargo/bin` and `~/.local/bin`, not `target/`).
- Lean `.lake/build` under `~/temp/oos-lean*` (remove `.lake/build` only, leaving `.lake/packages` and source intact).
- Next.js build outputs (`.next*`) and Sphinx `_build` directories under `~/temp/`.

### Tier 1 — Safe Disposable Artifacts & Caches (Ask approval before removal)
- `~/tk/*`: Native testkit and CTP run directories (`perf-*`, `oos-sync-*`, `c44`, `hdrc`, etc.). Check `/proc` for 0 active processes referencing `~/tk/` before removing.
- `~/tmp/*`: Temporary agent scratch trees (e.g., `oos-lean-implementation` snapshots and observations).
- Giant diagnostic logs in `~/temp/` (e.g., `diagdb_head_*.out`, multi-GiB `server/*.err` or `unloaddb.err`). Check that no process holds them open in `/proc/*/fd`.
- Broken orphaned testcase checkouts inside `~/gh/cubrid-testcases/` whose `.git` file points to a nonexistent repository path (e.g., `/home/vimkim/cubrid-testcases-private-ex/.git/worktrees/...`).
- Packaging or extraction sandboxes in `~/temp/` (`cubrid-*-make-dist.*`, `cbrd-*-packaging.*`, `w820b-*`). Check that `git worktree list` does not list them.
- Podman unused images: run `podman image prune -a -f`. Check `podman system df` and `podman ps -a` first, and avoid pruning containers or volumes without approval.
- Log directories inside `~/.cub/install/*/debug_gcc/log/` and inactive orphan `~/.cub/install/<name>` (where `~/gh/cb/<name>` no longer exists).
- Tool caches and superseded binary versions:
  - `~/.codex/packages/standalone/releases/*`: keep active running version and highest version.
  - `~/.debug/*`: `perf` build-id debug cache.
  - `~/.vscode-server/cli/servers/*` and `data/CachedExtensionVSIXs`: keep `lru.json[0]` and active server processes, update `lru.json`, and preserve `extensions/` and `code-*`.
  - `~/.npm/_cacache`, `~/.npm/_npx` (when no `npm` or `npx` process runs).
  - `~/.cache/Homebrew/downloads`, `uv cache clean`.
  - `~/.local/share/Trash/{files,info}`.
  - `~/.local/share/claude/versions/*`: keep active running versions and newest version.

### Tier 2 — Inactive Development State (Ask approval before removal)
- Inactive `~/gh/cb/*/.cub-workenv`: Contains `db/` test databases (can reach 9–34 GiB each for `inner-table`, `sidecar`, `repid-65535-repro`). Must cross-check active `cub_master`, `cub_server`, `cub_broker`, `cub_cas`, agents, and containers.
- `CLEAN` linked worktrees in `~/gh/cubrid-testcases-private-ex/*` and `~/gh/cubrid-testcases/*` (excluding `develop`).
- `CLEAN` inactive linked worktrees in `~/gh/cb/*` (excluding `cubrid` and `develop`, and preserving worktrees containing `.scratch`, `.artifacts`, or `scratch`).
  - `cubrid-worktree delete` also removes clean per-worktree submodule checkouts under `~/gh/cb/cubrid/.git/worktrees/<name>/modules/`. These can account for ~10–20 GiB across the worktree collection.
- Remaining inactive `~/.cub/install/<name>` directories (always preserve `develop` and active daemon prefixes).
- Project `.scratch/`, `experiments/`, and docker runtime node directories (`docker-compose/node-{a,b}`) after checking 0 git-tracked files, 0 active daemons, and 0 `ET_CORE` files.

### Tier 3 — Backups, Archives, Tool Data, Personal Files (Keep, remove, or move to `/mnt/nvme/data-*`)
- `/mnt/nvme/data-{1..8}` typically has ~2–3 TB aggregate free space (check `df -h` first) for offloading items that should not be removed.
- Candidates:
  - Cleanup archives (`~/temp/vimkim-quota-cleanup-*/archives`, `~/repo-cleanup-backups`).
  - `~/.local/share/cubrid-ci-data` (`git-cache`, `github-actions`, `CBRD-*` artifacts).
  - `~/.codex/sessions` and `~/.codex/thread_history_1.sqlite` (check active `codex` daemons before touching).
  - `~/.local/share/uv/tools/cubrid-oos-search` (large Python/ML venv).
  - Reference checkouts (`~/gh/mysql`, `~/gh/pg`).
  - Unused toolchains (`~/.rustup/toolchains`, `~/.local/share/mise/installs`, `~/.elan`).
  - `~/.local/share/cubrid-tc-chronicle/backups`.
  - Personal directories (`~/temp/university`).

---

## 2. Known `dev2` Pitfalls & Mandatory Protections

1. **ELF `ET_CORE` Core Dump Misidentification (2026-11-18 incident)**
   - A `core.loaddb.*` file inside `.cub/install/...` was previously mistaken for a compiled binary and removed.
   - Always inspect the 20-byte ELF header (`\x7fELF`, `e_type` at bytes `[16:18]`): `ET_REL=1`, `ET_EXEC=2`, `ET_DYN=3`, **`ET_CORE=4`**.
   - Never remove any `ET_CORE` file automatically. List its exact path and size for explicit user approval.

2. **Git Submodule Bloat Inside `~/gh/cb/cubrid/.git/worktrees/`**
   - Initialized `cubrid-cci` and `cubrid-jdbc` submodules store module gitdirs inside `cubrid/.git/worktrees/<name>/modules/` (~19 GiB across ~240 worktrees).
   - Use `cubrid-worktree delete --dry-run` to check the superproject and populated submodules, including submodules with no configured `submodule.*.url`. Follow the linked-worktree removal procedure in the skill.

3. **Active Daemons, Bots, and Agents**
   - Always check live `/proc` before removing `node_modules`, `.venv`, `.cache/ms-playwright`, `~/.hermes`, `~/.local/share/*-bot`, or `~/temp/*`:
     - Bots and automation: `cubrid-teams-dev2bot`, `vimkim-bot`, `my-cubrid-pr-review`, `teams-reader`, `cubrid-ci-shell-queue-website`, `hermes`.
     - Playwright browser cache: check which `chromium-*` version is actively executed, and keep `~/.cache/ms-playwright`.
     - Idle `cub_master`: a lingering `cub_master` daemon keeps its `.cub/install/<name>` prefix and CWD active. Check `/proc` and stop cleanly (`cubrid master stop` with `stdin=DEVNULL` per `CBRD-27443`) only when authorized to remove that experiment.
     - Zombie `(deleted)` daemons: processes whose `exe` already says `(deleted)` (e.g., `cub_master (deleted)`) hold memory, not directory locks, until restarted or stopped.

4. **Preserve Build Speed & History**
   - Never remove `~/.cache/ccache` (keeps incremental CUBRID rebuilds under ~20s).
   - Never remove `dirty` Git worktrees or worktrees containing `.scratch` or `.artifacts` notes without explicit review.
   - Check `git for-each-ref refs/heads` before and after bulk worktree cleanup and save exact `git worktree add` restoration JSON.

5. **`du` vs `df` Discrepancies**
   - XFS shared extents/reflinks, concurrent server writes by other `dev2` users, or open `(deleted)` FDs can cause `df` free-space deltas to differ from `du` sums.
   - Always report both `du` and `df -h /home`, and check that `/proc/*/fd` shows `0` bytes held in `(deleted)` files under `$HOME`.

6. **`uv cache clean` Lock Hang**
   - `uv cache clean` can hang indefinitely on `~/.cache/uv/.lock` when another `uv` process or stale lock blocks access.
   - Always invoke `uv cache clean` with a short timeout (for example `timeout=30`), and skip it when the lock blocks completion.

7. **Python 3.12+/3.14 `shutil.rmtree` Permission Handler Pitfall**
   - `shutil.rmtree(..., onexc=...)` may pass `os.open` as `func` (requiring `flags`), which breaks simple `func(path)` retries.
   - Pre-chmod directories inside `target_real` to `u+rwx` and regular files to `u+rw` before calling `shutil.rmtree` so read-only test trees remove cleanly.
