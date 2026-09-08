---
name: cubrid-ci-fix
description: "Diagnose and repair CUBRID PR CI failures with human approval before fixes and before pushes, retain failed-TC history, and verify locally and in CI. Use for runtime or miscellaneous CI failures requiring an iterative fix; use cubrid-ci-analyze for a report-only snapshot. Triggers on phrases like 'fix this PR CI', 'repair CUBRID CI failures', 'CI 버그 고쳐줘', or 'loop until CUBRID CI passes'."
---

# Repair CUBRID PR CI

Work from one identified PR and exact tested revisions. Maintain the repair record under `/home/vimkim/gh/my-cubrid-docs`. A local pass is a candidate fix; completion requires the current PR's required CI to pass.

## 1. Identify the effort

Resolve the supplied PR URL, or the current branch's PR with `gh pr view --json url,number,state,headRefOid,headRefName,baseRefName`. Require an open CUBRID PR. Record the full engine head SHA, source worktree, remote/branch identities and dirty state. Preserve unrelated edits; use an isolated worktree when necessary.

Use `track-work` for this long-running loop. Resume an existing effort by reading its ledger and evidence before creating another. Read [the ledger contract](references/ledger.md) and create its initial record now.

Resolve `CUBRID_TESTCASES_DIR` (test_sql and test_medium) and `CUBRID_TESTCASES_PRIVATE_EX_DIR` (test_shell) from the worktree's loaded environment. Inspect configured paths without dumping secrets. If unset, inspect local configuration; ask for the missing root if it cannot be established. Validate each as a Git checkout and record HEAD and dirty state. Never run a testcase sync/push helper merely to locate files.

## 2. Collect and account for failures

Use `cubrid-ci-analyze` for the available runtime snapshot and read [CI evidence collection](references/ci-evidence.md) for miscellaneous checks, direct API fallback, and per-TC identity verification. Cover test_shell, test_sql, test_medium, prerequisite jobs, and all discovered miscellaneous checks, including formatting/license checks. Respect an explicitly narrower user request, but report remaining PR-wide coverage as incomplete.

Locate every failed or abnormal TC in its configured Git repository using evidence repository/revision/full path. Preserve fixtures, answer files and suite configuration. Resolve ambiguity before editing; a basename match alone is insufficient. Missing private access or unresolved source identity is a limitation, not a pass.

Inventory every failure occurrence, abnormal result and job-level failure. Reconcile counts and keep unavailable or pending checks visible. Collection is read-only: it does not authorize a rerun comment, push, or testcase update.

## 3. Analyze and request fix approval — HITL

Consult relevant my-cubrid-docs and my-cubrid-jira context, the tested code/diff and TC sources. Use `diagnosing-bugs` when a failure needs a debugging loop, and feature-specific context only when relevant. Trace each proposed cause to observed evidence; distinguish inference and unknowns. Group failures only when the evidence supports a common cause.

Present a reviewable plan in the ledger: affected TCs/checks, root cause and confidence, exact repositories/files/functions to change, proposed behavior and why it is correct, intended test/answer changes, reproduction command and verification criteria. A concrete edit description or proposed patch in the report is appropriate; leave source/test files unchanged until approval.

Ask the user to review and approve that plan. Approval covers retries within the stated diagnosis and scope. A new cause, changed behavior contract, different repository, weakened assertion, or materially expanded change requires a revised plan and renewed approval. A missing tool or setup failure is not permission to broaden the patch. Record the user's answer and its scope; elapsed time or an automatic continuation is not approval.

## 4. FIX-STEP: apply and verify the approved fix

Modify the engine or testcase repository as justified and approved. Preserve the assertion's intended coverage; derive expected answers from specified behavior or an independently validated baseline, rather than copying failing output to obtain green results.

Read [focused local verification](references/local-verification.md). Before running CTP, initialize JDBC and prepare the selected build:

```bash
git submodule update --init cubrid-jdbc
direnv exec . just configure-build
```

Use `cubrid-build` for worktree preparation and subsequent `just build` / `just build-test`. Use `cubrid-shell-run` and the existing `just ctp::shell-debug` helper for focused shell tests; use `cubrid-sql-run` for CTP single-file SQL/medium scenarios. The local reference defines their prerequisites and proof of execution. No new framework is part of this skill; propose separate work if existing tools cannot faithfully execute the TC.

Replay each affected TC and relevant regression checks; for miscellaneous failures run the applicable check from the tested workflow with its tool versions and base/merge context. Inspect formatting diffs for unrelated indentation churn. Keep local convenience recipes out of organization-facing verification instructions.

Record command, source/test revisions and patch identities, installation identity, execution count, complete result and evidence paths for every attempt. Check actual TC identity and assertions, not just exit status. Preserve failures before retrying.

If verification fails, return to FIX-STEP within approved scope. Change the hypothesis or collect new evidence between attempts; do not loop unchanged commands without a reason. Reopen HITL if diagnosis/scope changes. A non-reproducible failure, unavailable dependency or environment mismatch remains unresolved; document the next needed observation instead of declaring success.

## 5. Review the verified changes and request push approval — HITL

Once the affected local TCs/checks pass, present the final diff, explanation, exact verification evidence and limitations, and a per-repository publication plan: source/test/docs repositories, branches, remotes, intended commits and push destinations. Explain how CI will obtain any changed testcase branch; a local testcase pass does not prove CI will consume those changes.

Ask explicitly for approval to commit/push that reviewed set and to post the necessary CI trigger comments afterward. Keep the locally verified changes unpushed until the answer arrives. Permission for one push is not standing permission for future pushes or force-pushes. Reuse authorization already given for the exact reviewed set.

Before publication, recheck PR head, remote branches, local diff and verification identities. If they changed materially, reconcile and reverify the affected changes before requesting approval for the revised set. Publish only approved repositories/commits; record receipts. On partial failure, reconcile actual remote state before retrying. Preserve each successful push and its identity.

## 6. Monitor the pushed revision and repeat

After the approved push, resolve the actual remote PR head again. Use `cubrid-ci-trigger` only within the granted comment authorization; request all three runtime suites for a full repair effort. Record the head/comment receipt. Avoid duplicate triggers while queued; an absent status is not proof that triggering failed. A same-head re-trigger needs explicit authorization unless the user already approved that specific retry.

Poll actual job/run handles at bounded intervals and preserve the work-tracker state across long waits. The analyzer collects snapshots without waiting; the repair loop performs the monitoring. Record cancellation, timeout, missing jobs and API errors distinctly. If the PR head changes externally, mark the old snapshot superseded and collect the new identity rather than mixing results.

For new failures, return to analysis and the applicable approval gate. Local retry approval survives within its scope, but every newly verified push requires its own approval. If a testcase push did not reach CI, fix the publication/selection problem before claiming an engine regression.

Finish only when the intended pushed engine/test revisions are verified, all requested runtime suites and the current PR's required checks have acceptable terminal results, and every ledger item is resolved or explicitly accepted by the user as outside scope. A missing, skipped or neutral runtime suite is not a pass; an optional/skipped miscellaneous check needs documented applicability. Unknown required-check visibility prevents a claim that the PR is ready. Report any unrelated failed checks even when the user excludes their repair. Update the ledger and work-tracker with the final evidence.
