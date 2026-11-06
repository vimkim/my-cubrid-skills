# Monitor requests with cubrid-ci-watch

Use `cubrid-ci-watch` from `my-cubrid/bin`. The Python CLI owns durable request state, shared polling, deadlines, and replayable JSON events. It consumes `cubrid-pr-status --json --history 0` and read-only GitHub metadata. Use the installed command or `~/my-cubrid/bin/cubrid-ci-watch`. Read its `--help` and `docs/cubrid-ci-watch/README.md` in the `my-cubrid` checkout for the current CLI contract.

## Register the original request

Register after the trigger and pickup check. Preserve the original trigger time, exact head SHA, receipt, and selected suites even if no run has appeared:

```bash
cubrid-ci-watch register "$PR_URL" \
  --head "$HEAD_SHA" \
  --suite shell --suite sql --suite medium \
  --triggered-at "$TRIGGER_TIME" --receipt "$RECEIPT"
```

Pass only the selected suites. Both build contexts are included by the CLI. Use the returned comment URL as the receipt for `/run` operations. For a GitHub failed-job rerun, pass `--kind rerun-failed`, `--run-id "$RUN_ID"`, and the intended `--attempt "$TARGET_ATTEMPT"`, with the stable operation receipt saved before the mutation.

When pickup is verified, include `--run-id` and `--attempt` in registration. To bind a request registered before pickup, repeat its original registration with those two options. Repeating the registration preserves its identity, original trigger time, deadline, and already recorded events. A conflicting binding is an error, not authorization to follow another run.

An unbound request can produce a `pickup_candidate` event. Verify the candidate against the saved trigger receipt before adding its binding. The newest run or a matching SHA alone cannot establish that association. If the relationship or attempt cannot be verified, retain the unresolved state. Do not post another `/run` to resolve it.

## Run one shared poller

Use one persistent process for all requests. Start it through the available background runner with captured output and verify that it survives the triggering session's return:

```bash
cubrid-ci-watch poll
```

Alternatively, an existing scheduler can invoke `cubrid-ci-watch poll --once`. The CLI prevents simultaneous pollers. Registration alone does not establish that polling is running. If the CLI or persistent runner is unavailable, preserve the receipt and registration details and report monitoring as not started.

Use `cubrid-ci-watch status --json` for the registry's stored observations. Use `cubrid-ci status "$PR_NUMBER" --json --history 0` when the user requests a fresh standalone snapshot. A successful query means collection succeeded, not that CI passed.

## Consume events

Read events with `cubrid-ci-watch events --after "$LAST_EVENT_ID"`. Save the cursor only after handling the events. Replayed events retain their identifiers, so consumers can deduplicate them. Verify a delivery channel before claiming notifications are enabled. A local event stream alone does not establish that an agent or user received it.

Invoke AI for a pickup candidate, a new failure or `no_verdict` event, a combined terminal result, a changed head or superseding execution, the 24-hour delay, or the monitoring deadline. Waiting states and unchanged results stay in the CLI. Keep long-running CI work waiting in `work-tracker`, with its CLI request identifier, receipt, head SHA, and last processed event identifier.

The CLI continues through missing pickup, queueing, partial execution, and a failure while other contexts remain unfinished. It emits one delay event at 24 hours and performs a final observation at 48 hours. Verified completion on that final observation takes precedence over a deadline event. Otherwise, monitoring ends with unresolved evidence retained. This does not cancel CI or assign a CI failure verdict.

After a head change or verified superseding execution, retain the original evidence and report the replacement. A replacement needs its own registration and receipt. Unsupported run-attempt evidence remains unresolved. Monitoring never triggers, reruns, or cancels CI.
