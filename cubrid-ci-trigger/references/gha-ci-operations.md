# gha-ci operations contract

Consult this reference when selecting a rerun mechanism, diagnosing a missing or failed CUBRID gha-ci status, or explaining the run's output and retention.

## Scope and run shape

For PRs based on `develop` or `feature/**`, `/run` starts GitHub Actions `gha-ci`. CircleCI remains a separate legacy path for release branches and is outside `cubrid-ci-trigger`.

Every comment-triggered run builds both release and debug modes. The shell, SQL, and medium suites execute with the debug build. `test_sql_by_cci` executes the SQL cases through CCI with the release build. Therefore:

- a release-only build failure does not stop the debug suites, but `test_sql_by_cci` fails with "plan found no usable release build";
- a debug build failure prevents the shell, SQL, and medium suites from producing useful testcase verdicts;
- a previously published build for the same commit may be reused;
- `/run all` produces both build statuses and all four suite statuses;
- `/run shell`, `/run sql`, `/run medium`, or `/run sql_by_cci` leaves unselected suite contexts untouched or absent.

The default shard counts are shell 50, SQL 10, medium 1, and sql_by_cci 10. Treat timing as observed rather than guaranteed; a full run commonly spends its first several minutes building and then depends on queue and suite duration.

## Run and attempt semantics

`/run all`, a suite-specific `/run`, and `/run rerun <source-run-id>` each create a new CI workflow run with a new run ID.

GitHub's **Re-run failed jobs** keeps the run ID and creates a new CI workflow attempt. Successful jobs are retained while failed jobs run again. The rerun can replace suite and build commit statuses with the new verdicts, and summary or artifact evidence associated with that run may reflect the later attempt. Capture needed failure evidence before starting it.

GitHub's **Re-run all jobs** replays the original issue-comment event, whose gate resolves the PR's current head. It is not a reliable way to retest the original run's commit after the PR moves. Use `/run all` for a deliberate full run on the current head.

## Why prefer /run rerun <run-id>

When an eligible same-head source run exists and no disqualifier applies, `/run rerun <run-id>` gives decisive operational advantages over `/run all` or `/run <suite>`:

1. **Build reuse**: Because the engine commit and `BUILD_RECIPE` match, `build (release)` and `build (debug)` skip source checkout and compilation (`reuse=reused`).
2. **Zero shards for unchanged passing suites**: Suites with 0 failures, 0 unrun cases, and 0 TC changes set `par=0`, launch no shard pods, and carry forward their `pass` verdict and commit status (`Nothing to re-run`).
3. **Light-lane execution instead of up to 71 main-lane shards**: `/run all` claims up to 71 `cubrid-arc` shards (50 `shell`, 10 `sql`, 10 `sql_by_cci`, 1 `medium`). `/run rerun <run-id>` defaults to 1 `cubrid-arc-light` shard per suite with work, avoiding queue contention with other PRs' full runs.
4. **Automatic scale-out for large `shell` reruns**: If a `shell` rerun's estimated `TIMINGS` load exceeds 90 minutes (`5400`s, such as after merging `develop` into `tc/pr-<N>`), `plan` automatically spreads it onto `cubrid-arc` (~30 min/shard, up to 50 shards).
5. **Handles TC-only updates even after a 100% green run**: Diffing `tc/pr-<N>` from the source run's `tc_sha` to `HEAD`, any added, modified, or renamed file matching `${subdir}/.*/(cases|answers)/[^/]+$` selects all cases in its `cases/` directory (editing only `answers/` still reruns its paired cases), and deleted or renamed-away failing cases are cleanly removed from `want.list` rather than failing with `rerun_gone`.
6. **Handles wholly dead shards**: Any shard that died before producing results (`found=no`, 0 handled) has its entire `plan/shards/<idx>.list` carried into `unrun.list`.
7. **Complete status refresh, chaining, and evidence preservation**: Republishes build statuses and every source suite's status in one comment, supports chaining `/run rerun` onto a prior `/run rerun` (even a 0-shard carried-forward run), creates a new run ID that keeps the source run's logs intact, and prints the ready-to-copy `/run rerun <run-id>` (with `testtools=<branch>` if used) in every PR run summary.

## Recovery decision table

