<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/readme/hero-dark.svg">
    <img alt="my-cubrid-skills end-to-end CUBRID agent workflow" src="assets/readme/hero-light.svg" width="100%">
  </picture>
</p>

<h1 align="center">my-cubrid-skills</h1>

<p align="center">
  <strong>End-to-end Claude Code &amp; Codex skill pipeline for CUBRID database engine development.</strong><br>
  Ticket-first worktrees, native testkit verification, human-gated PRs, CI root-cause analysis, and ownership-aware sync.
</p>

<p align="center">
  <a href="#why-this-exists--end-to-end-workflow">Workflow</a> ·
  <a href="#skills-by-workflow-stage">Skills (24)</a> ·
  <a href="#ci-and-test-skill-layout">CI &amp; Test Layout</a> ·
  <a href="#installation--sync">Installation &amp; Sync</a> ·
  <a href="#usage">Usage</a> ·
  <a href="#prerequisites">Prerequisites</a> ·
  <a href="#general-purpose-skill-migration">Migration</a>
</p>

---

## Why this exists & end-to-end workflow

Engine work on CUBRID spans JIRA triage, multi-submodule worktrees, preset CMake/Ninja builds, three separate native `cubrid-testkit` runners, dual engine + testcase PRs, GitHub Actions diagnostics, and squash merges. Ad-hoc prompts drift across sessions and mix read-only investigation with irreversible mutations.

`my-cubrid-skills` packages those workflows as composable, contract-driven `SKILL.md` modules built around three engineering boundaries:

- **Explicit human gates on external writes**: PR creation ([`cubrid-pr-create`](cubrid-pr-create/SKILL.md)) persists a draft body for review before opening or updating GitHub PRs; final merges ([`cubrid-pr-merge`](cubrid-pr-merge/SKILL.md)) are strictly user-invoked with squash commit previews.
- **Read-only diagnostics decoupled from side effects**: Snapshot CI analysis ([`cubrid-ci-analyze`](cubrid-ci-analyze/SKILL.md)) never triggers workflows, while workflow dispatch ([`cubrid-ci-trigger`](cubrid-ci-trigger/SKILL.md)) enforces duplicate/rerun guards independently.
- **Isolated verification & atomic sync**: Local tests run through native `cubrid-testkit` with ordered artifact verdicts rather than guessed exit codes, and skill installation uses isolated staging with ownership tracking and recoverable pruning.

### End-to-end stage flow

1. **JIRA & Triage**: Inspect tickets ([`cubrid-jira`](cubrid-jira/SKILL.md)), cross-reference linked PRs ([`cubrid-xref`](cubrid-xref/SKILL.md)), screen duplicates ([`cubrid-jira-dup`](cubrid-jira-dup/SKILL.md)), and author Korean triage reports ([`cubrid-jira-issue-write`](cubrid-jira-issue-write/SKILL.md)).
2. **Worktree & Herdr Space**: Spin up or clean up ticket-first worktrees with `cubrid-cci`/`cubrid-jdbc` submodules and Herdr Spaces/Tabs ([`cubrid-worktree`](cubrid-worktree/SKILL.md)).
3. **Build & Focused Testkit**: Configure preset builds and run `ctest` ([`cubrid-build`](cubrid-build/SKILL.md)), then verify focused SQL, medium, or shell cases ([`cubrid-test-sql-run`](cubrid-test-sql-run/SKILL.md), [`cubrid-test-medium-run`](cubrid-test-medium-run/SKILL.md), [`cubrid-test-shell-run`](cubrid-test-shell-run/SKILL.md)).
4. **2-Step Draft PR**: Persist the Korean PR body and resume metadata in `my-cubrid-docs`, review or edit, and publish only after confirmation ([`cubrid-pr-create`](cubrid-pr-create/SKILL.md)).
5. **Review & CI Analyze**: Run budgeted specialist code reviews ([`cubrid-code-review`](cubrid-code-review/SKILL.md)), trigger or rerun `gha-ci` safely ([`cubrid-ci-trigger`](cubrid-ci-trigger/SKILL.md)), and attribute exact-commit failures ([`cubrid-ci-analyze`](cubrid-ci-analyze/SKILL.md)).
6. **User-Invoked Merge**: Preview squash commit messages for the engine PR and linked testcase PRs, merge changed TC PRs, close unchanged ones, refresh the TC gate, and merge the engine PR on confirmation ([`cubrid-pr-merge`](cubrid-pr-merge/SKILL.md)).

