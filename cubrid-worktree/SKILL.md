---
name: cubrid-worktree
description: "Create, prepare, list, open, and safely delete CUBRID ticket worktrees and Herdr workspaces or tabs from any working directory for implementation, non-PR experiments or benchmarks, and PR code review, including worktrees with cubrid-cci/cubrid-jdbc submodules. Use when starting work on a CBRD ticket, opening a derived or benchmark worktree, preparing a PR review checkout, or deleting a finished worktree regardless of starting cwd. Triggers on phrases like 'start CBRD-XXXXX', 'create worktree for CBRD-XXXXX', 'open review worktree', 'prepare CBRD-XXXXX-bench', 'delete worktree', 'remove worktree', 'cubrid-worktree delete', 'cubrid-worktree'."
argument-hint: "[create|review|open|list|delete] [CBRD-XXXXX | CBRD-XXXXX-summary | PR URL/number]"
---

# CUBRID Worktree & Herdr Entry

Use the standalone `cubrid-worktree` CLI to manage ticket-first CUBRID worktrees under `~/gh/cb/` and their Herdr Spaces/Tabs from any starting directory.

Read `/home/vimkim/my-cubrid/CUBRID.md` and follow its forward-only policy: apply these rules to newly created worktrees, and preserve existing legacy worktrees and branches untouched.

## Steps

### 1. Check the CLI preflight

Verify `cubrid-worktree` is on `PATH`:

```bash
command -v cubrid-worktree
```

If missing, stop and tell the user to install it from `~/gh/cubrid-worktree` (`just install`) or GitHub (`uv tool install git+https://github.com/vimkim/cubrid-worktree`).

### 2. Apply ticket-first naming rules

Choose the worktree and branch name by task role:

| Task | Name | Base / Fallback |
| --- | --- | --- |
| Single original PR preparation | `CBRD-NNNNN` | Fetches and branches from `origin/develop` (or `--base <ref>`) |
| Non-PR test, benchmark, diagnostic, reproduction, or derived worktree | `CBRD-NNNNN-<summary>` | Allowed whether or not `CBRD-NNNNN` exists |
| First PR code review for a ticket | `CBRD-NNNNN` | Used when `CBRD-NNNNN` is unoccupied |
| PR code review when `CBRD-NNNNN` is already occupied | `CBRD-NNNNN-pr-<N>` | Automatic fallback by `cubrid-worktree review` |
| Unticketed PR code review | `PR-<N>` | Used when the PR title has no `[TICKET-123]` tag |

Keep `<summary>` short kebab-case (`[A-Za-z0-9][A-Za-z0-9._-]*`), without `/`, and without a second distinct ticket key.

### 3. Inspect existing ticket worktrees first

Before creating a worktree, check what already exists for that ticket from any `pwd`:

```bash
cubrid-worktree list CBRD-NNNNN --json
```

Use the result to decide whether to reuse an existing worktree (`open` or `--reuse`), create the primary `CBRD-NNNNN` worktree, or create a derived `CBRD-NNNNN-<summary>` worktree.

### 4. Create, review, open, or delete from any directory

`cubrid-worktree` automatically resolves `~/gh/cb/develop` as the control repository, manages sibling worktrees under `~/gh/cb/<name>`, runs `prepare-build` when creating, and handles Herdr placement when `HERDR_ENV=1`.

- **Implementation or non-PR experiment/benchmark**:

  ```bash
  cubrid-worktree create CBRD-NNNNN --json
  cubrid-worktree create CBRD-NNNNN-bench --base origin/develop --json
  ```

  Add `--no-fetch`, `--no-prepare`, `--no-herdr`, `--no-focus`, or `--reuse` when needed.

- **PR code review**:

  ```bash
  cubrid-worktree review 7887 --json
  cubrid-worktree review --interactive
  ```

  Review checkouts record `branch.<name>.pr-url` and `branch.<name>.cubrid-role = review`. Never push or trigger CI on a `review` checkout unless the user explicitly overrides that safety boundary.

- **Open an existing worktree in Herdr**:

  ```bash
  cubrid-worktree open CBRD-NNNNN-bench --json
  ```

  Pass `--new-tab` to force a fresh tab even if a pane with that `cwd` already exists in the ticket Space.

- **Delete a worktree (including submodules)**:

  ```bash
  cubrid-worktree delete CBRD-NNNNN-bench --dry-run --json
  cubrid-worktree delete CBRD-NNNNN-bench --json
  cubrid-worktree delete CBRD-NNNNN-bench --delete-branch --json
  ```

  - Inspects `.gitmodules` and index gitlinks directly (does not rely solely on `git submodule status`, so initialized submodules such as `cubrid-cci` and unregistered populated submodules such as `cubrid-jdbc` are both checked).
  - Refuses protected control/main worktrees, locked worktrees, active `cwd` inside the target, and dirty superprojects or submodules unless `--force` is explicitly approved.
  - Runs `git submodule deinit --all`, empties any remaining clean populated submodule directories, removes `<common-git-dir>/worktrees/<name>/modules/`, re-verifies clean status, and runs plain `git worktree remove` (without `--force` in normal mode).
  - Preserves the local branch by default; pass `--delete-branch` to delete a merged local branch (`git branch -d`, or `-D` with `--force`).
  - Scope boundary: `cubrid-worktree delete` removes only the Git worktree (and optional local branch). Before deleting an initialized CUBRID worktree, verify no active `cub_master`/`cub_server`/`cub_broker`/`cub_cas` or agent sessions use it, and release its `cub-workenv` numeric allocation first if applicable (`cub-workenv reset --worktree <path> --apply`, since `cub-workenv prune` only inspects missing entries still registered in Git). Afterward, remove any unneeded matching install prefix (`~/.cub/install/<name>`).

### 5. Follow the Herdr Space-per-ticket topology

Invoking this workflow authorizes `cubrid-worktree` to place worktrees into Herdr when `HERDR_ENV=1`:

- If no Herdr Space exists for the ticket (`CBRD-NNNNN`, or `PR-<N>`), it creates a new Space (`herdr-next-to-current` or `herdr workspace create`) and renames the initial tab to `<summary>` when starting with a derived worktree.
- If a Space for that ticket already exists, it creates a new Tab inside that existing Space with `--cwd` set to the worktree.

Report the created, opened, or deleted worktree path, branch (including kept/deleted status on delete), `cubrid-role`, submodule cleanup summary (if applicable), and Herdr location (`<workspace>, tab <label> (<tab_id>), pane <pane_id>`). If the user also asks to launch a coding agent in that new tab, follow the active Herdr and global agent-launch rules.
