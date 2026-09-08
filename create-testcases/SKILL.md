---
name: create-testcases
description: Create CUBRID test cases (unit/SQL/shell) for a given feature or bug fix. Use when the user asks to create tests, write test cases, or mentions testing a CBRD ticket.
argument-hint: [feature-description or CBRD-XXXXX]
disable-model-invocation: true
---

Create CUBRID test cases for a given feature or bug fix.

Select test types that exercise the feature's observable behavior: unit, SQL/medium, shell, or isolation. Do not create all types for every change. Read the module's existing tests and applicable AGENTS.md before choosing a framework.

$ARGUMENTS

For OOS (Out-of-row Overflow Storage), consult `cubrid-oos-context`. Choose data and thresholds from the current implementation and configuration; do not confuse OOS with disk exhaustion or assume a payload size alone proves out-of-row placement.

## Step 1: Understand what to test

- If a CBRD ticket is mentioned, use `/cubrid-jira` to fetch context first.
- Read the relevant source code to understand the feature/fix being tested.
- Identify the key behaviors, edge cases, and error conditions to cover.

## Step 2: Create Unit Tests

Create tests under the appropriate `unit_tests/<module>/` and follow its actual CMake/test conventions. The top-level suite uses Catch2, while the OOS module has Google Test infrastructure; neither pattern applies universally. Reuse module fixtures and registration rather than adding a new main/link pattern blindly. Consult `unit_tests/AGENTS.md` and `cubrid-build` for compilation and execution.

## Step 3: Create SQL Tests

Resolve `CUBRID_TESTCASES_DIR` from the loaded environment, validate its Git root, and inspect the appropriate SQL/medium category and nearby tests. Ask for an unresolved root rather than assuming a HOME path.

**Conventions**:
- Directory structure: `<test_dir>/cases/<name>.sql` and `<test_dir>/answers/<name>.answer`
- Test naming: use JIRA ticket ID if available (e.g., `cbrd_26609.sql`), otherwise descriptive name
- SQL file contains: setup DDL, test DML/queries, cleanup (DROP statements)
- Use `autocommit on;` at the top if needed
- Follow neighboring answer-file formatting and runner comparison rules.
- Derive expectations from intended behavior. Run with `cubrid-sql-run`, inspect and independently validate output, then capture a new answer if appropriate. Never overwrite an existing regression answer simply because the current run differs.

**Files to create**:
- `$CUBRID_TESTCASES_DIR/sql/<category>/<test_name>/cases/<name>.sql`
- `$CUBRID_TESTCASES_DIR/sql/<category>/<test_name>/answers/<name>.answer` (if deterministic)

## Step 4: Create Shell Tests

Resolve `CUBRID_TESTCASES_PRIVATE_EX_DIR`, validate the Git root, and inspect neighboring shell tests in the relevant category. Run with `cubrid-shell-run`.

**Conventions**:
- Directory structure: `<category>/<test_name>/cases/<test_name>.sh`
- Test script sources `$init_path/init.sh` for helper functions
- Standard flow:
  ```bash
  #!/bin/bash
  . $init_path/init.sh
  init test

  # Setup
  cubrid_createdb testdb
  cubrid server start testdb

  # Test operations
  csql -c "SQL" testdb
  # ... verify results ...

  # Cleanup
  cubrid server stop testdb
  cubrid deletedb testdb
  finish
  ```
- Use `write_ok` / `write_nok` to record pass/fail
- Use `test_exec_sql` and `test_exec_command` helpers
- Result format: `<test_name>-N : OK` or `<test_name>-N : NOK`
- Follow the neighboring test's expected-output convention; create `.result` only when that harness uses it.

**Files to create**:
- `$CUBRID_TESTCASES_PRIVATE_EX_DIR/shell/<category>/<test_name>/cases/<test_name>.sh`
- `$CUBRID_TESTCASES_PRIVATE_EX_DIR/shell/<category>/<test_name>/cases/<test_name>.result`

## Step 5: Summary

After creating all test files, present a summary table:

| Type | Path | Description |
|------|------|-------------|
| Unit | `unit_tests/...` | ... |
| SQL  | `~/gh/tc/...` | ... |
| Shell | `$CUBRID_TESTCASES_PRIVATE_EX_DIR/...` | ... |

Ask the user if they want to adjust any of the test cases.
