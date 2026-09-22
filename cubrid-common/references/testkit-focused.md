# Native testkit focused-run contract

Read this reference before a focused SQL, medium, or shell run. These workflows use explicit native `cubrid-testkit`; CTP remains an asset dependency, not an implicit fallback.

## Establish run identity

Start inside the intended CUBRID Git worktree and load only that worktree's environment. Locate the installed `cubrid-common/scripts/testkit-focused.py` relative to the active runner skill, then run:

```bash
direnv exec . python3 "$TESTKIT_FOCUSED" preflight --suite "$SUITE"
```

Pass `--allow-commit-mismatch` only when the user explicitly authorizes that exact exception. It bypasses a confirmed source/install commit mismatch only. The helper still rejects a missing or unparseable identity, missing `testkit`, invalid CUBRID/CTP/JDK paths, or unavailable containment.

If `testkit` is absent, stop and ask the user to install their intended cubrid-testkit revision manually with `go install`. Never build, install, pull, or update it for them. Retain the helper output: it records the worktree HEAD and dirt, installed commit, testkit version and SHA-256, CUBRID/CTP/JDK paths, and containment probe. A dirty source worktree is a warning when identity matches, not a blocker.

## Create one retained attempt

Create a new attempt directory for every invocation. Keep earlier setup failures, NOK runs, and inconclusive attempts when retrying. Record the engine and testcase revisions/patches, preflight output, expected case list, copied configuration, command, combined output, exit status, and result artifacts.

Copy `$CUBRID` and `$CTP_HOME` into the attempt and use an attempt-local `$HOME`. Preserve any copied `$ATTEMPT_DIR/cubrid/databases` under another name within the attempt, then create a fresh empty `cubrid/databases`; never reuse its copied registry. Run only against those disposable trees: testkit requires `CUBRID_DATABASES` inside `$CUBRID`, and fixed CTP logs/results and shell FM state must not overwrite another attempt. For SQL and medium, also copy the selected testcase directory—including `cases`, `answers`, and fixtures—into the attempt; native sqlsuite writes `.result` files beside cases. Shell uses its source corpus read-only through `scenario_disk=on`.

Rewrite every install-bound runtime variable for the attempt: at minimum `CUBRID`, `CUBRID_DATABASES`, `CUBRID_TMP`, `CTP_HOME`, `HOME`, the CUBRID/CTP entries in `PATH`, and the copied CUBRID `lib` entry in `LD_LIBRARY_PATH`. Confirm `command -v cubrid`, `cubrid_rel`, and printed paths resolve to the disposable install before starting testkit.

Build `expected-cases.txt` before execution with one absolute case path per line in execution order. Reject an empty list. For CI reproduction, bind engine and testcase revisions using [CI evidence and testcase identity](ci-evidence.md).

Prepare the copied configuration with the shared helper:

```bash
python3 "$TESTKIT_FOCUSED" prepare-config \
  --suite sql \
  --base-conf "$ATTEMPT_DIR/CTP/conf/sql.conf" \
  --output-conf "$ATTEMPT_DIR/conf/sql.conf" \
  --scenario "$COPIED_SCENARIO" \
  --expected-list "$ATTEMPT_DIR/expected-cases.txt"
```

Use `--suite medium --base-conf .../medium_dev.conf --expected-list ... --data-file "$COPIED_MDB_ARCHIVE"` for medium. Use `--suite shell --base-conf .../shell_ci.conf --scenario "$SHELL_CORPUS" --expected-list "$ATTEMPT_DIR/expected-cases.txt"` for shell. The helper refuses an empty or partial SQL/medium scenario list, refuses to overwrite an existing attempt configuration, and prints its SHA-256.

Inspect the effective configuration before running. SQL and medium are serial (`parallel_slots=1`) with exclusions cleared for the explicit selection. Medium additionally requires `create_table_reuseoid=no` and the recorded data archive. Shell is serial, disables updates/retries/continuation, selects cases through `testcase_from_file`, records file feedback, and requires `scenario_disk=on`; do not replace it with an uncontained or writable-corpus run.

## Invoke the native family

Capture process status without treating it as the testcase verdict:

```bash
set +e
direnv exec . env \
  HOME="$ATTEMPT_DIR/home" \
  CUBRID="$ATTEMPT_DIR/cubrid" \
  CUBRID_DATABASES="$ATTEMPT_DIR/cubrid/databases" \
  CUBRID_TMP="$ATTEMPT_DIR/cubrid/tmp" \
  CTP_HOME="$ATTEMPT_DIR/CTP" \
  PATH="$ATTEMPT_DIR/CTP/bin:$ATTEMPT_DIR/CTP/common/script:$ATTEMPT_DIR/cubrid/bin:$PATH" \
  LD_LIBRARY_PATH="$ATTEMPT_DIR/cubrid/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}" \
  TESTKIT_NATIVE=sql \
  TESTKIT_CONTAIN=1 \
  testkit sql -c "$ATTEMPT_DIR/conf/sql.conf" \
  >"$ATTEMPT_DIR/run.log" 2>&1
RUNNER_EXIT=$?
set -e
printf '%s\n' "$RUNNER_EXIT" >"$ATTEMPT_DIR/exit.status"
```

For medium, keep `TESTKIT_NATIVE=sql` and change the task/config to `medium`. For shell, use `TESTKIT_NATIVE=shell testkit shell`. Never omit `TESTKIT_NATIVE`: unselected families delegate silently to legacy CTP. Never substitute CTP after a native failure unless the user explicitly requests a separate CTP run.

Use a managed process/session for a long invocation. Do not launch a second copy while checking progress.

## Prove the verdict

For SQL/medium, take the result directory only from this run's `Result Root Dir:` line. For shell, the copied CTP root makes this attempt's directory `$ATTEMPT_DIR/CTP/result/shell/current_runtime_logs`. Then run:

```bash
python3 "$TESTKIT_FOCUSED" verify \
  --suite "$SUITE" \
  --result-dir "$RESULT_DIR" \
  --expected-list "$ATTEMPT_DIR/expected-cases.txt" \
  --run-log "$ATTEMPT_DIR/run.log" \
  --runner-exit "$RUNNER_EXIT"
```

A pass requires the exact expected positive case set, complete summaries, zero failures/skips, all-success XML/verdict artifacts, and suite-specific result files. Runner exit `0` is insufficient. Missing artifacts, setup errors, zero cases, or identity differences are inconclusive or failed—not passes.

Report every attempt path and outcome. A later pass does not erase an earlier failure or inconclusive run. Test execution authorizes neither testcase/source edits nor publication.
