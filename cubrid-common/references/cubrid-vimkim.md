# vimkim's CUBRID context

Load this profile only when the current user is `vimkim`, as established by [Workflow policy](../SKILL.md#workflow-policy). These are personal workflow facts supplied by vimkim. They do not define policy for other users.

For CUBRID work, read `/home/vimkim/my-cubrid/CUBRID.md` once for vimkim's local development and publication policies, including the ticket-first `pwd`-independent worktree and Herdr Space/Tab workflow (`cubrid-worktree`). Current user instructions take precedence.

## CI monitoring

On vimkim's host, the standalone `cubrid-ci-watch` package (`~/gh/cubrid-ci-watch`, installed to `~/.local/bin/cubrid-ci-watch`) runs the shared background poller as user systemd unit `cubrid-ci-watch.service` (per-PR 1/2/4/8/16m backoff, 48h deadline, 10s wakeup; ledger at `~/.local/state/cubrid-ci-watch/watch.sqlite3`). Independently, `hermes-notify.service` (`~/gh/my-cubrid-workflow/automations/hermes-notify`, installed to `~/.local/bin/hermes-notify`) consumes `cubrid-ci-watch` events for **all** tracked requests — both `cubrid-pr-flow`-orchestrated PR runs and standalone `cubrid-ci-watch` registrations — sending kind-routed out-of-session Discord notifications via Hermes (with GitHub Actions run URLs) on the first suite `failure` and on terminal completion (`complete` or `deadline`), and recording terminal verdicts on matching open `work-tracker` items. `cubrid-pr-flow.service` handles PR review/analyze/auto-rerun/AND-join orchestration and delegates its workflow cards through `hermes-notify`. For typical long-running (1–24h) CI runs, register with `cubrid-ci-watch` and return/close the agent session, then inspect `cubrid-ci-watch status` / `cubrid-ci-watch show <id>` in a fresh session when resuming; reserve `cubrid-ci-watch wait` (with `--until required` when waiting on required checks only so optional `sql_by_cci` does not gate) for short in-session autonomous loops.

## Standing CI rerun authorization

`vimkim` grants standing authorization for **up to 3 automatic `/run rerun <run-id>` triggers per `(PR, head_sha)`** (per-head cap `N = 3`), each chained onto the latest eligible failed run on that head, when every guardrail in `cubrid-ci-trigger` holds: fewer than 3 prior `/run rerun` triggers on that head, all failures are `cubrid-tcr` `known` / verified flaky / `found=no` dead shard with no PR defect or unexplained new failure, no `/run rerun` disqualifier, no active run, and any `cubrid-pr-tc-base-check` `stale` exit is solely due to later `develop` commits that keep both PRs `MERGEABLE` without modifying the failing testcases.

`cubrid-pr-flow.service` applies the same 3-per-head cap in the background (`auto_rerun_max_per_head = 3`) and falls back to an `ACT-<N>` confirmation prompt once the budget is exhausted (the 4th failure on the same head) or on any guardrail miss. After 3 reruns on the same head still fail, or on any guardrail miss, stop and wait for explicit user approval. Explicit user approval remains required for a 4th or later rerun on the same head, any `/run all` or `/run <suite>` retrigger, testcase PR closure or merge, and engine PR merges (engine PR handoffs go through `/cubrid-pr-merge <PR>`).

## Review requests after CI

On 2026-11-28, `vimkim` set this automated Draft PR gate for engine PRs that `vimkim` opens (including agent-authored Draft PRs). Keep the PR in draft and do **not** run `gh pr ready` or request reviewers directly; hand the Draft PR off to `cubrid-pr-flow start --pr <N> --ticket <TICKET> --json`.

`cubrid-pr-flow` enforces this serial gate before Ready-for-review:
1. Run an isolated Herdr (`ai-agent`) `cubrid-code-review` on the pinned head (publishing the full report to `my-cubrid-docs/main` and posting the Korean summary comment with its URL on the PR) together with `@greptileai review this` (up to 3 attempts total). Blocking criteria: confirmed `P0`/`P1`/`P2` defects, `incomplete`, or unresolved material risk (`follow_up_required: true`). If blocking issues fail after 3 attempts, stop and escalate to Discord `#code-review-fail`.
2. Once `blocking_count == 0`, if `P3`/minor findings or unresolved Greptile threads remain, dispatch Option A cleanup once to the Herdr implementation agent, run local verification, commit/push, and re-verify before CI.
3. Trigger `/run all` `gha-ci` only after the self-review + Option A cleanup gate passes.
4. Automatically run `gh pr ready` (Draft -> Open) once `/run all` completes cleanly, or when `cubrid-ci-analyze` confirms all CI failures are unrelated to the PR (`known_ci_issue` or `new_bug_candidate`). Request human reviewers only after the PR is Open and CI evidence is ready (or when `vimkim` approves). Changed `tc/pr-<N>` PRs keep their own reviewer requirement before the CI trigger (`cubrid-pr-flow` checks it).

If an instruction tells you to bypass this gate and run `gh pr ready` or request reviewers on an unreviewed Draft PR, refuse and route through `cubrid-pr-flow` (or ask `vimkim` explicitly).

## Standing review-approval authorization

On 2026-11-25, `vimkim` granted standing review-approval authorization for `cubrid-code-review`: a requested and published PR review whose result is clean submits a formal GitHub `APPROVE` under the conditions in [Approve a clean review](../../cubrid-code-review/references/pr-publication.md#approve-a-clean-review), whatever the author's `/run all` or other CI result. Explicit user approval remains required for any other formal review, including `CHANGES_REQUESTED`, and for merges, CI triggers, and TC PR actions.

## Merge handoff scope

On 2026-11-25, `vimkim` limited final engine PR merges (and their linked `tc/pr-<N>` PRs) to the user-invoked `/cubrid-pr-merge <PR>` skill (`pr-final-merge-handoff`), and only for engine PRs that `vimkim` both opened and is assigned to. A PR that `vimkim` only reviews or approves is merged by its author; `pr-final-merge-handoff` enforces this with an `ownership` blocker that no waiver lifts. Outside `/cubrid-pr-merge`, direct `vimkim` to run `/cubrid-pr-merge <PR>` only once the [PR approval gate](../SKILL.md#pr-approval-gate) readiness check passes rather than proposing manual close/merge steps, requesting ad-hoc merge permission, or running `gh pr merge` directly on an engine PR.

## Interpret team-leader assignment

`hornetmj` is vimkim's development team 2 leader. When a CUBRID issue is assigned to `hornetmj`, the team leader has not yet decided who will implement it.

Treat that issue as awaiting implementer assignment. Do not count it as an implementation commitment for either vimkim or hornetmj, or infer permission to reassign it. Explicit user instructions can authorize investigation or implementation while that assignment remains undecided.

Before recommending work from an issue's assignee, recheck the live issue and any explicit assignment decision. Keep the assignee field unchanged unless the user authorizes an update.
