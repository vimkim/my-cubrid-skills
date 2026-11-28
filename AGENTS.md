# my-cubrid-skills

## Purpose

- This Git-managed repository is the source collection for CUBRID development skills. General-purpose skills are maintained in `vimkim/my-skills`.
- Skills are installed globally for Claude Code and Codex via the repository `justfile` and `npx skills`.
- Make skill fixes and improvements in this repository first. Do not edit globally installed or generated skill copies.

## Directory structure

Each top-level directory with a `SKILL.md` is a skill:

- `cubrid-jira/` — CUBRID JIRA issue lookup
- `cubrid-xref/` — bidirectional CUBRID PR ↔ JIRA issue lookup and caching
- `cubrid-worktree/` — ticket-first CUBRID worktree and Herdr Space/Tab setup
- `cubrid-build/` — prepare, build, and test local CUBRID worktrees
- `cubrid-performance/` — diagnose and optimize performance with optional baseline comparisons
- `cubrid-test-sql-run/` — run focused SQL cases locally
- `cubrid-test-medium-run/` — run complete focused medium directories locally
- `cubrid-ci-analyze/` — exact-commit GitHub Actions evidence analysis with `cubrid-ci`
- `cubrid-ci-trigger/` — trigger CUBRID CI suites on GitHub PRs
- `cubrid-pr-create/` — GitHub PR creation with CBRD title format
- `cubrid-pr-merge/` — user-invoked final merge handoff with confirmed squash commit messages
- `cubrid-jira-issue-write/` — JIRA issue report writer
- `cubrid-jira-kanban-sync/` — sync personal JIRA kanban issue statuses with GitHub PR, review, and CI state
- `cubrid-jira-dup/` — duplicate-candidate check before a JIRA write
- `cubrid-manual-search/` — evidence-backed English/Korean CUBRID manual search
- `cubrid-oos-context/` — OOS project context loader
- `cubrid-qa-fetch/` — authenticated CUBRID internal QA result retrieval and analysis
- `cubrid-test-shell-run/` — run and debug focused shell tests locally
- `create-testcases/` — CUBRID test case generator
- `cubrid-disk-cleanup/` — `dev2` home disk usage audit, tiered cleanup, and safety guardrails
- `workflow-hygiene/` — `workflow-watchdog` health check, safe Tier 1 cleanup, ops digest, and timer controls
- `cubrid-review-intake/` — assigned PR review intake with `cubrid-review-flow`, approval-gated posting, and review worktree cleanup
- `cubrid-issue-intake/` — two-stage `Confirmed` JIRA issue intake and implementation with `confirmed-issue-flow`
- `my-cubrid-skills-create/` — create new skills in this collection
- `cubrid-common/` — shared helper scripts used by CUBRID skills; an internal dependency rather than a user-facing workflow

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
