# vimkim's CUBRID context

Load this profile only when the current user is `vimkim`, as established by [Workflow policy](../SKILL.md#workflow-policy). These are personal workflow facts supplied by vimkim. They do not define policy for other users.

For CUBRID work, read `/home/vimkim/my-cubrid/CUBRID.md` once for vimkim's local development and publication policies, including the ticket-first `pwd`-independent worktree and Herdr Space/Tab workflow (`cubrid-worktree`). Current user instructions take precedence.

## CI monitoring

On vimkim's host, the standalone `cubrid-ci-watch` package (`~/gh/cubrid-ci-watch`, installed to `~/.local/bin/cubrid-ci-watch`) runs the shared background poller as user systemd unit `cubrid-ci-watch.service` (per-PR 1/2/4/8/16m backoff, 48h deadline, 10s wakeup; ledger at `~/.local/state/cubrid-ci-watch/watch.sqlite3`). Independently, `hermes-notify.service` (`~/gh/my-cubrid-workflow/automations/hermes-notify`, installed to `~/.local/bin/hermes-notify`) consumes `cubrid-ci-watch` events for **all** tracked requests — both `cubrid-pr-flow`-orchestrated PR runs and standalone `cubrid-ci-watch` registrations — sending kind-routed out-of-session Discord notifications via Hermes (with GitHub Actions run URLs) on the first suite `failure` and on terminal completion (`complete` or `deadline`), and recording terminal verdicts on matching open `work-tracker` items. `cubrid-pr-flow.service` handles PR review/analyze/auto-rerun/AND-join orchestration and delegates its workflow cards through `hermes-notify`. For typical long-running (1–24h) CI runs, register with `cubrid-ci-watch` and return/close the agent session, then inspect `cubrid-ci-watch status` / `cubrid-ci-watch show <id>` in a fresh session when resuming; reserve `cubrid-ci-watch wait` (with `--until required` when waiting on required checks only so optional `sql_by_cci` does not gate) for short in-session autonomous loops.

## Standing CI rerun authorization

`vimkim` grants standing authorization for **at most one automatic `/run rerun <run-id>` per `(PR, head_sha)`** when every guardrail in `cubrid-ci-trigger` holds: zero prior reruns on that head, all failures are `cubrid-tcr` `known` / verified flaky / `found=no` dead shard with no PR defect or unexplained new failure, no `/run rerun` disqualifier, no active run, and any `cubrid-pr-tc-base-check` `stale` exit is solely due to later `develop` commits that keep both PRs `MERGEABLE` without modifying the failing testcases.

`cubrid-pr-flow.service` applies the same 1-per-head cap in the background (`auto_rerun_max_per_head = 1`) and falls back to an `ACT-<N>` confirmation prompt on a second failure or any guardrail miss. Explicit user approval remains required for a 2nd rerun on the same head, any `/run all` or `/run <suite>` retrigger, testcase PR closure or merge, and engine PR merges (engine PR handoffs go through `/cubrid-pr-merge <PR>`).

## Standing review-approval authorization

On 2026-11-25, `vimkim` granted standing review-approval authorization for `cubrid-code-review`: a requested and published PR review whose result is clean submits a formal GitHub `APPROVE` under the conditions in [Approve a clean review](../../cubrid-code-review/references/pr-publication.md#approve-a-clean-review), whatever the author's `/run all` or other CI result. Explicit user approval remains required for any other formal review, including `CHANGES_REQUESTED`, and for merges, CI triggers, and TC PR actions.

## Merge handoff scope

On 2026-11-25, `vimkim` limited final engine PR merges (and their linked `tc/pr-<N>` PRs) to the user-invoked `/cubrid-pr-merge <PR>` skill (`pr-final-merge-handoff`), and only for engine PRs that `vimkim` both opened and is assigned to. A PR that `vimkim` only reviews or approves is merged by its author; `pr-final-merge-handoff` enforces this with an `ownership` blocker that no waiver lifts. Outside `/cubrid-pr-merge`, direct `vimkim` to run `/cubrid-pr-merge <PR>` once reviews and CI are ready rather than proposing manual close/merge steps, requesting ad-hoc merge permission, or running `gh pr merge` directly on an engine PR.

## Interpret team-leader assignment

`hornetmj` is vimkim's development team 2 leader. When a CUBRID issue is assigned to `hornetmj`, the team leader has not yet decided who will implement it.

Treat that issue as awaiting implementer assignment. Do not count it as an implementation commitment for either vimkim or hornetmj, or infer permission to reassign it. Explicit user instructions can authorize investigation or implementation while that assignment remains undecided.

Before recommending work from an issue's assignee, recheck the live issue and any explicit assignment decision. Keep the assignee field unchanged unless the user authorizes an update.
