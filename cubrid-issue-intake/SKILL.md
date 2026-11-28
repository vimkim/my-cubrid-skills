---
name: cubrid-issue-intake
description: "Select and start a Confirmed CUBRID JIRA issue through the two-stage confirmed-issue-flow workflow: Stage 1 writes a brief, a local reproduction, and plan.md without code edits; Stage 2 implements the approved plan and hands the Draft PR to cubrid-pr-flow. Use when choosing the next Confirmed issue to work on, starting a Confirmed CBRD issue, reviewing its plan.md, or moving it to implementation. Triggers on phrases like 'pick a confirmed issue', 'start CBRD-XXXXX from Confirmed', 'intake CBRD-XXXXX', 'implement the approved plan', 'Confirmed 이슈 골라줘', '이슈 인테이크'."
argument-hint: "[CBRD-XXXXX]"
---

# CUBRID Issue Intake

Move one `Confirmed` JIRA issue through two stages with `confirmed-issue-flow`. Stage 1 analyzes, reproduces, and plans. Stage 2 starts only after the user approves `plan.md`.

Take an optional `CBRD-XXXXX` key from `$ARGUMENTS`. If there is no key, start at step 2.

## 1. Preflight

```bash
command -v confirmed-issue-flow cubrid-jira cubrid-worktree hss work-tracker
confirmed-issue-flow --help
```

If `confirmed-issue-flow` is missing, stop. Tell the user to run `just sync` in `~/gh/my-cubrid-workflow/automations/confirmed-issue-flow`. Read [Workflow policy](../cubrid-common/SKILL.md#workflow-policy) before you interpret assignees.

## 2. Select an issue

```bash
confirmed-issue-flow list --json
```

Show each issue with its key, summary, priority, assignee, and local state (worktree, Herdr workspace, PR, and tracker item). Recommend issues that are assigned to the user and have no local state.

`hornetmj` assignment means that the issue waits for the team leader to assign an implementer. Do not start such an issue. `intake` refuses it. Pass `--allow-unassigned` only when the user explicitly authorizes that ticket in this session.

## 3. Stage 1: intake

Preview, then run:

```bash
confirmed-issue-flow intake <TICKET> --dry-run --json
confirmed-issue-flow intake <TICKET> --json
```

Intake does these steps:

1. It creates or reuses the worktree `~/gh/cb/<TICKET>`.
2. It adds a work-tracker item. The item is `pending` when 5 items are already active.
3. It writes `stage1-brief.md`.
4. It starts a Herdr worker (`hss ensure`) and sends the Stage 1 prompt to the worker.

The worker analyzes the cause and reproduces it locally. Then it writes `plan.md` and stops before it edits code, pushes, or creates a PR. The files go in `${XDG_STATE_HOME:-~/.local/state}/confirmed-issue-flow/<TICKET>/`.

Useful options:

- `--base <ref>` sets the worktree base.
- `--launcher <name>` selects the agent (`ai-agent`, `codex`, `claude`, `shell`, and others).

Use `--auto-pr` only when the user asks to skip the plan review. It runs Stage 2 without a pause.

## 4. Review plan.md with the user

```bash
confirmed-issue-flow status <TICKET> --json
```

When `plan_exists` is `true`, read `plan.md` and show the user:

- The reproduction result.
- The files and functions that will change.
- The risks: locking, recovery, and compatibility.
- The test plan.

If the plan has gaps (no reproduction, no test plan, or scope that is too wide), tell the user, and ask the worker to revise the plan through Herdr. Do not start Stage 2 until the user explicitly approves the plan in this session.

## 5. Stage 2: implement

Preview, then run:

```bash
confirmed-issue-flow implement <TICKET> --dry-run --json
confirmed-issue-flow implement <TICKET> --json
```

The worker implements the plan, builds and tests it, and creates a Draft PR through [`cubrid-pr-create`](../cubrid-pr-create/SKILL.md). Then it calls `cubrid-pr-flow start --pr <N> --ticket <TICKET> --json` for review and CI orchestration.

Add `--transition-jira` only when the user agrees to move the JIRA issue. It moves the issue to `Develop` by default, or to the status in `--jira-to <status>`. The JIRA transition is a write to an external service. Show the dry-run transition before you run it live.

## 6. Monitor

```bash
confirmed-issue-flow status [<TICKET>] --json
confirmed-issue-flow watch
```

`status` shows the stage files, the worktree, the Herdr worker, and the PR state for one ticket or all tickets. `watch` follows the progress of the tickets. Run `confirmed-issue-flow watch --help` first. If the installed version does not have `watch`, run `status` again.

## 7. Report

Report the following:

- The ticket and the stage that it reached.
- The worktree, brief, and plan paths.
- The Herdr worker.
- The JIRA transition, if one ran.
- The PR link and the `cubrid-pr-flow` state, when the PR exists.
