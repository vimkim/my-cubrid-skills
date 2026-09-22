---
name: cubrid-test-medium-run
description: "Run one complete CUBRID medium testcase directory serially with native cubrid-testkit and prove the ordered artifact verdict. Use for local reproduction or iteration on selected medium regressions, including CI failures. Not for arbitrary single medium SQL files, SQL, shell, unit, or isolation tests. Triggers on requests to run a medium testcase directory, reproduce a medium failure locally, rerun a medium CI failure, or use the focused medium runner."
---

# Run focused CUBRID medium tests

Medium is stateful: execute one complete selected directory in its original order. Do not treat an arbitrary `.sql` file as an independent medium testcase. Follow the [native testkit focused-run contract](../cubrid-common/references/testkit-focused.md) for shared preflight, disposable execution, verdict proof, attempt retention, and fallback/authorization policy.

## 1. Resolve the complete directory

Resolve the requested directory under the loaded environment's `CUBRID_TESTCASES_DIR/medium`; validate the testcase repository Git root, HEAD, dirty state, and tracked full path. Require its complete `cases`, `answers`, and fixtures. For CI replay, use [CI evidence and testcase identity](../cubrid-common/references/ci-evidence.md).

Enumerate every `.sql` case in the directory in original lexical execution order and write that positive set to `expected-cases.txt`. Reject a file-only selection, a partial hand-picked subset, missing answers, or an empty directory.

## 2. Build a serial immutable attempt

Within the shared attempt layout, copy the entire selected medium directory and required `mdb.tar.gz`; record the data archive SHA-256. Point the scenario and expected list at the copied case tree so generated `.result` files cannot modify the testcase checkout.

Use `testkit-focused.py prepare-config --suite medium` with copied `medium_dev.conf` and the copied data archive. Inspect the effective config. It must keep `parallel_slots=1`, `test_category=medium`, `create_table_reuseoid=no`, the complete copied scenario, and the recorded `data_file`. Do not substitute `medium.conf`, parallel slots, or a reused prepared database without a separately validated contract.

## 3. Execute and prove

Medium uses the native SQL family switch with the medium task:

```bash
TESTKIT_NATIVE=sql TESTKIT_CONTAIN=1 testkit medium -c "$CONF"
```

Capture combined output and process status. Extract this attempt's result root from `Result Root Dir:`, then run `testkit-focused.py verify --suite medium`. A pass requires the complete expected ordered case set, positive matching total, complete summaries/XML, every generated `.result`, all successes, and zero failures. Exit status alone is never a verdict.

Contained extraction of `mdb.tar.gz` can print ownership-mapping errors and a nonzero `tar` status while the suite completes correctly. Preserve and report that warning; judge the testcase result only through the full artifact contract. Treat investigation or repair of the warning as separate cubrid-testkit work.

## 4. Report and iterate

In addition to the shared attempt record, report the medium testcase revision/patches, directory and data-archive hashes, ordered expected/actual counts, extraction warnings, and result root. Use `cubrid-build` after authorized engine changes.
