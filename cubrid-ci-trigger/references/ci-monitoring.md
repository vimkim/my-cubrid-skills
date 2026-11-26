# Monitor requests with cubrid-ci-watch

Use the standalone `cubrid-ci-watch` CLI (`~/gh/cubrid-ci-watch`, installed via `just install` or `daily-update-cubrid` to `~/.local/bin/cubrid-ci-watch`). The Python CLI owns durable request state, shared polling, deadlines, and replayable JSON events. It consumes `cubrid-pr-status --json --history 0` and read-only GitHub metadata. Read `cubrid-ci-watch --help` and `~/gh/cubrid-ci-watch/README.md` for the current CLI contract.

## Register the original request

Register after the trigger and pickup check. Preserve the original trigger time, exact head SHA, receipt, and selected suites even if no run has appeared:

```bash
cubrid-ci-watch register "$PR_URL" \
  --head "$HEAD_SHA" \
  --suite shell --suite sql --suite medium --suite sql_by_cci \
  --triggered-at "$TRIGGER_TIME" --receipt "$RECEIPT"
```

Pass all four suites (`shell`, `sql`, `medium`, `sql_by_cci`) for `/run all`, every suite present in the source run (including zero-shard carried-forward suites) for `/run rerun <run-id>`, or only the selected suites for a subset run. Both build contexts are included by the CLI. On explicit user request to exclude optional suites (`sql_by_cci`), pass `--required-only` (defaults to `shell`, `sql`, `medium`, or filters `sql_by_cci` out of supplied `--suite` flags) at registration, or remove an optional suite from an active request with `cubrid-ci-watch drop-suite "$REQUEST_ID" --suite sql_by_cci`. Use the returned comment URL as the receipt for `/run` operations. For a GitHub failed-job rerun, pass `--kind rerun-failed`, `--run-id "$RUN_ID"`, and the intended `--attempt "$TARGET_ATTEMPT"`, with the stable operation receipt saved before the mutation.

When pickup is verified, include `--run-id` and `--attempt` in registration. To bind a request registered before pickup, repeat its original registration with those two options. Repeating the registration preserves its identity, original trigger time, deadline, and already recorded events. A conflicting binding is an error, not authorization to follow another run.

An unbound request can produce a `pickup_candidate` event. Verify the candidate against the saved trigger receipt before adding its binding. The newest run or a matching SHA alone cannot establish that association. If the relationship or attempt cannot be verified, retain the unresolved state. Do not post another `/run` to resolve it.

## Run one shared poller

Use one persistent process for all requests. Check `cubrid-ci-watch status` (or `systemctl --user status cubrid-ci-watch.service` on hosts running the user systemd service) to see whether a shared poller already holds `poll.lock` before starting a new one. Start a poller only if none owns `poll.lock`:

```bash
cubrid-ci-watch poll
```

If `cubrid-ci-watch poll` exits `2` with `another poller owns the state directory`, treat that as an already-running shared poller rather than a failure requiring a manual polling loop. Alternatively, an existing scheduler can invoke `cubrid-ci-watch poll --once`. Registration alone does not establish that polling is running. If the CLI or persistent runner is unavailable, preserve the receipt and registration details and report monitoring as not started.

By default, `poll` uses per-PR 1/2/4/8/16-minute exponential backoff with a 10-second wakeup loop (pass `--interval SECONDS` for a fixed interval override). Use `cubrid-ci-watch status` (or `ls`) for the concise active-request human summary and poller state, `cubrid-ci-watch show "$REQUEST_ID"` for one request's detailed contexts and events, and `cubrid-ci-watch status --json` for the registry's stored observations. Use `cubrid-ci status "$PR_NUMBER" --json --history 0` when the user requests a fresh standalone snapshot. A successful query means collection succeeded, not that CI passed.

## Wait inside the current session (short runs only)

For typical 1–24h CI runs, prefer registering and returning/closing the session rather than keeping a session open; out-of-session notifications and `work-tracker` notes are handled by an external event consumer when running (e.g., `hermes-notify.service`), and any new session can inspect `cubrid-ci-watch status` or `cubrid-ci-watch show "$REQUEST_ID"`.

Only when staying in the current session for a short run until CI produces a failure or finishes, block on `cubrid-ci-watch wait` instead of `schedule` timers or repeated `gh run view` / `gh pr checks` / `gh pr view` loops:

