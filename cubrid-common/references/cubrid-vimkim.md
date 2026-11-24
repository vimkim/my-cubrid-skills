# vimkim's CUBRID context

Load this profile only when the current user is `vimkim`, as established by [Workflow policy](../SKILL.md#workflow-policy). These are personal workflow facts supplied by vimkim. They do not define policy for other users.

For CUBRID work, read `/home/vimkim/my-cubrid/CUBRID.md` once for vimkim's local development and publication policies, including the ticket-first `pwd`-independent worktree and Herdr Space/Tab workflow (`cubrid-worktree`). Current user instructions take precedence.

## CI monitoring

On vimkim's host, the standalone `cubrid-ci-watch` package (`~/gh/cubrid-ci-watch`, installed to `~/.local/bin/cubrid-ci-watch`) runs the shared background poller as user systemd unit `cubrid-ci-watch.service` (per-PR 1/2/4/8/16m backoff, 48h deadline, 10s wakeup; ledger at `~/.local/state/cubrid-ci-watch/watch.sqlite3`). Check poller and active request state with `cubrid-ci-watch status` (or `just status` in `~/gh/cubrid-ci-watch`), and use `cubrid-ci-watch wait` when waiting inside the current session. No separate out-of-session notification bridge (`my-cubrid-hermes` / `cubrid-briefing`) is active.

## Interpret team-leader assignment

`hornetmj` is vimkim's development team 2 leader. When a CUBRID issue is assigned to `hornetmj`, the team leader has not yet decided who will implement it.

Treat that issue as awaiting implementer assignment. Do not count it as an implementation commitment for either vimkim or hornetmj, or infer permission to reassign it. Explicit user instructions can authorize investigation or implementation while that assignment remains undecided.

Before recommending work from an issue's assignee, recheck the live issue and any explicit assignment decision. Keep the assignee field unchanged unless the user authorizes an update.
