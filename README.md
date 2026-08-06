# my-cubrid-skills

A collection of Claude Code skills for CUBRID database engine development. These skills provide specialized workflows for JIRA integration, PR reviews, CI failure analysis, test creation, and more.

## Skills

| Skill | Description |
|-------|-------------|
| `cubrid-jira` | Look up CUBRID JIRA issue context (CBRD-XXXXX) |
| `cubrid-ci-analyze` | Collect exact-commit CircleCI snapshots with `cubrid-ci` and write failure-analysis reports |
| `cubrid-code-analysis-report` | Create a source-traceable Korean CUBRID subsystem book with PostgreSQL/MySQL comparison, runtime experiments, reproducible quizzes, and adaptive grilling |
| `cubrid-pr-review` | Review the CUBRID PR at the current worktree HEAD using Claude Code `/code-review` or Codex `/review`, plus CUBRID-specific validation |
| `cubrid-pr-create` | Create GitHub PRs with `[CBRD-XXXXX]` title format and Korean body |
| `cubrid-jira-issue-write` | Write structured JIRA issue reports in Korean |
| `cubrid-manual-search` | Answer CUBRID questions from the local English/Korean RST manual with file-and-line citations |
| `cubrid-oos-context` | Load OOS (Out-of-row Overflow Storage) project context |
| `create-testcases` | Create CUBRID test cases (unit/SQL/shell) for features or bug fixes |
| `schedule-visualizer` | Generate single-file HTML project schedules (daily Excel-like calendar grid + Gantt timeline) from issues, dates, and milestones |
| `cubrid-common` | Shared helper scripts used internally by other CUBRID skills |

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
just install
```

**Managing:**

```bash
just list                # List installed skills
just check               # Check for available updates
just remove cubrid-jira  # Remove a specific skill
```

Since `npx skills` uses symlinks by default, renamed or updated skills sync automatically when you `git pull` the source repo.

## Usage

Once installed, invoke skills as slash commands in Claude Code:

```
/cubrid-jira CBRD-25123
/cubrid-pr-review https://github.com/CUBRID/cubrid/pull/6950
/cubrid-pr-create CBRD-26583
/cubrid-ci-analyze https://github.com/CUBRID/cubrid/pull/6864
/cubrid-code-analysis-report page buffer
/cubrid-manual-search What is the default value of max_clients?
/create-testcases CBRD-26609
```

Skills also trigger automatically based on context (e.g., pasting a CUBRID PR URL triggers `cubrid-pr-review`).

## Prerequisites

Some skills require external tools:

| Tool | Required by | Install |
|------|------------|---------|
| `cubrid-jira` | `cubrid-jira`, `cubrid-pr-review` | `uv tool install git+https://github.com/vimkim/cubrid-jira` |
| `gh` | `cubrid-pr-review`, `cubrid-pr-create` | [cli.github.com](https://cli.github.com/) |
| `cubrid-ci` | `cubrid-ci-analyze` | `cargo install --path /home/vimkim/gh/cubrid-circleci-analyzer --locked` |
| `clangd` | `cubrid-pr-review` (LSP analysis) | System package manager |

## License

MIT
