---
name: cubrid-sql-run
description: "Run a focused CUBRID CTP SQL or medium testcase against the intended local build and verify actual case results. Use for local reproduction or iteration on a selected SQL/medium regression, including CI failures. Triggers on phrases like 'run one SQL TC', 'reproduce a medium test', 'ctp.sh sql', or 'rerun a SQL CI failure locally'."
---

# Run focused CTP SQL and medium tests

## 1. Resolve the case and prepare

Resolve the selected test under `CUBRID_TESTCASES_DIR` from the loaded worktree environment. Validate the Git root, tracked full path, HEAD and dirty state. Ask for a missing root or ambiguous test identity rather than choosing a basename match. Preserve answer files, fixtures and category context. For CI replay, use the per-test revision contract in [CI evidence collection](../cubrid-ci-fix/references/ci-evidence.md).

Read [CTP preflight](../cubrid-common/references/ctp-preflight.md) before execution. It covers JDBC initialization, `just configure-build`, child-process installation identity and the runner's broad cleanup side effects. Verify an execution environment isolated from unrelated CUBRID work.

## 2. Prepare a single-case configuration

CTP's SQL runner accepts one scenario file as well as a directory. Both `sql` and `medium` route to it. Use the suite-specific CI configuration where available, and inspect the installed `CTP/bin/ctp.sh`, `conf/sql.conf`, `conf/medium.conf`, and `sql/bin/run.sh` to verify current options.

Copy the appropriate configuration to a unique attempt directory. Edit the copy's `[sql]` section using a section-aware editor; verify the effective values before executing:

- `scenario` is the absolute selected TC file in its intact checkout.
- `test_category` remains the actual suite; JDBC/CCI mode, charset, server settings and relevant parameters match the CI failure.
- For medium, resolve `data_file` and other fixture paths to that testcase checkout's matching dataset. The default HOME-based path may point at another revision. The currently installed medium loader extracts `mdb.tar.gz` by name; retain the expected archive basename and dataset layout.
- Disable any testcase auto-update mechanism found in the selected runner/configuration. Inspect exclusions; remove only those preventing an explicitly selected reproduction and record the override.
- Retain locale and database setup initially. Reuse setup only after proving the existing locale/database/configuration state meets the selected case's prerequisites, and record the reuse. Setup time alone does not justify skipping it.

After defining validated `CTP_HOME`, `SUITE` (`sql` or `medium`), `CONF`, and `ATTEMPT_DIR`, invoke CTP and preserve its exit status and output:

```bash
set +e
direnv exec . "$CTP_HOME/bin/ctp.sh" "$SUITE" -c "$CONF" > "$ATTEMPT_DIR/ctp.log" 2>&1
CTP_EXIT=$?
set -e
```

A long-running invocation needs a managed process/session handle so progress can be checked without launching it again. Read the emitted `Result Root Dir`, `main.info` or interface-specific summary, exact case results and failure/core/setup logs. The runner can return zero despite failed tests. Require expected cases actually executed, positive total, all expected successes, zero failures and no hidden setup/core errors. A zero-case run, missing summary, skipped case or unrelated binary is inconclusive, even with exit zero.


## 3. Verify and iterate

Record suite, exact case path, engine/test revisions and local patches, effective configuration, binary identity, command, output path and expected/actual case counts. Keep each failed attempt before retrying. A skipped or zero-case run is inconclusive; one later pass does not erase an earlier flaky result.

Use `cubrid-build` after authorized engine changes. Reuse prepared locale/database state only with evidence of matching prerequisites. This runner invocation authorizes execution, not changes to regression answers or publication. For an approved CI repair, return evidence to `cubrid-ci-fix`, which owns fix and push approval. Stop with a concrete missing dependency or fidelity limit if the existing runner cannot execute the case; propose a separate framework rather than silently substituting direct csql output for CTP verification.
