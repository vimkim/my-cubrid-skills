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

### Option 1: `npx skills` (recommended)

Uses the [`skills`](https://github.com/vercel-labs/skills) CLI to install and manage skills with automatic symlinks.

```bash
# Global — available in all projects (~/.claude/skills/)
npx skills add vimkim/my-cubrid-skills --global

# Project-local — current project only (.claude/skills/)
npx skills add vimkim/my-cubrid-skills

# Install specific skills only
npx skills add vimkim/my-cubrid-skills --skill jira --skill cubrid-pr-review

# Copy files instead of symlink
npx skills add vimkim/my-cubrid-skills --copy
```

**Updating** (picks up renames, new skills, removals):

```bash
npx skills update        # Update all installed skills
npx skills check         # Check for available updates
```

**Managing:**

```bash
npx skills list          # List installed skills
npx skills remove jira   # Remove a specific skill
```

Since `npx skills` uses symlinks by default, renamed or updated skills sync automatically when you `git pull` the source repo. Use `npx skills update` to re-sync if needed.

### Option 2: Manual symlinks

**Global** (all projects):

```bash
git clone https://github.com/vimkim/my-cubrid-skills.git ~/my-cubrid-skills

mkdir -p ~/.claude/skills
for skill in ~/my-cubrid-skills/*/; do
  name=$(basename "$skill")
  [ -f "$skill/SKILL.md" ] && ln -sf "$skill" ~/.claude/skills/"$name"
done
```

**Project-local** (single project):

```bash
cd /path/to/your/cubrid-project

mkdir -p .claude/skills
for skill in ~/my-cubrid-skills/*/; do
  name=$(basename "$skill")
  [ -f "$skill/SKILL.md" ] && ln -sf "$skill" .claude/skills/"$name"
done
```

Add `.claude/skills/` to `.gitignore` if you don't want to share with the team.

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