| Condition | Operation | Reason |
|---|---|---|
| A few cases appear flaky (with history evidence) | `/run rerun <run-id>` | Runs recorded failures without repeating passing suites |
| TC-only changes under `cases/` or `answers/` in `tc/pr-<N>` (or `develop` merged into `tc/pr-<N>`, even if source run passed 100%) | `/run rerun <run-id>` | Diffs `tc_sha..HEAD`, runs affected `cases/` directories, drops deleted/renamed failing cases, and skips unchanged suites |
| A shard died before running any case (`found=no`) | `/run rerun <run-id>` | Carries the whole dead shard's named cases |
| Prior `/run rerun` still has failures or new `cases/`/`answers/` fixes | `/run rerun <prior-rerun-id>` | Chains cleanly onto the newer run (even a 0-shard carried-forward run) |
| Release build alone failed for transient infrastructure | `gh run rerun <run-id> --failed` (or `/run sql_by_cci` if many `sql_by_cci` dirs would overload 1 light shard) | Re-executes the failed build job within the same run |
| Debug build failed before shards ran | `gh run rerun <run-id> --failed`, or a new full run | `plan` aborted with no `failed.list` for `/run rerun` to carry |
| Source code was pushed after the source run | `/run all` | `/run rerun` rejects `prev_sha != $SHA` |
| TC changes outside `cases/` or `answers/` (shared helpers, scripts, configs, data files) | `/run <affected-suite>` or `/run all` | `/run rerun` diff ignores paths outside `(cases\|answers)/[^/]+$` and falsely carries forward old verdicts |
| A shard handled only part of its assignment and then died/timed out (`rerun_short > 0`) | `/run <affected-suite>` or `/run all` | Unhandled tail is unnamed; `collect` holds the rerun red |
| Source run has `held` fault (build/TC provenance `mixed`/`mismatch`, unexplained `rerun_gone > 0`, inherited `held`, or pre-`held` legacy failure with 0 cases) | `/run <affected-suite>` or `/run all` | `held` propagates across `/run rerun` and keeps every rerun red |
| Source ID is `built by run`, incomplete/cancelled, >30 days old, predates relayout/`tc_sha`, or omits a needed suite | `/run <missing-suite>` or `/run all` | `gate`/`plan` rejects missing `failed.list`/jobs, or missing suites stay absent |
| Build recipe (`image\|args`) on `develop` changed since source run | `/run <affected-suite>` or `/run all` | `plan` rejects `prev_recipe != $recipe` |
| Need a new `testtools=<branch>` tested against previously passing cases | `/run <suite> testtools=<branch>` or `/run all testtools=<branch>` | `/run rerun` does not diff `cubrid-testtools` |
| Oversized `sql`, `medium`, or `sql_by_cci` rerun (many top-level `_...` dirs failed/changed, or `sql_by_cci` `nobuild`) | `/run sql`, `/run sql_by_cci`, or `/run all` | Dir-unit reruns never scale past 1 `cubrid-arc-light` shard (120-min timeout) and pull entire `_...` dirs |
| Check contexts are absent on a new head, or a run was cancelled/superseded | `/run all` (after any active run stops) | Restores build and all required suite statuses together |
| Base branch is `release/11.x` (CircleCI) | Outside this skill | `comment_trigger.yml` only accepts `all\|shell\|sql\|medium` and ignores `/run rerun` |

`/run rerun` selects every suite identified by the source run's shard/status jobs. It plans recorded failures (expanding `sql`, `medium`, and `sql_by_cci` failures to their top-level `_...` directory), named cases from wholly dead shards, and cases whose `cases/` or `answers/` files changed since the source run's `tc_sha` (excluding deleted/renamed-away cases). `shell` reruns exceeding 90 minutes scale out up to 50 `cubrid-arc` shards; dir-unit suites always use 1 `cubrid-arc-light` shard. A suite with nothing selected runs 0 shards and carries forward the source verdict — unless the source carried an unrecoverable `held` fault (`rerun_short`, provenance mismatch, `rerun_gone`), which stays red until a full `/run <suite>` or `/run all`. The source internal run directory and failure list must still exist (<30 days). For collected source links and per-case comparisons, read [Rerun evidence](../../cubrid-common/references/ci-reruns.md).

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
