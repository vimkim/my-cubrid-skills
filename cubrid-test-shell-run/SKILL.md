---
name: cubrid-test-shell-run
description: "Run one focused CUBRID shell testcase or a narrow subtree against the intended local build and prove the actual case results. Use for local reproduction or iteration on selected shell regressions, including CI failures. Not for unit, SQL, medium, or isolation tests. Triggers on requests to run or debug one shell test, reproduce a shell failure locally, run an itrack/bug/CBRD shell case, or use the current CTP shell runner."
argument-hint: "<test-dir-or-subtree>"
---

# Run focused CUBRID shell tests

The current runner implementation is CTP. Keep the workflow's case identity and result proof independent of that implementation.

## 1. Resolve the test and prepare

Resolve `CUBRID_TESTCASES_PRIVATE_EX_DIR` from the loaded worktree environment and verify its Git root, HEAD and dirty state. Inspect configuration if unset; ask for the root if it cannot be established. Locate the requested full path with `rg --files` or search test content; disambiguate duplicate basenames. For CI replay, verify repository/revision/path using [CI evidence collection](../cubrid-common/references/ci-evidence.md).

`TEST_DIR` must contain `cases/<name>.sh`; it is not the script or `cases/` itself. An ancestor runs a subtree, so enumerate the expected case set before launching. Preserve the checkout's fixtures and answers.

Read [CTP preflight](../cubrid-common/references/ctp-preflight.md), initialize JDBC and configure/build the intended worktree. Verify child-process installation identity and an environment isolated from unrelated CUBRID processes/databases. Do not use blanket process-kill commands as troubleshooting.

## 2. Run the existing helper

Inspect current local recipes and the helper before invocation:

```bash
just --list
command -v cubrid-shell-debug.sh
```

The current canonical recipe is:

```bash
direnv exec . just ctp::shell-debug "$TEST_DIR"
```

`just shell-debug` is a compatibility wrapper. `shell-debug-many` uses the same execution mechanism for a subtree. These are personal convenience tools, not organization-wide reviewer commands.

The installed helper copies `$HOME/CTP/conf/shell_ci.conf`, narrows scenario, disables testcase updates, removes exclusions, allocates a PTY and prints a retained transcript path. It also initializes a missing shell FM configuration snapshot; verify that snapshot represents the intended install. Recheck these behaviors if the installed helper changes.

The current recipe/helper interpolates arguments through shell/sed. Paths with whitespace or shell/sed metacharacters need the direct configuration path below; quoting the outer just argument does not fix inner interpolation.

## 3. Direct CTP fallback

If the helper is unavailable or cannot represent the path safely, copy the correct shell configuration to a unique attempt directory. Use a safe configuration editor to set an absolute `scenario`, set `testcase_update_yn=false`, and remove only exclusions blocking the explicitly selected reproduction. Verify effective values and any repository-update hooks before execution. Preserve relevant CI parameters and fixtures.

For validated CTP_HOME and CONF paths:

```bash
direnv exec . "$CTP_HOME/bin/ctp.sh" shell -c "$CONF"
```

Capture stdout/stderr, exit status, and this invocation's output locations; allocate a PTY if the installed runner requires one. Use a managed session for long execution. Do not add obsolete recipe copies to a worktree or use interactive mode autonomously: the stock interactive configuration can update test repositories and exclude the selected case.

## 4. Prove execution and retain results

Read the emitted transcript and per-case logs, discovering paths from this run rather than guessing a timestamp directory. Require:

- The expected case identities actually executed.
- A positive `Total Execution Case` count matching the selected case set.
- Zero failures, passing assertions, and a complete final summary.
- The intended engine installation and testcase revision/patch were used.

The helper rejects NOK, zero execution and missing summary, but inspect the case set and logs yourself. Exit zero alone is insufficient. Preserve logs before repeating; record infrastructure errors, excluded cases and unknown results distinctly.

## 5. Iterate within authorization

Rebuild/install after authorized engine changes using `cubrid-build`, then repeat the selected case. Inspect the first relevant failure before changing the hypothesis or patch. Test execution alone does not authorize answer changes, source fixes, commits or pushes. If reproduction identifies a likely defect, report the exact command, identity, results, logs, and proposed next action for review.
