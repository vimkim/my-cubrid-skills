# my-cubrid-skills

A collection of Claude Code skills for CUBRID database engine development. These skills provide specialized workflows for JIRA integration, PR reviews, CI failure analysis, test creation, and more.

## Skills

| Skill | Description |
|-------|-------------|
| `cubrid-jira` | Look up CUBRID JIRA issue context (CBRD-XXXXX) |
| `cubrid-test-sql-run` | Run focused SQL cases with native testkit and verify artifact verdicts |
| `cubrid-test-medium-run` | Run complete medium directories serially with native testkit and verify artifact verdicts |
| `cubrid-test-shell-run` | Run focused shell cases with contained native testkit and verify artifact verdicts |
| `cubrid-ci-analyze` | Collect exact-commit GitHub Actions evidence with `cubrid-ci` and write failure-analysis reports |
| `cubrid-ci-trigger` | Trigger or rerun GitHub Actions gha-ci on supported CUBRID pull requests |
| `cubrid-pr-create` | Create GitHub PRs with `[CBRD-XXXXX]` title format and Korean body |
| `cubrid-jira-issue-write` | Write structured JIRA issue reports in Korean |
| `cubrid-manual-search` | Answer CUBRID questions from the local English/Korean RST manual with file-and-line citations |
| `cubrid-oos-context` | Load OOS (Out-of-row Overflow Storage) project context |
| `create-testcases` | Create CUBRID test cases (unit/SQL/shell) for features or bug fixes |
| `track-work` | Register, update, and inspect long-running work in the `work-tracker` ledger so status and context survive agent sessions |
| `cubrid-common` | Shared helper scripts used internally by other CUBRID skills |

## CI and test skill layout

| Responsibility | Skill |
|---|---|
| Read-only runtime snapshot and root-cause report | `cubrid-ci-analyze` |
| Authorized one-shot CI trigger and duplicate prevention | `cubrid-ci-trigger` |
| Focused local shell execution | `cubrid-test-shell-run` |
| Focused local SQL execution | `cubrid-test-sql-run` |
| Focused local medium execution | `cubrid-test-medium-run` |
| Build/install and configured ctest suite | `cubrid-build` |
| New behavioral testcases | `create-testcases` |
| Shared native testkit preflight/configuration/verdict, CI evidence identity, and common helpers | `cubrid-common` |

Snapshot analysis and triggering are independent capabilities; SQL, medium, and shell retain distinct selection and result contracts. Shared native-testkit preparation and CI evidence identity live under `cubrid-common`, not a user-facing coordinator. Runner names stay independent of the current runner implementation.

## Installation

### Using `npx skills`

Uses the [`skills`](https://github.com/vercel-labs/skills) CLI to install globally to `~/.claude/skills/`.

```bash
npx skills add vimkim/my-cubrid-skills -y -g
```

Or clone locally and use the justfile:

```bash
git clone https://github.com/vimkim/my-cubrid-skills.git ~/gh/my-cubrid-skills
cd ~/gh/my-cubrid-skills
just sync
```

**Managing:**

```bash
just sync                # Verify current skills, then recoverably prune obsolete owned skills
just sync-dry-run        # Preview additions, conflicts and removals
just list                # List installed skills
just remove cubrid-jira  # Remove a specific skill
```

Run `just sync` after source updates. It never pulls Git. Python 3.12+, Git, just, Node 22.20+ and npm/npx are required. The Python standard-library engine invokes `skills@1.7.0` in an isolated staging home, verifies both agent installations, and promotes changes before pruning. Source layout remains top-level `<name>/SKILL.md`.

Ownership lives in `~/.local/state/skill-collections/state.json` and applicable installer metadata. Git history alone never authorizes deletion. Edited or manually managed installations and third-party ownership are preserved; conflicts return 2 while independent eligible installs may proceed. Current conflicts suppress collection pruning. Installer, scan and verification failures return 1; missing peer evidence skips pruning and returns 2. Local legacy copies without ownership evidence require review and backup before explicit replacement.

`collection-sync.json` lists both personal collections and the five approved old-to-new transfers. Default paths expect sibling checkouts; for worktrees or another layout pass `just sync --config /absolute/path/config.json` with correct collection paths. Missing peers never imply deletion. Destination-supplied or destination-owned skills remain protected whichever collection synchronizes first. The destination verifies installation and ownership transfer before original source files are removed.

Removed unchanged owned skills are backed up under `$XDG_STATE_HOME/skill-collections/recovery/removed-*` (default `~/.local/state`). Sync prints the verified recovery location. Restore content, agent links, ownership and installer metadata without overwriting existing skills:

```sh
just sync-dry-run --restore /absolute/path/to/recovery/removed-XXXX
just sync --restore /absolute/path/to/recovery/removed-XXXX
```

Restore the source directory too before the next normal sync. Explicit `just remove` remains a direct installer action without recovery. Sync does not manage third-party updates.

`tools/sync_skills.py` is a standalone vendored copy of `vimkim/my-skills/scripts/sync_skills.py`; maintain both copies together. The authoritative engine, public-command tests and full conflict/recovery documentation are in `my-skills`. Validate byte equality, the old wrapper and restoration in isolation using `python3 ../my-skills/tests/check_vendored_sync.py .` from this checkout. No live synchronization is part of that check.

## Usage

Once installed, invoke skills as slash commands in Claude Code:

```
/cubrid-jira CBRD-25123
/cubrid-pr-create CBRD-26583
/cubrid-ci-analyze https://github.com/CUBRID/cubrid/pull/6864
/cubrid-manual-search What is the default value of max_clients?
/create-testcases CBRD-26609
/track-work register this CI wait and keep its status current
```

Skills also trigger automatically based on context.

## Prerequisites

Some skills require external tools:

| Tool | Required by | Install |
|------|------------|---------|
| `cubrid-jira` | `cubrid-jira` | `uv tool install git+https://github.com/vimkim/cubrid-jira` |
| `gh` | `cubrid-ci-trigger`, `cubrid-ci-analyze`, `cubrid-pr-create` | [cli.github.com](https://cli.github.com/) |
| `cubrid-ci` | `cubrid-ci-analyze` | `cargo install --path /home/vimkim/gh/cubrid-ci --locked` |
| `testkit` | `cubrid-test-sql-run`, `cubrid-test-medium-run`, `cubrid-test-shell-run` | Manually install the intended `cubrid-testkit` revision with `go install` |
| JDK 8 + CTP assets | `cubrid-test-sql-run`, `cubrid-test-medium-run` | Use the selected worktree environment's configured installations |
| `work-tracker` | `track-work` | `just install` in `/home/vimkim/gh/work-tracker` |

## License

MIT
