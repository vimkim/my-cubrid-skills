---
name: cubrid-disk-cleanup
description: "Audit and reduce disk usage under a CUBRID home directory on Linux. Use when /home approaches capacity, a quota alert triggers, or old worktrees, build directories, and caches accumulate. Triggers on phrases like 'disk usage warning', 'reduce /home usage', 'remove old worktrees', '디스크 용량 정리', '빌드 아티팩트 정리'."
---

# CUBRID Disk Cleanup

Audit home directory storage, enforce safety checks, remove approved targets by tier, and report freed disk space. Consult [references/cleanup-catalog.md](references/cleanup-catalog.md) for the `dev2` directory catalog, tier rules, and known pitfalls.

Pass an optional size threshold or scope through `$ARGUMENTS` (default: review all directories at or above `2 GiB`).

## 1. Measure baseline usage and live processes

1. Run `df -h /home` to record total, used, and available filesystem space.
2. Run parallel `du -x -B1 -s` across all top-level entries under `$HOME`.
3. Scan `/proc/*/exe`, `/proc/*/cwd`, `/proc/*/environ`, `/proc/*/fd`, and `/proc/*/cmdline` for processes owned by the current user.
4. Record every active `.cub/install/<name>` prefix, active `~/gh/cb/<name>` worktree, running agent or bot directory, and running compiler (`cmake`, `ninja`, `make`, `gcc`, `clang`, `ld`, `cargo`, `rustc`, `lake`, `lean`, `cpack`).
5. Scan `/proc/*/fd` for open `(deleted)` files at or above `1 MiB` under `$HOME`.

## 2. Audit directories at or above the threshold

1. Inspect every top-level directory at or above the size threshold (`2 GiB` by default) to identify subdirectories at or above `2 GiB`.
2. Classify Git worktrees under `~/gh/cb` and `~/gh/cubrid-testcases*`:
   - Separate `CLEAN`, `DIRTY`, `locked`, `prunable`, and broken `NOT_GIT` worktrees.
   - Check detached `HEAD` commits for branch, tag, or remote reachability.
   - Check each clean worktree for `.scratch`, `.artifacts`, `scratch`, and initialized submodules.
3. Classify `~/.cub/install/*` directories as active, inactive, or orphan (no matching `~/gh/cb/<name>` checkout).
4. Check Podman reclaimable storage with `podman system df` and free space on `/mnt/nvme/data-*`.

## 3. Enforce safety checks before every removal

Apply all safety checks before removing any file or directory:

1. Abort build-directory removal if an active compiler or build process runs.
2. Walk each candidate directory and read the ELF header of any file named `core`, `core.*`, or `*.core`. If `e_type == 4` (`ET_CORE`), skip that candidate and report the preserved core dump path.
3. Check that zero Git-tracked files (`git ls-files`) sit inside any build, cache, or scratch target before removal.
4. Preserve every path referenced by an active process, every dirty worktree, primary `develop` or `main` checkouts, `~/.cache/ccache`, and personal archives.
5. Remove directories through Python `shutil.rmtree` with an internal `PermissionError` chmod handler, not unguarded shell `rm -rf` expansions.
6. Remove clean linked Git worktrees without `--force`:
   - Snapshot `git for-each-ref refs/heads` before removal.
   - Check submodule cleanliness with `git submodule foreach --recursive`.
   - Run `git submodule deinit --all` without `--force` when initialized submodules exist.
   - Run `git worktree remove` without `--force`.
   - Save `git worktree add` restoration commands to `~/temp/vimkim-disk-cleanup/`.
   - Check that `git for-each-ref refs/heads` after removal matches the pre-removal snapshot.

## 4. Review and execute by approval tier

Present candidates grouped by tier and wait for explicit user approval unless the user already authorized that tier.

1. **Tier 0 (Build artifacts)**: `~/gh/cb/*/build*`, stale moved CMake build trees, `~/temp/*/build*`, Rust `target/`, Lean `.lake/build`, and Next.js `.next*` directories. Remove them immediately only when the user explicitly pre-authorized build artifact removal.
2. **Tier 1 (Disposable artifacts and caches)**: `~/tk/*` testkit runs, temporary scratch in `~/tmp/`, multi-gigabyte diagnostic logs, broken orphan testcase checkouts, packaging sandboxes, and unused Podman images (`podman image prune -a`). Tier 1 also covers install log files, inactive orphan `.cub/install/*` entries, and superseded tool versions or caches. Require user confirmation before removal.
3. **Tier 2 (Inactive development state)**: inactive `~/gh/cb/*/.cub-workenv`, `CLEAN` linked worktrees in testcase and engine repositories, remaining inactive `~/.cub/install/*` entries (excluding `develop`), and project `.scratch` or experiment directories without `ET_CORE` files. Require user confirmation before removal.
4. **Tier 3 (Archives, backups, and personal data)**: present removal versus relocation to free `/mnt/nvme/data-*` volumes.

Write a JSON audit record of all removed, skipped, preserved, and errored paths under `~/temp/vimkim-disk-cleanup/`.

## 5. Report post-cleanup state

1. Re-run `df -h /home`, parallel top-level `du` on `$HOME`, and the open `(deleted)` FD scan.
2. Check `du` on primary `.git/worktrees` directories and `podman system df` when Tier 2 or Podman cleanup ran.
3. Report before and after `du` and `df` numbers, reclaimed GiB per category, clickable links to audit and restoration logs, preserved `ET_CORE` paths, active exceptions, and remaining candidates.
