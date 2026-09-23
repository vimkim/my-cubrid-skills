# gha-ci operations contract

Consult this reference when selecting a rerun mechanism, diagnosing a missing or failed CUBRID gha-ci status, or explaining the run's output and retention.

## Scope and run shape

For PRs based on `develop` or `feature/**`, `/run` starts GitHub Actions `gha-ci`. CircleCI remains a separate legacy path for release branches and is outside `cubrid-ci-trigger`.

Every comment-triggered run builds both release and debug modes. Requested suites execute with the debug build. Therefore:

- a release-only build failure does not stop the suites;
- a debug build failure prevents the suites from producing useful testcase verdicts;
- a previously published build for the same commit may be reused;
- `/run all` produces both build statuses and all three suite statuses;
- `/run shell`, `/run sql`, or `/run medium` leaves unselected suite contexts untouched or absent.

The default shard counts are shell 50, SQL 10, and medium 1. Treat timing as observed rather than guaranteed; a full run commonly spends its first several minutes building and then depends on queue and suite duration.

## Run and attempt semantics

`/run all`, a suite-specific `/run`, and `/run rerun <source-run-id>` each create a new CI workflow run with a new run ID.

GitHub's **Re-run failed jobs** keeps the run ID and creates a new CI workflow attempt. Successful jobs are retained while failed jobs run again. The rerun can replace suite and build commit statuses with the new verdicts, and summary or artifact evidence associated with that run may reflect the later attempt. Capture needed failure evidence before starting it.

GitHub's **Re-run all jobs** replays the original issue-comment event, whose gate resolves the PR's current head. It is not a reliable way to retest the original run's commit after the PR moves. Use `/run all` for a deliberate full run on the current head.

## Recovery decision table

| Condition | Operation | Reason |
|---|---|---|
| A few cases appear flaky | `/run rerun <run-id>` | Runs recorded failures without repeating passing suites |
| A shard died before running any case | `/run rerun <run-id>` | Carries the whole dead shard's named cases |
| A shard handled only part of its assignment and then died | `/run all` | The unhandled tail is not individually recoverable and a partial rerun remains red |
| Release build alone failed for transient infrastructure | `gh run rerun <run-id> --failed` | Re-executes the failed build job within the same run |
| Debug build failed before shards ran | `gh run rerun <run-id> --failed`, or a new full run | `/run rerun` has no failed shard cases to carry |
| Source code was pushed after the source run | `/run all` | `/run rerun` requires the same tested engine commit as the current PR head |
| Check contexts are absent on a new head | `/run all` | PR pushes do not attach the gha-ci PR status set |
| A run was cancelled or superseded | `/run all` after the prior run stops | Restores build and selected suite statuses together |

`/run rerun` derives its suite set from non-successful shard jobs in the source run. Suites whose shards all passed remain untouched. The source internal run directory and failure list must still exist.

## Concurrency and evidence safety

All `/run` requests for one PR share one cancellation group, regardless of selected suite. A second request cancels the in-flight request and can leave build contexts pending and suite contexts red or errored. Wait for a GitHub rerun to finish before posting another `/run` for the PR.

Before a same-head retrigger, retain the current run URL and any evidence needed for diagnosis. Do not infer that an absent status means no run exists: inspect known receipts, linked Actions runs, and pending statuses.

## Result location

Open the selected `gha-ci: test_<suite>` status and follow its Details link to the Actions run summary. Results are written to the GitHub step summary rather than a PR comment. The summary includes:

- planned, executed, passed, failed, skipped, and never-run counts;
- failed-case tables and per-case folded logs;
- cases never run because a shard died before execution;
- shard and total wall-clock measurements;
- build, testcase, and CTP provenance;
- an internal Artifacts link.

The Artifacts link is reachable only from the internal network or VPN. The internal run directory is pruned 30 days after the run. Treat GitHub's own log and workflow retention as a separate repository setting unless it is independently verified.

## Advanced CTP selection

The workflow accepts an explicit trailing `testtools=<branch>` on `/run` and `/run rerun`. Preserve it when the user or source run explicitly requires a non-default `cubrid-testtools` branch. Ordinary runs use the workflow default; never choose an override speculatively.
