# Preserve TC isolation until the engine merge

Keep each engine PR's testcase changes on `tc/pr-<engine PR number>` in both `CUBRID/cubrid-testcases` and `CUBRID/cubrid-testcases-private-ex`. Keep the associated TC PRs open during development, review, and CI, including TC PRs with no changes. Finalize them only in the last handoff immediately before the engine PR merge.

## Interpret the gate at the right stage

Before acting, inspect the selected base's current TC sync, merge-gate, and finalization workflows. The `develop` workflow uses `TC Merge Gate / Check TC PRs`. Do not assume that feature or release bases use the same gate.

| Observed state | Next action |
|---|---|
| Review is unfinished, another applicable CI check is pending or failed, or the current revisions are unverified | Keep the TC PRs open. Finish review, verification, or CI work. |
| The TC gate reports open TC PRs while review or other CI continues | Report the gate as deferred to the final merge handoff. Do not ask the user to close or merge TC PRs now. |
| The gate cannot read a repository or reports unexplained unlanded content | Report the lookup or content problem. Resolve the uncertainty while preserving the TC branches. |
| Reviews and other CI are complete, but no engine merge is authorized or ready to execute | Keep TC PRs open. Report readiness for the final handoff without requesting TC closure now. |
| Reviews are complete, all other applicable CI has passed, and the engine merge is authorized and ready to execute | Begin the final handoff below. |

An isolation-related TC gate failure is not a regression-suite failure. Report both the observed gate result and its deferred action. Do not call the PR fully green or mergeable while this gate remains blocked. A status request, CI trigger, or CI analysis does not authorize TC finalization or an engine merge.

## Complete one final merge handoff

1. Recheck the engine PR's current head and base, completed reviews, and all other applicable CI results. Include required checks and any additional CI the user requested. Confirm that evidence covers the intended engine and TC revisions. Missing, stale, or unexplained results leave the handoff unready.
2. Inspect both testcase repositories' current `tc/pr-N` tips, TC PR reviews, diffs, and actual target branches. Resolve required approvals for TC publication and the engine merge before changing either TC PR. Reuse authorization already given for these operations.
3. Merge TC PRs carrying changes into their intended testcase targets. Close a TC PR without merging only after proving it has no unlanded changes. A closed TC PR alone does not prove that its content landed.
4. Refresh the applicable TC gate. For `develop`, rerun `TC Merge Gate / Check TC PRs` and verify its fresh verdict for the current engine head. A rerun of unrelated CI does not rejudge this gate. Confirm that neither testcase branch retains unlanded changes.
5. Recheck the engine head, reviews, and other applicable checks, then proceed directly to the authorized engine PR merge. A changed head, changed TC content, or new blocker returns the task to verification.

GitHub does not provide a transaction across these repositories. Prepare permissions and review before step 3 to keep the handoff close to atomic. If the engine merge fails or must wait after TC finalization, report which TC changes already landed and the remaining blocker. Preserve the remaining branches and reassess readiness before retrying. Do not claim continued isolation or automatically revert published TC changes.

The engine's TC finalizer can close remaining TC PRs and delete `tc/pr-N` after the engine PR closes. Preserve changed cases through the TC merge before relying on that cleanup.