---

## Skills by workflow stage

### 1. JIRA & Cross-Reference

| Skill | Purpose |
|-------|---------|
| [`cubrid-jira`](cubrid-jira/SKILL.md) | Look up CUBRID JIRA issue context (`CBRD-XXXXX`), choose transitions, and publish reviewed Markdown descriptions |
| [`cubrid-jira-kanban-sync`](cubrid-jira-kanban-sync/SKILL.md) | Sync active CUBRID JIRA kanban ticket statuses with live GitHub PR, review, CI, and sub-task state |
| [`cubrid-jira-dup`](cubrid-jira-dup/SKILL.md) | Find and assess duplicate or related `CBRD` issues before creating or writing to JIRA |
| [`cubrid-jira-issue-write`](cubrid-jira-issue-write/SKILL.md) | Write or revise structured Korean JIRA issue reports for triage |
| [`cubrid-xref`](cubrid-xref/SKILL.md) | Bidirectional lookup between CUBRID GitHub PRs and `CBRD` JIRA issues (engine, `tc-private`, `tc-public`, follow-up PRs) with 24h local SQLite caching |

### 2. Workspace, Build & Local Verification

| Skill | Purpose |
|-------|---------|
| [`cubrid-worktree`](cubrid-worktree/SKILL.md) | Create, prepare, list, open, and safely delete (with submodules) ticket-first CUBRID worktrees and Herdr Spaces/Tabs |
| [`cubrid-build`](cubrid-build/SKILL.md) | Prepare, configure, build, install, and run configured `ctest` suites via preset-aware `just` targets |
| [`cubrid-test-sql-run`](cubrid-test-sql-run/SKILL.md) | Run focused SQL cases or narrow SQL subtrees with native `cubrid-testkit` and prove artifact verdicts |
| [`cubrid-test-medium-run`](cubrid-test-medium-run/SKILL.md) | Run complete medium testcase directories serially with native `cubrid-testkit` and verify ordered artifact verdicts |
| [`cubrid-test-shell-run`](cubrid-test-shell-run/SKILL.md) | Run focused shell cases with contained native `cubrid-testkit` and verify artifact verdicts |
| [`create-testcases`](create-testcases/SKILL.md) | Create CUBRID test cases (unit/SQL/shell) for new features or bug fixes |
| [`cubrid-performance`](cubrid-performance/SKILL.md) | Diagnose and optimize CUBRID workloads, engine code, and utilities on Linux with optional baseline comparisons |

### 3. Pull Requests, Review, CI & Merge

| Skill | Purpose |
|-------|---------|
| [`cubrid-pr-create`](cubrid-pr-create/SKILL.md) | Save Korean PR drafts in `my-cubrid-docs` for human review, then create draft PRs or update existing descriptions after confirmation |
| [`cubrid-code-review`](cubrid-code-review/SKILL.md) | Review pinned PRs or diffs with budgeted specialists across C/C++, concurrency, storage I/O, recovery, and HA, with evidence-backed reports and handoffs |
| [`cubrid-ci-trigger`](cubrid-ci-trigger/SKILL.md) | Trigger, rerun, or wait on GitHub Actions `gha-ci` for supported CUBRID PRs with duplicate-cancellation prevention |
| [`cubrid-ci-analyze`](cubrid-ci-analyze/SKILL.md) | Collect exact-commit GitHub Actions evidence with `cubrid-ci`, add testcase-history context, and write failure-analysis reports |
| [`cubrid-pr-merge`](cubrid-pr-merge/SKILL.md) | User-invoked: preview squash commit messages, then merge changed TC PRs, close unchanged ones, refresh the TC gate, and merge the engine PR after confirmation |

### 4. Reference, QA & Operations

