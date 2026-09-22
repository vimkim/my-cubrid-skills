---
name: cubrid-test-sql-run
description: "Run one focused CUBRID SQL testcase or narrow SQL subtree with native cubrid-testkit and prove the artifact verdict. Use for local reproduction or iteration on selected SQL regressions, including CI failures. Not for medium, shell, unit, or isolation tests. Triggers on requests to run one SQL testcase, reproduce a SQL failure locally, rerun a SQL CI failure, or use the focused SQL runner."
---

# Run focused CUBRID SQL tests

Follow the [native testkit focused-run contract](../cubrid-common/references/testkit-focused.md) for shared preflight, disposable execution, verdict proof, attempt retention, and fallback/authorization policy. The steps below define only SQL-specific selection and evidence.

## 1. Resolve the intended run

Resolve the selected test under the loaded environment's `CUBRID_TESTCASES_DIR/sql`; validate the testcase repository Git root, HEAD, dirty state, and tracked full path. Disambiguate duplicate basenames. For CI replay, use [CI evidence and testcase identity](../cubrid-common/references/ci-evidence.md).

Select one `.sql` file or a narrow directory. Preserve its containing `cases`/`answers` pair and fixtures. Enumerate the expected `.sql` paths before running; a selected case without its answer is an error, not a skip to accept.

## 2. Build an immutable attempt

Within the shared attempt layout, copy the selected SQL case group so native `.result` files never modify the testcase checkout. Point the scenario at the copied `.sql` or copied narrow directory, and write `expected-cases.txt` with the copied absolute `.sql` paths in execution order.

Use `testkit-focused.py prepare-config --suite sql` with the copied `sql.conf`. Inspect its `[sql]` values and preserve the intended JDBC mode, charset, locale, server, and broker settings. The prepared config fixes `parallel_slots=1`, `enable_memory_leak=no`, and the explicit scenario. Native interactive and memory-leak modes delegate to CTP; stop rather than presenting either as a native run.

## 3. Execute and prove

Invoke exactly the explicit family under containment:

```bash
TESTKIT_NATIVE=sql TESTKIT_CONTAIN=1 testkit sql -c "$CONF"
```

Capture combined output and process status as described by the shared contract. Extract the result root from this attempt's `Result Root Dir:` line, then run `testkit-focused.py verify --suite sql`. A pass requires the expected positive case count, identical expected/executed identities, complete `summary_info`, `main.info`, XML, per-case `.result` artifacts, all successes, and zero failures. Exit status alone is never a verdict.

## 4. Report and iterate

In addition to the shared attempt record, report the SQL testcase revision/patches, selected case group, JDBC mode, expected/actual case counts, and result root. Use `cubrid-build` after authorized engine changes.
