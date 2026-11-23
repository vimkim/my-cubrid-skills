# Monitor requests with cubrid-ci-watch

Use `cubrid-ci-watch` from `my-cubrid/bin`. The Python CLI owns durable request state, shared polling, deadlines, and replayable JSON events. It consumes `cubrid-pr-status --json --history 0` and read-only GitHub metadata. Use the installed command or `~/my-cubrid/bin/cubrid-ci-watch`. Read its `--help` and `docs/cubrid-ci-watch/README.md` in the `my-cubrid` checkout for the current CLI contract.

## Register the original request

Register after the trigger and pickup check. Preserve the original trigger time, exact head SHA, receipt, and selected suites even if no run has appeared:

```bash
cubrid-ci-watch register "$PR_URL" \
  --head "$HEAD_SHA" \
  --suite shell --suite sql --suite medium --suite sql_by_cci \
  --triggered-at "$TRIGGER_TIME" --receipt "$RECEIPT"
```

Pass all four suites (`shell`, `sql`, `medium`, `sql_by_cci`) for `/run all`, or only the selected suites for a subset run. Both build contexts are included by the CLI. Use the returned comment URL as the receipt for `/run` operations. For a GitHub failed-job rerun, pass `--kind rerun-failed`, `--run-id "$RUN_ID"`, and the intended `--attempt "$TARGET_ATTEMPT"`, with the stable operation receipt saved before the mutation.

When pickup is verified, include `--run-id` and `--attempt` in registration. To bind a request registered before pickup, repeat its original registration with those two options. Repeating the registration preserves its identity, original trigger time, deadline, and already recorded events. A conflicting binding is an error, not authorization to follow another run.

An unbound request can produce a `pickup_candidate` event. Verify the candidate against the saved trigger receipt before adding its binding. The newest run or a matching SHA alone cannot establish that association. If the relationship or attempt cannot be verified, retain the unresolved state. Do not post another `/run` to resolve it.

## Run one shared poller

Use one persistent process for all requests. Check whether a host-managed collector (such as `cubrid-hermes`) is already running before starting a new poller. Start a poller only if none owns `poll.lock`:

```bash
cubrid-ci-watch poll
```

If `cubrid-ci-watch poll` exits `2` with `another poller owns the state directory`, treat that as an already-running shared poller rather than a failure requiring a manual polling loop. Alternatively, an existing scheduler can invoke `cubrid-ci-watch poll --once`. Registration alone does not establish that polling is running. If the CLI or persistent runner is unavailable, preserve the receipt and registration details and report monitoring as not started.

Use `cubrid-ci-watch status --json` for the registry's stored observations. Use `cubrid-ci status "$PR_NUMBER" --json --history 0` when the user requests a fresh standalone snapshot. A successful query means collection succeeded, not that CI passed.

## Wait inside the current session

When staying in the current session until CI produces a failure or finishes, block on `cubrid-ci-watch wait` instead of `schedule` timers or repeated `gh run view` / `gh pr checks` loops:

```bash
cubrid-ci-watch wait "$REQUEST_ID" --after "$LAST_EVENT_ID"
# or wait until the request closes (complete / head_changed / superseded / deadline):
cubrid-ci-watch wait "$REQUEST_ID" --after "$LAST_EVENT_ID" --until terminal
```

Launch `cubrid-ci-watch wait` as one background shell task and end the turn so the runtime wakes the session only when a meaningful event (`pickup_candidate`, `failure`, `no_verdict`, `complete`, `head_changed`, `superseded`, `delay`, `deadline`) commits and prints as JSONL on stdout. `wait` cooperates with any running poller via non-blocking `poll.lock` checks (making no duplicate GitHub API calls while a shared poller runs) and falls back to 15-minute polling (`--interval 900`) when no poller is active.

`wait` exits `0` after emitting matching events or when the request is already closed, `3` if an optional `--timeout` elapses, and `2` on invalid input or storage errors. After waking on an intermediate event (such as an early `failure`), advance `LAST_EVENT_ID` to the highest emitted `id` before calling `wait` again.

## Consume events

Read events with `cubrid-ci-watch events --after "$LAST_EVENT_ID"`. Save the cursor only after handling the events. Replayed events retain their identifiers, so consumers can deduplicate them. For out-of-session notifications on hosts running `my-cubrid-hermes`, bind the request with `cubrid-briefing bind` to deliver watcher events to Discord and an idle bound Herdr agent; verify the configured sink before claiming notifications are enabled. A local event stream alone does not establish that an agent or user received it.

Invoke AI for a pickup candidate, a new failure or `no_verdict` event, a combined terminal result, a changed head or superseding execution, the 24-hour delay, or the monitoring deadline. Waiting states and unchanged results stay in the CLI. Keep long-running CI work waiting in `work-tracker`, with its CLI request identifier, receipt, head SHA, and last processed event identifier.

The CLI continues through missing pickup, queueing, partial execution, and a failure while other contexts remain unfinished. It emits one delay event at 24 hours and performs a final observation at 48 hours. Verified completion on that final observation takes precedence over a deadline event. Otherwise, monitoring ends with unresolved evidence retained. This does not cancel CI or assign a CI failure verdict.

After a head change or verified superseding execution, retain the original evidence and report the replacement. A replacement needs its own registration and receipt. Unsupported run-attempt evidence remains unresolved. Monitoring never triggers, reruns, or cancels CI.