| Skill | Purpose |
|-------|---------|
| [`cubrid-manual-search`](cubrid-manual-search/SKILL.md) | Answer CUBRID questions from the local English/Korean RST manual with file-and-line citations |
| [`cubrid-oos-context`](cubrid-oos-context/SKILL.md) | Load authoritative OOS (Out-of-row Overflow Storage) project specification context when conformance or design behavior matters |
| [`cubrid-qa-fetch`](cubrid-qa-fetch/SKILL.md) | Fetch and analyze authenticated pages, NOK lists, and core stacks from CUBRID's internal QA portal |
| [`cubrid-disk-cleanup`](cubrid-disk-cleanup/SKILL.md) | Audit Linux CUBRID home disk usage, enforce live-process/worktree safety checks, and clean approved artifacts by tier |
| [`daily-schedule`](daily-schedule/SKILL.md) | Maintain daily and weekly work plans using `my-cubrid-schedule`, the external `track-work` ledger, and live GitHub/CI state |
| [`my-cubrid-skills-create`](my-cubrid-skills-create/SKILL.md) | Scaffold and register new skills in the `my-cubrid-skills` collection |

### 5. Internal Shared Foundation

| Skill | Purpose |
|-------|---------|
| [`cubrid-common`](cubrid-common/SKILL.md) | Shared workflow policy, user context, native testkit preflight/configuration/verdict logic, CI evidence identity, and helper scripts used internally by other CUBRID skills |

### General-purpose skill migration

