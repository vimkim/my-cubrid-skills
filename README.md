# my-cubrid-skills

A collection of Claude Code skills for CUBRID database engine development. These skills provide specialized workflows for JIRA integration, PR reviews, CI failure analysis, test creation, and more.

## Skills

| Skill | Description |
|-------|-------------|
| `cubrid-jira` | Look up CUBRID JIRA issue context (CBRD-XXXXX) |
| `cubrid-test-sql-run` | Run focused SQL cases with native testkit and verify artifact verdicts |
| `cubrid-test-medium-run` | Run complete medium directories serially with native testkit and verify artifact verdicts |
| `cubrid-test-shell-run` | Run focused shell cases with contained native testkit and verify artifact verdicts |
| `cubrid-ci-analyze` | Collect exact-commit CircleCI snapshots with `cubrid-ci` and write failure-analysis reports |
| `cubrid-pr-create` | Create GitHub PRs with `[CBRD-XXXXX]` title format and Korean body |
| `cubrid-jira-issue-write` | Write structured JIRA issue reports in Korean |
| `cubrid-manual-search` | Answer CUBRID questions from the local English/Korean RST manual with file-and-line citations |
| `cubrid-oos-context` | Load OOS (Out-of-row Overflow Storage) project context |
| `create-testcases` | Create CUBRID test cases (unit/SQL/shell) for features or bug fixes |
| `schedule-visualizer` | Generate single-file HTML project schedules (daily Excel-like calendar grid + Gantt timeline) from issues, dates, and milestones |
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
just install
```

**Managing:**

```bash
just list                # List installed skills
just check               # Check for available updates
just remove cubrid-jira  # Remove a specific skill
```

Run `just reinstall` after source updates. For a rename, remove the legacy installed name explicitly before reinstalling, then use `just list` to verify that the new name exists and the old name is absent.

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
| `gh` | `cubrid-pr-create` | [cli.github.com](https://cli.github.com/) |
| `cubrid-ci` | `cubrid-ci-analyze` | `cargo install --path /home/vimkim/gh/cubrid-circleci-analyzer --locked` |
| `testkit` | `cubrid-test-sql-run`, `cubrid-test-medium-run`, `cubrid-test-shell-run` | Manually install the intended `cubrid-testkit` revision with `go install` |
| JDK 8 + CTP assets | `cubrid-test-sql-run`, `cubrid-test-medium-run` | Use the selected worktree environment's configured installations |
| `work-tracker` | `track-work` | `just install` in `/home/vimkim/gh/work-tracker` |

## License

MIT
