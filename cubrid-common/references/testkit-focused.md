# Native testkit focused-run contract

Read this reference before a focused SQL, medium, or shell run. These workflows use explicit native `cubrid-testkit`; CTP remains an asset dependency, not an implicit fallback.

## Establish run identity

Start inside the intended CUBRID Git worktree and load only that worktree's environment. Locate the installed `cubrid-common/scripts/testkit-focused.py` relative to the active runner skill, then run:

```bash
direnv exec . python3 "$TESTKIT_FOCUSED" preflight --suite "$SUITE"
# For shell, also pass --selection "$SELECTION" to verify init.sh helpers before copying CTP:
direnv exec . python3 "$TESTKIT_FOCUSED" preflight --suite shell --selection "$SELECTION"
```

Pass `--allow-commit-mismatch` only when the user explicitly authorizes that exact exception. It bypasses a confirmed source/install commit mismatch only. The helper still rejects a missing or unparseable identity, missing `testkit`, invalid CUBRID/CTP/JDK paths, a `CUBRID_JAVA_HOME` that is not Java 8, unavailable containment, or a `CTP_HOME` whose `shell/init_path/init.sh` lacks helpers called by `--selection`.

If `testkit` is absent, stop and ask the user to install their intended cubrid-testkit revision manually with `go install`. Never build, install, pull, or update it for them. Retain the helper output: it records the worktree HEAD and dirt, installed commit, testkit version and SHA-256, CUBRID/CTP/JDK paths, `CTP_HOME` git dirt and `origin/develop` lag (`ctp_head`, `ctp_dirty`, `ctp_behind_origin_develop`), shell `init.sh` helper readiness (`ctp_init_has_wait_until`), and containment probe. A dirty source worktree or stale/dirty `CTP_HOME` is a warning when selected helpers are present, not a blocker, unless a selected shell case invokes an `init.sh` helper missing from `CTP_HOME`. Every suite, shell included, requires a JDK 8 `JAVA_HOME`, and the helper prints `java_home=` for every suite. Shell cases start the PL server too. For SQL and medium the helper also requires `jdbc/cubrid_jdbc.jar` in the install; initialize the `cubrid-jdbc` submodule and reinstall when it is missing.

## Create one retained attempt

Create a new attempt directory for every invocation under a short root such as `$HOME/tk/<n>`. CUBRID exits when `$CUBRID_TMP` (`$ATTEMPT_DIR/cubrid/tmp`) is longer than 96 characters, because it holds socket paths; `prepare-config` rejects a longer path. Keep earlier setup failures, NOK runs, and inconclusive attempts when retrying. Record the engine and testcase revisions/patches, preflight output, expected case list, copied configuration, command, combined output, exit status, and result artifacts.

Copy `$CUBRID` and `$CTP_HOME` into the attempt and use an attempt-local `$HOME`. Preserve any copied `$ATTEMPT_DIR/cubrid/databases` under another name within the attempt, then create a fresh empty `cubrid/databases`; never reuse its copied registry. For shell, start from an empty result tree with `rm -rf "${ATTEMPT_DIR:?}/CTP/result"`: shell testkit appends to fixed files under `result/shell/current_runtime_logs`, so runs copied from the source CTP tree would mix into this attempt's logs. `prepare-config --suite shell` refuses a missing `$ATTEMPT_DIR/CTP`, a non-empty `CTP/result`, or a `CTP/shell/init_path/init.sh` missing helpers called by selected cases. Run only against those disposable trees: testkit requires `CUBRID_DATABASES` inside `$CUBRID`, and fixed CTP logs/results and shell FM state must not overwrite another attempt. For SQL and medium, also copy the entire selected testcase group—including `cases`, `answers`, and fixtures—into the attempt; native sqlsuite writes `.result` files beside cases. Shell uses its source corpus read-only through `scenario_disk=on`.

Rewrite every install-bound runtime variable for the attempt: at minimum `CUBRID`, `CUBRID_DATABASES`, `CUBRID_TMP`, `CTP_HOME`, `HOME`, the CUBRID/CTP entries in `PATH`, and the copied CUBRID `lib` entry in `LD_LIBRARY_PATH`. Unset every variable in the preflight `env_unset=` line. A worktree environment such as cub-workenv exports `CUBRID_CONF_FILE`, `CUBRID_BROKER_CONF_FILE`, and `CUBRID_<PARAM>` overrides; if they leak in, the binaries read a configuration outside the attempt while CTP edits the attempt's `conf`, and the server never starts. Keep `CUBRID_JAVA_HOME`, but make sure it points at Java 8 in the run shell as well. The PL server starts from it, and a newer JDK (for example Temurin 21 exported by a direnv or mise setup) makes every server start fail with "PL server can not be started". The run then reports NOK cases that say nothing about the testcase. The preflight rejects a non-8 `CUBRID_JAVA_HOME` and prints `cubrid_java_version=`. Set `JAVA_HOME` to the preflight `java_home=` value for every suite. Set `CUBRID_JAVA_HOME` to the preflight `cubrid_java_home=` value. If the preflight prints no `cubrid_java_home=` line, use the `java_home=` value. An empty `JAVA_HOME` or `CUBRID_JAVA_HOME` makes shell cases fail at setup with NOK results that say nothing about the testcase. Set `CCACHE_DISABLE=1`: the containment runs as uid 0, so ccache cannot create its temporary directory and the locale library build fails. Run the preflight `testkit=` path, not bare `testkit`: a mise shim does not resolve once `HOME` points into the attempt. Confirm `command -v cubrid`, `cubrid_rel`, and printed paths resolve to the disposable install before starting testkit.