The general-purpose skills `gh-pr-comments-all`, `resolve-greptile-comments`, `markdown-write`, and `track-work` moved to [vimkim/my-skills](https://github.com/vimkim/my-skills). Maintain and install them from that collection. `question-socratically` moved there too and is now disabled. `daily-schedule` and `my-cubrid-skills-create` remain here; `daily-schedule` uses the external `track-work` skill. See [docs/general-skills-migration.md](docs/general-skills-migration.md).

---

## CI and test skill layout

| Responsibility | Skill |
|---|---|
| Read-only runtime snapshot and root-cause report | [`cubrid-ci-analyze`](cubrid-ci-analyze/SKILL.md) |
| Authorized one-shot CI trigger and duplicate prevention | [`cubrid-ci-trigger`](cubrid-ci-trigger/SKILL.md) |
| Focused local shell execution | [`cubrid-test-shell-run`](cubrid-test-shell-run/SKILL.md) |
| Focused local SQL execution | [`cubrid-test-sql-run`](cubrid-test-sql-run/SKILL.md) |
| Focused local medium execution | [`cubrid-test-medium-run`](cubrid-test-medium-run/SKILL.md) |
| Build/install and configured `ctest` suite | [`cubrid-build`](cubrid-build/SKILL.md) |
| New behavioral testcases | [`create-testcases`](create-testcases/SKILL.md) |
| Shared native testkit preflight/configuration/verdict, CI evidence identity, and common helpers | [`cubrid-common`](cubrid-common/SKILL.md) |

Snapshot analysis and triggering are independent capabilities; SQL, medium, and shell retain distinct selection and result contracts. Shared native-testkit preparation and CI evidence identity live under [`cubrid-common`](cubrid-common/SKILL.md), not a user-facing coordinator. Runner names stay independent of the current runner implementation.

---

## Installation & sync

### Quick install (`npx skills`)

Uses the [`skills`](https://github.com/vercel-labs/skills) CLI to install globally to `~/.claude/skills/` (and configured agents):

```bash
npx skills add vimkim/my-cubrid-skills -y -g
```

### Local clone & `just` workflow

Clone locally and manage both Claude Code and Codex installations through [`justfile`](justfile):

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

### Sync engine, requirements & ownership

Run `just sync` after source updates. It never pulls Git. **Python 3.12+**, **Git**, **just**, **Node 22.20+**, and **npm/npx** are required. The Python standard-library engine invokes `skills@1.7.0` in an isolated staging home, verifies both agent installations, and promotes changes before pruning. Source layout remains top-level `<name>/SKILL.md`.

Ownership lives in `~/.local/state/skill-collections/state.json` and applicable installer metadata. Git history alone never authorizes deletion. Edited or manually managed installations and third-party ownership are preserved; conflicts return `2` while independent eligible installs may proceed. Current conflicts suppress collection pruning. Installer, scan, and verification failures return `1`; missing peer evidence skips pruning and returns `2`. Local legacy copies without ownership evidence require review and backup before explicit replacement.

### Cross-collection migrations (`collection-sync.json`)

[`collection-sync.json`](collection-sync.json) lists both personal collections and the five approved old-to-new transfers. Default paths expect sibling checkouts; for worktrees or another layout pass `just sync --config /absolute/path/config.json` with correct collection paths. Missing peers never imply deletion. Destination-supplied or destination-owned skills remain protected whichever collection synchronizes first. The destination verifies installation and ownership transfer before original source files are removed.

### Recoverable pruning & restore

Removed unchanged owned skills are backed up under `$XDG_STATE_HOME/skill-collections/recovery/removed-*` (default `~/.local/state`). Sync prints the verified recovery location. Restore content, agent links, ownership, and installer metadata without overwriting existing skills:

```sh
just sync-dry-run --restore /absolute/path/to/recovery/removed-XXXX
just sync --restore /absolute/path/to/recovery/removed-XXXX
```

Restore the source directory too before the next normal sync. Explicit `just remove` remains a direct installer action without recovery. Sync does not manage third-party updates.

### Vendored sync engine verification

[`tools/sync_skills.py`](tools/sync_skills.py) is a standalone vendored copy of `vimkim/my-skills/scripts/sync_skills.py`; maintain both copies together. The authoritative engine, public-command tests, and full conflict/recovery documentation are in `my-skills`. Validate byte equality, the old wrapper, and restoration in isolation using:

```bash
python3 ../my-skills/tests/check_vendored_sync.py .
```

Run from this checkout; no live synchronization is part of that check.

---

## Usage

Once installed, invoke skills as slash commands in Claude Code:

```text
/cubrid-worktree CBRD-28099
/cubrid-jira CBRD-25123
/cubrid-pr-create CBRD-26583
/cubrid-ci-analyze https://github.com/CUBRID/cubrid/pull/6864
/cubrid-manual-search What is the default value of max_clients?
/cubrid-performance Make this workload faster; no historical baseline is available
/create-testcases CBRD-26609
```

Skills also trigger automatically based on context.

`cubrid-pr-create` first saves the PR body and resume context in `my-cubrid-docs` for you to read or edit. After you confirm the listed publication steps, it creates a draft PR or updates the existing PR description from that saved body. A detailed explanation is optional.

---

## Prerequisites

Some skills require external CLI tools or runtimes:

| Tool | Required by | Install |
|------|------------|---------|
| `cubrid-worktree` | `cubrid-worktree` | `uv tool install git+https://github.com/vimkim/cubrid-worktree` (or `just install` in `~/gh/cubrid-worktree`) |
| `cubrid-jira` (`cubrid-jira-kanban`) | `cubrid-jira`, `cubrid-jira-kanban-sync` | `uv tool install git+https://github.com/vimkim/cubrid-jira` |
| `cubrid-jira-dup` | `cubrid-jira-dup` | `uv tool install git+https://github.com/vimkim/cubrid-jira-duplicate-poc` |
| `gh` | `cubrid-ci-trigger`, `cubrid-ci-analyze`, `cubrid-pr-create` | [cli.github.com](https://cli.github.com/) |
| `cubrid-ci` | `cubrid-ci-analyze` | `cargo install --path ~/gh/cubrid-ci --locked` |
| `testkit` | `cubrid-test-sql-run`, `cubrid-test-medium-run`, `cubrid-test-shell-run` | Manually install the intended `cubrid-testkit` revision with `go install` |
| JDK 8 + CTP assets | `cubrid-test-sql-run`, `cubrid-test-medium-run` | Use the selected worktree environment's configured installations |
| `work-tracker` | `daily-schedule` (uses external `track-work`) | `just install` in `~/gh/work-tracker` |

---

## License

MIT
