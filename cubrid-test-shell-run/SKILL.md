---
name: cubrid-test-shell-run
description: "Run one focused CUBRID shell testcase or narrow subtree with native cubrid-testkit and prove the artifact verdict. Use for local reproduction or iteration on selected shell regressions, including CI failures. Not for unit, SQL, medium, isolation, or whole-corpus qualification. Triggers on requests to run or debug one shell test, reproduce a shell failure locally, run an itrack/bug/CBRD shell case, or use the focused shell runner."
---

# Run focused CUBRID shell tests

This is the accepted personal focused workflow. It does not claim that cubrid-testkit's upstream whole-corpus shell equivalence gate has passed. Follow the [native testkit focused-run contract](../cubrid-common/references/testkit-focused.md) for shared preflight, disposable execution, verdict proof, attempt retention, and fallback/authorization policy.

## 1. Resolve the exact case set

Resolve the loaded environment's `CUBRID_TESTCASES_PRIVATE_EX_DIR`, then validate its Git root, HEAD, dirty state, and the requested tracked full path. Disambiguate duplicate basenames. For CI replay, use [CI evidence and testcase identity](../cubrid-common/references/ci-evidence.md).

A shell case is exactly `<name>/cases/<name>.sh`; the repeated name is semantic. A selected ancestor denotes a subtree. Enumerate every matching case before execution, sort reproducibly, and write the absolute paths to `expected-cases.txt`. Reject an empty set.

## 2. Build a contained immutable attempt

Within the shared attempt layout, keep the shell testcase checkout in place and read-only; `scenario_disk=on` gives the contained slot a disposable overlay for all case writes.

Use `testkit-focused.py prepare-config --suite shell` with copied `shell_ci.conf`, the full shell corpus as `scenario`, and the exact expected list as `testcase_from_file`. Inspect the effective config. It must use one slot, `scenario_disk=on`, file feedback, no testcase update, no continuation, no retry, and no writable workspace/ram overlay. Preserve relevant timeout, parameter, and macro policy from the CI reproduction.

## 3. Execute and prove

Invoke exactly the explicit shell family under containment:

```bash
TESTKIT_NATIVE=shell TESTKIT_CONTAIN=1 testkit shell -c "$CONF"
```

Capture combined output and process status. Because the attempt has its own CTP copy, its result directory is `$ATTEMPT_DIR/CTP/result/shell/current_runtime_logs`. Run `testkit-focused.py verify --suite shell` against it. A pass requires the exact positive dispatched and finished case set, zero failures/skips, passing assertions, complete status/feedback/XML/test logs, and matching expected totals. A shell script's process status and testkit's exit status are not testcase verdicts.

## 4. Report and iterate

In addition to the shared attempt record, report the shell testcase revision/patches, exact case set, assertion failures, expected/actual counts, and result directory. Use `cubrid-build` after authorized engine changes.
