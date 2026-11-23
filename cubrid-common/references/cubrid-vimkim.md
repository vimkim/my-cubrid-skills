# vimkim's CUBRID context

Load this profile only when the current user is `vimkim`, as established by [Workflow policy](../SKILL.md#workflow-policy). These are personal workflow facts supplied by vimkim. They do not define policy for other users.

For CUBRID work, read `/home/vimkim/my-cubrid/CUBRID.md` once for vimkim's local development and publication policies, including the ticket-first `pwd`-independent worktree and Herdr Space/Tab workflow (`cubrid-worktree`). Current user instructions take precedence.

## CI monitoring and delivery

On vimkim's host, `my-cubrid-hermes` runs the shared `cubrid-ci-watch` collector (`cubrid-hermes-*-watcher.service`) and the `cubrid-briefing` delivery bridge (Discord and explicitly bound Herdr agents). Use `cubrid-ci-watch wait` when waiting inside the current session, and `cubrid-briefing bind` when out-of-session Discord or Herdr alerts are desired.

## Interpret team-leader assignment

`hornetmj` is vimkim's development team 2 leader. When a CUBRID issue is assigned to `hornetmj`, the team leader has not yet decided who will implement it.

Treat that issue as awaiting implementer assignment. Do not count it as an implementation commitment for either vimkim or hornetmj, or infer permission to reassign it. Explicit user instructions can authorize investigation or implementation while that assignment remains undecided.

Before recommending work from an issue's assignee, recheck the live issue and any explicit assignment decision. Keep the assignee field unchanged unless the user authorizes an update.
