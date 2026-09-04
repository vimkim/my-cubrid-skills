# my-cubrid-skills

## Purpose

- This Git-managed repository is the single source of truth (SSOT) for the user's skills, especially skills used in their work as a CUBRID DBMS researcher and engineer.
- Skills are installed globally for Claude Code and Codex via the repository `justfile` and `npx skills`.
- Make skill fixes and improvements in this repository first. Do not edit globally installed or generated skill copies.

## Directory structure

Each top-level directory with a `SKILL.md` is a skill:

- `cubrid-jira/` — CUBRID JIRA issue lookup
- `cubrid-build/` — prepare, build, and test local CUBRID worktrees
- `cubrid-ci-analyze/` — exact-commit CircleCI snapshot and failure analysis with `cubrid-ci`
- `cubrid-ci-trigger/` — trigger CUBRID CI suites on GitHub PRs
- `cubrid-code-survey/` — concise PostgreSQL/MySQL source surveys with focused reversible CUBRID runtime probes
- `cubrid-isolation-test/` — create and run CUBRID concurrency and MVCC isolation tests
- `cubrid-pr-create/` — GitHub PR creation with CBRD title format
- `cubrid-jira-issue-write/` — JIRA issue report writer
- `cubrid-manual-search/` — evidence-backed English/Korean CUBRID manual search
- `cubrid-oos-context/` — OOS project context loader
- `cubrid-qa-fetch/` — authenticated CUBRID internal QA result retrieval and analysis
- `cubrid-shell-run/` — run and debug focused CTP shell tests locally
- `create-testcases/` — CUBRID test case generator
- `gh-pr-comments-all/` — fetch and merge all GitHub PR comment types
- `my-cubrid-skills-create/` — create new skills in this collection
- `resolve-greptile-comments/` — resolve replied Greptile review threads
- `schedule-visualizer/` — single-file HTML schedule generator with templates in `assets/` and a `verify_html.sh` check
- `track-work/` — register, update, and inspect long-running work in the `work-tracker` ledger across agent sessions
- `cubrid-common/` — shared helper scripts used by CUBRID skills; an internal dependency rather than a user-facing workflow

The `.agents/`, `.claude/`, and other generated directories created by `npx skills` are not editable sources.

## Updating a skill

1. Edit the skill's `SKILL.md` and any supporting scripts or assets in its source directory.
2. Perform appropriate source-level validation.
3. Ask the user for confirmation before the completion workflow below.

## Adding a skill

1. Create a top-level directory named for the new skill.
2. Add a `SKILL.md` with `name` and `description` frontmatter plus its instructions.
3. Add supporting `scripts/`, `assets/`, or reference files when needed.
4. Perform appropriate source-level validation.
5. Ask the user for confirmation before the completion workflow below.

## Completion workflow

- After finishing and verifying any skill change, ask the user whether to:
  1. reinstall the skills with `just reinstall`, and
  2. commit and push the repository changes.
- Run those publication steps only after the user explicitly confirms (for example, `yes`).
- After reinstalling, verify the installed skills with `just list`.
- Before committing, preserve unrelated user changes and include only the intended skill work.
