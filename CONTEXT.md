# CUBRID Development Skills

This context names the workflows used to build CUBRID and create, execute, and interpret its test suites.

## Language

**Test suite**:
A named CUBRID regression corpus with its own case format, execution rules, and result contract, such as SQL, medium, shell, or isolation.
_Avoid_: Test type, test bucket

**Focused test runner**:
A workflow that executes one selected testcase or narrow subtree against an intended local CUBRID build and proves which cases ran and how they finished.
_Avoid_: Single-test helper, replay helper

**Runner implementation**:
The executable mechanism used by a focused test runner to discover, execute, judge, and record testcases while preserving the test suite's result contract.
_Avoid_: Test framework, backend

**Run identity**:
The provenance binding one attempt to its selected source worktree, installed engine, runner executable, testcase revision, and effective configuration.
_Avoid_: Build version, environment details

**Attempt**:
One runner invocation and its retained configuration, logs, status, and verdict artifacts. A later attempt supplements rather than replaces earlier evidence.
_Avoid_: Run result, latest run

**Suite migration gate**:
The suite-specific evidence threshold for adopting a runner implementation in a defined workflow; SQL, medium, and shell gates are independent.
_Avoid_: Global testkit readiness, migration complete
