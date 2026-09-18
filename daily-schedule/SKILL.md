---
name: daily-schedule
description: Maintain and answer the user's daily and weekly work plan from the todays-schedule control sheets, the work-tracker ledger, and live GitHub/CI state. Use when the user asks what to do today or next, hands over a daily or weekly plan to track, reports progress on planned items, or wants an end-of-day or end-of-week wrap-up. Triggers on phrases like 'what should I do today', '오늘 뭐 하지', '다음은?', 'what did I plan last week', '지난주에 뭐 하기로 했지', '차주 계획', 'track my schedule', 'wrap up today'.
---

# Daily Schedule

Schedule home: `/home/vimkim/temp/todays-schedule/` (a git repository; leave files untracked unless the user asks to commit).

File conventions inside the schedule home:

- `YYYY-MM-DD-raw-prompt*.md` — the user's verbatim plan dump, saved unedited.
- `week-YYYY-MM-DD.md` — weekly control sheet, named by the Monday of the week it covers.
- `today-YYYY-MM-DD.md` — daily control sheet.

Control sheets state facts with a snapshot date. Snapshots are stale by definition: before recommending any PR-, CI-, or JIRA-related action, re-query the live source.

## 1. Establish current state (every invocation)

1. Get the real time: `date '+%Y-%m-%d %H:%M %Z (%A)'`. Note remaining working hours and upcoming Korean holidays the sheets mention.
2. Read the newest `week-*.md` whose date is ≤ today, and today's `today-YYYY-MM-DD.md` if it exists.
3. Read the ledger: `work-tracker today --json` (fall back to `work-tracker list --json` for the open backlog). If `work-tracker` is missing, say so and continue from the sheets alone. Follow the `track-work` skill for all ledger mutations.
4. Detect work already done today by other sessions: `git -C /home/vimkim/gh/my-cubrid-docs log --oneline --since=midnight` — agents commit evidence reports there.
5. For every candidate next action that references a PR or CI, re-check live state, e.g. `gh pr view <n> --repo CUBRID/cubrid --json state,isDraft,reviewDecision,mergeStateStatus` and `gh pr checks <n> --repo CUBRID/cubrid`.

## 2. Answer "what should I do today / what's next"

1. On the first ask of a day, create `today-YYYY-MM-DD.md` from the governing week sheet, the ledger, and live state: working window, per-item status and next action, a 운영 규칙 header (like `week-2026-09-21.md`), and a 진행 로그 section. Carry unfinished items forward from the previous today-sheet.
2. Recommend one most important next action with a timebox. Offer one fallback only if the primary is blocked. Do not enumerate the whole backlog unless asked.
3. Prefer actions that unblock people or long-running machines first: review requests, QA data requests, and CI triggers go out before deep solo work, especially before weekends and holidays.
4. Append the recommendation to the today sheet's 진행 로그.

## 3. Record progress

When the user reports an item done, blocked, or deferred: update the today sheet immediately, and mirror the change into work-tracker (`work-tracker status <ID> ... --note "..."` or `work-tracker note <ID> "..."`). Never mark an item done from assumption; require the user's word or verified evidence (merged PR, green CI, committed report).

## 4. End of day ("wrap up", "퇴근")

1. Update the today sheet: check off completed items, write a short outcome summary, list carried-over items with their blockers.
2. Add work-tracker notes to every item touched today; move statuses to `waiting`/`blocked` where accurate.
3. Report to the user: what got done, what carries over, and the single first action for the next working day.

## 5. Weekly plan intake (the user pastes a plan, "차주 계획")

1. Save the plan verbatim as `YYYY-MM-DD-raw-prompt*.md`.
2. Build `week-YYYY-MM-DD.md`: calendar notes (holidays shrink the real working days — say so), one section per item with JIRA/PR links, a date-stamped live-state snapshot, concrete next actions, and related work-tracker item IDs.
3. Register a work-tracker umbrella item whose description points at the week sheet; register new items for objectives not yet tracked; add cross-reference notes to existing related items instead of creating duplicates.
4. Verify the plan's premises against live state before accepting them — an item may already be further along than the user thinks (for example, a "get review" item whose PR is already approved). Report such corrections.
5. Close with sequencing advice: name the long-pole item to start first and any people-dependent request to send before the next holiday or weekend.

## Edge cases

- No week sheet covers today: build the day plan from work-tracker plus live PRs, and tell the user a weekly plan is missing.
- Sheet and ledger disagree: the ledger wins for status, the sheet wins for intent; reconcile both and note the correction.
- Today is past the governing week sheet's range: answer from what exists, then prompt the user for the next weekly plan.
