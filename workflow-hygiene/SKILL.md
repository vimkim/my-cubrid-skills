---
name: workflow-hygiene
description: "Check and clean the dev2 workflow environment with workflow-watchdog: daemon and timer health, orphan worktrees, stale backlog, and disk pressure. Apply only safe Tier 1 cleanups without asking; ask before Tier 2, disk cleanup, or backlog cancellation. Use for server hygiene, a daemon health check, an orphan worktree sweep, a disk check, or the morning ops digest. Triggers on phrases like 'server hygiene', 'check daemon health', 'orphan worktrees', 'disk check', 'morning ops digest', '서버 상태 점검', '워크트리 정리'."
argument-hint: "[check|cleanup|digest|timer]"
---

# Workflow Hygiene

Check the health of the local workflow automation with `workflow-watchdog`. Clean up only what the tool marks as safe. Escalate everything else to the user.

Take an optional mode from `$ARGUMENTS`: `check`, `cleanup`, `digest`, or `timer`. If there is no mode, run steps 1 to 4 in order.

## 1. Preflight

```bash
command -v workflow-watchdog
workflow-watchdog --help
```

If `workflow-watchdog` is missing, stop. Tell the user to run `just sync` in `~/gh/my-cubrid-workflow/automations/workflow-watchdog`. Before you use a flag in this skill, make sure that `--help` shows it.

## 2. Check

```bash
workflow-watchdog check --json
```

Report each finding: its category (for example daemons, timers, worktrees, disk, backlog), severity, subject, and suggested action. A finding with severity `ok` needs no action. Do not repair daemons or timers by hand from this step. Use step 5 for timer controls, and report other daemon failures with the log path or command from the finding.

## 3. Preview cleanup

```bash
workflow-watchdog cleanup --dry-run --json
```

Put each proposed action into one of these groups, as the tool classifies it:

| Group | Examples | Rule |
|---|---|---|
| Tier 1 (safe) | merged or orphan worktrees with no local changes, stale lock or pid files, expired caches | Apply in step 4 without a separate confirmation |
| Tier 2 | worktrees with local changes or unpushed commits, branches, install prefixes, anything the tool marks `confirm` | Ask the user first |
| Disk pressure | low free space on `/home` or a data volume | Hand off to [`cubrid-disk-cleanup`](../cubrid-disk-cleanup/SKILL.md) after the user agrees |
| `STALE_BACKLOG` | work-tracker items with no progress past the threshold | Ask the user for each item before you cancel it |

If the tool reports a group that this table does not show, treat it as Tier 2.

## 4. Apply

1. Apply only the Tier 1 actions from the preview:

   ```bash
   workflow-watchdog cleanup --apply --json
   ```

   If the tool takes a tier filter (see `--help`), limit the call to Tier 1. If the apply output contains an action that the dry run did not show, stop and report it.
2. Show the Tier 2 actions with their paths and reasons. Apply each one only after the user confirms it explicitly in this session. Use the tool's per-item or tier option for this.
3. For disk pressure, ask the user. On a yes, run [`cubrid-disk-cleanup`](../cubrid-disk-cleanup/SKILL.md), which has its own approval tiers.
4. For `STALE_BACKLOG`, show each item (id, title, last update, workdir). Cancel only the items that the user names, with `work-tracker status <id> cancelled --note "<reason>"` or the watchdog's cancel option.
5. Run `workflow-watchdog check --json` again and report what changed.

## 5. Digest and timer

Preview the morning ops digest. Send it only when the user asks:

```bash
workflow-watchdog digest --dry-run
workflow-watchdog digest --send
```

Control the systemd user timer through the automation's `justfile`:

```bash
just -d ~/gh/my-cubrid-workflow/automations/workflow-watchdog status
just -d ~/gh/my-cubrid-workflow/automations/workflow-watchdog up
just -d ~/gh/my-cubrid-workflow/automations/workflow-watchdog logs
```

Use `status` to see the timer state and the last run, `up` to install or restart the timer, and `logs` to read recent output.

## 6. Report

Report the following:

- The findings from the check.
- The Tier 1 actions that you applied.
- The Tier 2, disk, and backlog actions that you applied or skipped, and the reason for each.
- The timer state.
- The remaining findings.
