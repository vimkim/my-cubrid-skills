# my-cubrid-skills

A collection of Claude Code skills for CUBRID database engine development. These skills provide specialized workflows for JIRA integration, PR reviews, CI failure analysis, test creation, and more.

## Skills

| Skill | Description |
|-------|-------------|
| `cubrid-jira` | Look up CUBRID JIRA issue context (CBRD-XXXXX) |
| `cubrid-ci-analyze` | Collect exact-commit CircleCI snapshots with `cubrid-ci` and write failure-analysis reports |
| `cubrid-code-survey` | Compare one CUBRID mechanism with PostgreSQL and MySQL source, then validate narrow runtime questions with focused reversible probes |
| `cubrid-pr-create` | Create GitHub PRs with `[CBRD-XXXXX]` title format and Korean body |
| `cubrid-jira-issue-write` | Write structured JIRA issue reports in Korean |
| `cubrid-manual-search` | Answer CUBRID questions from the local English/Korean RST manual with file-and-line citations |
| `cubrid-oos-context` | Load OOS (Out-of-row Overflow Storage) project context |
| `create-testcases` | Create CUBRID test cases (unit/SQL/shell) for features or bug fixes |
| `schedule-visualizer` | Generate single-file HTML project schedules (daily Excel-like calendar grid + Gantt timeline) from issues, dates, and milestones |
| `track-work` | Register, update, and inspect long-running work in the `work-tracker` ledger so status and context survive agent sessions |
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
/cubrid-pr-create CBRD-26583
/cubrid-ci-analyze https://github.com/CUBRID/cubrid/pull/6864
/cubrid-code-survey How does page-buffer victim selection differ from PostgreSQL and MySQL?
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
| `gh` | `cubrid-pr-create` | [cli.github.com](https://cli.github.com/) |
| `cubrid-ci` | `cubrid-ci-analyze` | `cargo install --path /home/vimkim/gh/cubrid-circleci-analyzer --locked` |
| `work-tracker` | `track-work` | `just install` in `/home/vimkim/gh/work-tracker` |

## License

MIT