Ignore the `gh event listen` hint that `gh pr view` prints. GitHub event subscriptions (preview) are not enabled on this account, so `gh event listen` fails with HTTP 403. Do not retry it. Use `cubrid-ci-watch wait` or `poll` instead.

```bash
# Wake on any meaningful event (default):
cubrid-ci-watch wait "$REQUEST_ID" --after "$LAST_EVENT_ID"
# Wait until all required contexts finish (ignores pending/failing optional contexts such as sql_by_cci):
cubrid-ci-watch wait "$REQUEST_ID" --after "$LAST_EVENT_ID" --until required
# Wait until all tracked contexts finish or the request closes (complete / head_changed / superseded / deadline):
cubrid-ci-watch wait "$REQUEST_ID" --after "$LAST_EVENT_ID" --until terminal
```

Whenever the user's condition is "all required checks pass" or "wait only for required checks", use `cubrid-ci-watch wait "$REQUEST_ID" --after "$LAST_EVENT_ID" --until required` (and optionally `cubrid-ci-watch drop-suite "$REQUEST_ID" --suite sql_by_cci` if the user wants to stop tracking `sql_by_cci`); never hand-roll a `gh pr checks --required` polling loop.

`cubrid-ci-watch` classifies each context as required or optional from the union of the stable required set (`build (release)`, `test_shell`, `test_sql`, `test_medium`) and live `gh pr checks --required` when available (cached across transient errors). Once every required context is attributed and terminal while optional contexts remain unfinished, the poller emits `required_complete` (`payload.outcome`, `required_contexts`, `required_source`) and keeps the request active until `complete` (whose payload records both overall `outcome` and `required_outcome`). `wait --until required` wakes on `required_complete`, `complete`, `head_changed`, `superseded`, or `deadline`, and exits `0` immediately if `required_complete` already committed at `id <= --after`.

Launch `cubrid-ci-watch wait` as one background shell task and end the turn so the runtime wakes the session only when a meaningful event (`pickup_candidate`, `failure`, `no_verdict`, `required_complete`, `complete`, `head_changed`, `superseded`, `delay`, `deadline`) commits and prints as JSONL on stdout. `wait` cooperates with any running poller via non-blocking `poll.lock` checks (making no duplicate GitHub API calls while a shared poller runs) and falls back to per-PR 1/2/4/8/16-minute backoff polling (or a fixed `--interval SECONDS` if given) when no poller is active.

`wait` exits `0` after emitting matching events or when the request is already closed, `3` if an optional `--timeout` elapses, and `2` on invalid input or storage errors. After waking on an intermediate event (such as an early `failure`), advance `LAST_EVENT_ID` to the highest emitted `id` before calling `wait` again.

## Consume events

Read events with `cubrid-ci-watch events --after "$LAST_EVENT_ID"`. Save the cursor only after handling the events. Replayed events retain their identifiers, so consumers can deduplicate them. `cubrid-ci-watch` itself records local state and JSONL events only and sends no notifications on its own; verify separately that an external consumer/delivery sink (such as `hermes-notify.service` for both orchestrated PR runs and standalone `cubrid-ci-watch` registrations, delivering routed Discord first-failure + terminal notifications with Actions run URLs and terminal `work-tracker` notes) is active before claiming out-of-session notifications are enabled. A local event stream alone does not establish that an agent or user received it.

Invoke AI for a pickup candidate, a new failure or `no_verdict` event, a combined terminal result, a changed head or superseding execution, the 24-hour delay, or the monitoring deadline. Waiting states and unchanged results stay in the CLI. Keep long-running CI work waiting in `work-tracker`, with its CLI request identifier, receipt, head SHA, and last processed event identifier.

The CLI continues through missing pickup, queueing, partial execution, and a failure while other contexts remain unfinished. It emits one delay event at 24 hours and performs a final observation at 48 hours. Verified completion on that final observation takes precedence over a deadline event. Otherwise, monitoring ends with unresolved evidence retained. This does not cancel CI or assign a CI failure verdict.

After a head change or verified superseding execution, retain the original evidence and report the replacement. A replacement needs its own registration and receipt. Unsupported run-attempt evidence remains unresolved. Monitoring never triggers, reruns, or cancels CI.