For CI reproduction, bind engine and testcase revisions using [CI evidence and testcase identity](ci-evidence.md). The helper cannot prove the copied group is complete against its source.

Prepare the copied configuration with the shared helper:

```bash
python3 "$TESTKIT_FOCUSED" prepare-config \
  --suite sql \
  --base-conf "$ATTEMPT_DIR/CTP/conf/sql.conf" \
  --output-conf "$ATTEMPT_DIR/conf/sql.conf" \
  --scenario "$COPIED_GROUP" \
  --selection "$COPIED_SELECTION" \
  --output-expected-list "$ATTEMPT_DIR/expected-cases.txt"
```

For SQL, select a copied case or narrow directory within the copied group. For medium, use `--suite medium --base-conf .../medium_dev.conf --data-file "$COPIED_MDB_ARCHIVE"` and select the whole copied group containing `cases` and `answers`. For shell, use `--suite shell --base-conf .../shell_ci.conf --scenario "$SHELL_CORPUS"` and select a case or subtree within that corpus. The helper discovers and validates the cases, creates the expected list and configuration exclusively, and prints both hashes and the case count. Retain a failed attempt if either output write fails; do not run testkit.

Inspect the effective configuration before running. SQL and medium are serial (`parallel_slots=1`) with exclusions cleared for the explicit selection. Medium additionally requires `create_table_reuseoid=no` and the recorded data archive. Shell is serial, disables updates/retries/continuation, selects cases through `testcase_from_file`, records file feedback, and requires `scenario_disk=on`; do not replace it with an uncontained or writable-corpus run.

## Invoke the native family

Capture process status without treating it as the testcase verdict:

```bash
set +e
env ${ENV_UNSET:+$(printf -- '-u %s ' $ENV_UNSET)} \
  CCACHE_DISABLE=1 \
  HOME="$ATTEMPT_DIR/home" \
  CUBRID="$ATTEMPT_DIR/cubrid" \
  CUBRID_DATABASES="$ATTEMPT_DIR/cubrid/databases" \
  CUBRID_TMP="$ATTEMPT_DIR/cubrid/tmp" \
  CTP_HOME="$ATTEMPT_DIR/CTP" \
  JAVA_HOME="$JAVA_HOME_8" \
  CUBRID_JAVA_HOME="$CUBRID_JAVA_HOME_8" \
  PATH="$ATTEMPT_DIR/CTP/bin:$ATTEMPT_DIR/CTP/common/script:$ATTEMPT_DIR/cubrid/bin:$PATH" \
  LD_LIBRARY_PATH="$ATTEMPT_DIR/cubrid/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}" \
  TESTKIT_NATIVE=sql \
  TESTKIT_CONTAIN=1 \
  "$TESTKIT" sql -c "$ATTEMPT_DIR/conf/sql.conf" \
  >"$ATTEMPT_DIR/run.log" 2>&1
RUNNER_EXIT=$?
set -e
printf '%s\n' "$RUNNER_EXIT" >"$ATTEMPT_DIR/exit.status"
```

Take `TESTKIT`, `ENV_UNSET`, and `JAVA_HOME_8` from the retained preflight output (`testkit=`, `env_unset=`, and `java_home=`). Take `CUBRID_JAVA_HOME_8` from `cubrid_java_home=`, or from `java_home=` when that line is absent. Run this from a shell that already loaded the worktree environment; do not wrap it in `direnv exec .`, which exports the overrides again.

For medium, keep `TESTKIT_NATIVE=sql` and change the task/config to `medium`. For shell, use `TESTKIT_NATIVE=shell "$TESTKIT" shell`. Never omit `TESTKIT_NATIVE`: unselected families delegate silently to legacy CTP. Never substitute CTP after a native failure unless the user explicitly requests a separate CTP run.

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

A pass requires the exact expected positive case set, complete summaries, zero failures/skips (shell also allows macro skips of cases outside the selected set when XML, status, feedback, and run log reconcile them), all-success XML/verdict artifacts, and suite-specific result files. Runner exit `0` is insufficient. Missing artifacts, setup errors, zero cases, or identity differences are inconclusive or failed—not passes.

Report every attempt path and outcome. A later pass does not erase an earlier failure or inconclusive run. Test execution authorizes neither testcase/source edits nor publication.
