# my-cubrid-skills

## Purpose

- This Git-managed repository is the source collection for CUBRID development skills. General-purpose skills are maintained in `vimkim/my-skills`.
- Skills are installed globally for Claude Code and Codex via the repository `justfile` and `npx skills`.
- Make skill fixes and improvements in this repository first. Do not edit globally installed or generated skill copies.

## Directory structure

Each top-level directory with a `SKILL.md` is a skill (17 remaining in this collection):

- `cubrid-build/` — prepare, build, and test local CUBRID worktrees
- `cubrid-performance/` — diagnose and optimize performance with optional baseline comparisons
- `cubrid-test-sql-run/` — run focused SQL cases locally
- `cubrid-test-medium-run/` — run complete focused medium directories locally
- `cubrid-ci-analyze/` — exact-commit GitHub Actions evidence analysis with `cubrid-ci`
- `cubrid-ci-trigger/` — trigger CUBRID CI suites on GitHub PRs
- `cubrid-pr-create/` — GitHub PR creation with CBRD title format
- `cubrid-pr-merge/` — user-invoked final merge handoff with confirmed squash commit messages
- `cubrid-code-review/` — budgeted CUBRID PR code review with specialists
- `cubrid-jira-issue-write/` — JIRA issue report writer
- `cubrid-manual-search/` — evidence-backed English/Korean CUBRID manual search
- `cubrid-test-shell-run/` — run and debug focused shell tests locally
- `create-testcases/` — CUBRID test case generator
- `cubrid-disk-cleanup/` — `dev2` home disk usage audit, tiered cleanup, and safety guardrails
- `daily-schedule/` — daily/weekly work plan maintenance
- `my-cubrid-skills-create/` — create new skills in this collection
- `cubrid-common/` — shared helper scripts and policy used by CUBRID skills; an internal dependency rather than a user-facing workflow

CLI-bundled skills migrated to their owning repositories (installed via `just install` / `just sync` in each repo):

- `cubrid-jira`, `cubrid-jira-kanban-sync` -> `vimkim/cubrid-jira`
- `cubrid-jira-dup` -> `vimkim/cubrid-jira-duplicate`
- `cubrid-xref` -> `vimkim/cubrid-xref`
- `cubrid-worktree` -> `vimkim/cubrid-worktree`
- `cubrid-qa-fetch` -> `vimkim/cubrid-qahome-fetcher`
- `cubrid-oos-context` -> `vimkim/cubrid-oos-context`
- `workflow-hygiene`, `cubrid-issue-intake`, `cubrid-review-intake` -> `vimkim/my-cubrid-workflow` (`automations/*`)

For `gh-pr-comments-all`, `resolve-greptile-comments`, `markdown-write`, and `track-work`, edit the `skills/<name>/` source in `vimkim/my-skills`. `question-socratically` also moved there and is now disabled under `disabled-skills/`. `daily-schedule` and `my-cubrid-skills-create` remain here. See `docs/general-skills-migration.md` for the coordinated transfer.

The `.agents/`, `.claude/`, and other generated directories created by `npx skills` are not editable sources.

## Updating a skill

1. Edit the skill's `SKILL.md` and any supporting scripts or assets in its source directory.
2. Perform appropriate source-level validation.
3. Complete the Tier 1 workflow below.

## Adding a skill

1. Create a top-level directory named for the new skill.
2. Add a `SKILL.md` with `name` and `description` frontmatter plus its instructions.
3. Add supporting `scripts/`, `assets/`, or reference files when needed.
4. Perform appropriate source-level validation.
5. Complete the Tier 1 workflow below.

## Completion workflow

- `my-cubrid-skills` is a Tier 1 repository (`~/.codex/AGENTS.md` / `~/.claude/CLAUDE.md`). Once validation passes:
  1. Commit only the intended skill changes (preserving unrelated user changes), rebase onto the destination branch (`main`), fast-forward merge with `git merge --ff-only`, and push to its configured remote (`origin`).
  2. From the merged primary checkout, sync the installed skills with `just sync` (which also removes deleted or renamed skills) and verify with `just list`.
  3. Clean up the merged task worktree and local topic branch.
- Tier 1 integration authorizes `just sync` together with merge, push, and cleanup; no separate confirmation is required unless validation fails or rebase/sync encounters an unexpected conflict.
