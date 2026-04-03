# my-cubrid-skills

A collection of Claude Code skills for CUBRID database engine development. These skills provide specialized workflows for JIRA integration, PR reviews, CI failure analysis, test creation, and more.

## Skills

| Skill | Description |
|-------|-------------|
| `jira` | Look up CUBRID JIRA issue context (CBRD-XXXXX) |
| `analyze-ci-failures` | Analyze CircleCI shell test failures with root cause categorization |
| `cubrid-pr-review` | Deep C/C++ PR code review with LSP/clangd analysis (3 parallel agents) |
| `cubrid-pr-create` | Create GitHub PRs with `[CBRD-XXXXX]` title format and Korean body |
| `cubrid-jira-issue-write` | Write structured JIRA issue reports in Korean |
| `cubrid-manual` | Search the CUBRID manual (RST docs) for SQL syntax, config, APIs |
| `cubrid-oos-context` | Load OOS (Out-of-row Overflow Storage) project context |
| `create-testcases` | Create CUBRID test cases (unit/SQL/shell) for features or bug fixes |

## Installation

### Using `npx skills`

Uses the [`skills`](https://github.com/vercel-labs/skills) CLI to install globally to `~/.claude/skills/`.

```bash
npx skills add vimkim/my-cubrid-skills -y -g
```

Or clone locally and use the justfile:

```bash
git clone https://github.com/vimkim/my-cubrid-skills.git ~/temp/my-cubrid-skills
cd ~/temp/my-cubrid-skills
just install
```

**Managing:**

```bash
just list                # List installed skills
just check               # Check for available updates
just remove jira         # Remove a specific skill
```

Since `npx skills` uses symlinks by default, renamed or updated skills sync automatically when you `git pull` the source repo.

## Usage

Once installed, invoke skills as slash commands in Claude Code:

```
/jira CBRD-25123
/cubrid-pr-review https://github.com/CUBRID/cubrid/pull/6950
/cubrid-pr-create CBRD-26583
/analyze-ci-failures
/cubrid-manual
/create-testcases CBRD-26609
```

Skills also trigger automatically based on context (e.g., pasting a CUBRID PR URL triggers `cubrid-pr-review`).

## Prerequisites

Some skills require external tools:

| Tool | Required by | Install |
|------|------------|---------|
| `uv` | `jira`, `cubrid-oos-context` | [docs.astral.sh/uv](https://docs.astral.sh/uv/getting-started/installation/) |
| `cubrid-jira-search` | `jira`, `cubrid-pr-review` | `uv tool install cubrid-jira-fetcher` |
| `cubrid-oos-search` | `cubrid-oos-context` | `uv tool install cubrid-oos-search` |
| `gh` | `cubrid-pr-review`, `cubrid-pr-create`, `analyze-ci-failures` | [cli.github.com](https://cli.github.com/) |
| `clangd` | `cubrid-pr-review` (LSP analysis) | System package manager |

## License

MIT
