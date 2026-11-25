# Preserve TC isolation until the engine merge

Keep each engine PR's testcase changes on `tc/pr-<engine PR number>` in both `CUBRID/cubrid-testcases` and `CUBRID/cubrid-testcases-private-ex`. Keep the associated TC PRs open during development, review, and CI, including TC PRs with no changes. Finalize them only in the last handoff immediately before the engine PR merge.

For TC-only changes with no engine code edits targeting `develop` or `feature/**`, follow [TC-only changes (CI-carrier draft engine PR)](#tc-only-changes-ci-carrier-draft-engine-pr) instead of opening a standalone PR directly in a testcase repository.

## Interpret the gate at the right stage

Before acting, inspect the selected base's current TC sync, merge-gate, and finalization workflows. The `develop` workflow uses `TC Merge Gate / Check TC PRs`. Do not assume that feature or release bases use the same gate. Use the [PR approval gate](../SKILL.md#pr-approval-gate) for the engine PR and each TC PR that needs a merge.

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
2. Inspect both testcase repositories' current `tc/pr-N` tips, TC PR diffs, and actual target branches. Apply the approval gate to every planned merge before asking for merge permission. Resolve TC publication and engine merge authorization before changing either TC PR. Reuse authorization already given for these operations.
3. Rerun the approval checker immediately before each TC merge and show the result. Merge TC PRs carrying changes into their intended testcase targets once the gate is satisfied or explicitly waived. Close a TC PR without merging only after proving it has no unlanded changes. A closed TC PR alone does not prove that its content landed.
4. Refresh the applicable TC gate. For `develop`, rerun `TC Merge Gate / Check TC PRs` and verify its fresh verdict for the current engine head. A rerun of unrelated CI does not rejudge this gate. Confirm that neither testcase branch retains unlanded changes.
5. Recheck the engine head and applicable checks. Rerun the approval checker and show the result immediately before the authorized engine merge. A changed head, changed TC content, or new blocker returns the task to verification.

The user runs this handoff with `/cubrid-pr-merge <engine PR>`, which shows every squash commit message before `pr-final-merge-handoff execute`. Each merge uses a message from the [Squash commit message convention](squash-message.md), never GitHub's default commit list.

GitHub does not provide a transaction across these repositories. Prepare permissions and review before step 3 to keep the handoff close to atomic. If the engine merge fails or must wait after TC finalization, report which TC changes already landed and the remaining blocker. Preserve the remaining branches and reassess readiness before retrying. Do not claim continued isolation or automatically revert published TC changes.

The engine's TC finalizer can close remaining TC PRs and delete `tc/pr-N` after the engine PR closes. Preserve changed cases through the TC merge before relying on that cleanup.

## TC-only changes (CI-carrier draft engine PR)

`gha-ci` runs only against an open `CUBRID/cubrid` PR targeting `develop` or `feature/**` and checks out `tc/pr-<engine PR number>` from both `CUBRID/cubrid-testcases` and `CUBRID/cubrid-testcases-private-ex`. A standalone PR opened directly in a testcase repository has no linked `CUBRID/cubrid` PR or `tc/pr-<N>` branch, so `gha-ci` cannot test it directly. Use a CI-carrier draft engine PR for TC-only changes targeting `develop` or `feature/**`. Bases without `TC Branch Sync` or `gha-ci` (such as `release/*` backports) remain standalone TC-repository PRs unless the user instructs otherwise.

1. **Create a CI-carrier draft engine PR**: Create a ticket branch off `origin/<base>` (`develop` or `feature/<name>`) in `CUBRID/cubrid` (for example, `CBRD-NNNNN` or `CBRD-NNNNN-<summary>`; skip build setup such as `cubrid-worktree create <branch> --base origin/<base> --no-prepare` because no engine files change). Record one empty commit (`git commit --allow-empty -m "[CBRD-NNNNN] ..."`) so GitHub accepts the PR. Prepare and, after user confirmation, open a **draft** PR in `CUBRID/cubrid` targeting `<base>` via `cubrid-pr-create`. State clearly in `Remarks` that the draft engine PR exists only to provision `tc/pr-<N>` and run `gha-ci`, that only the TC PR will be merged, and that the draft engine PR will be closed without merging.
2. **Wait for `TC Branch Sync` and push TC changes to `tc/pr-<N>`**: Opening the draft engine PR triggers `TC Branch Sync` (`tc-branch-sync.yml`), which creates `tc/pr-<N>` (with an empty init commit) and a draft TC PR in both `CUBRID/cubrid-testcases` and `CUBRID/cubrid-testcases-private-ex` (branching from `<base>`, falling back to `develop` when `<base>` does not exist in a TC repository). Wait for `TC Branch Sync` to finish and verify the created `tc/pr-<N>` branches and PRs. In each affected TC repository, fetch `origin`, apply and commit the TC changes on top of `origin/tc/pr-<N>`, and push to `origin tc/pr-<N>` once push authorization is established. Update the changed TC PR's title and body and mark it ready for review when ready; leave any unchanged TC PR as draft.
3. **Verify with `cubrid-ci-trigger`**: Trigger `gha-ci` on the draft engine PR (`CUBRID/cubrid#<N>`) via `cubrid-ci-trigger` (such as `/run <affected-suite>` or `/run all` for the first run, and `/run rerun <run-id>` for subsequent TC-only edits under `cases/` or `answers/` on the same engine head). Expect `TC Merge Gate / Check TC PRs` to report blocked while TC PRs remain open; this does not block closing the draft engine PR because the engine PR is never merged.
4. **Approve and merge ONLY the changed TC PR(s), then close the engine PR**: Apply the [PR approval gate](../SKILL.md#pr-approval-gate) (`cubrid-pr-approval-check`) to every TC PR carrying changes before requesting merge permission and again immediately before each TC merge. **Always merge the approved changed TC PR(s) first, before closing the draft engine PR.** Squash-merge each with a message from the [Squash commit message convention](squash-message.md) (`gh pr merge <n> --squash --subject "<title>" --body-file <body>` after `pr-final-merge-handoff lint-message`). Once every changed TC PR is merged, close the draft engine PR without merging (`gh pr close <N> --repo CUBRID/cubrid`); do not merge the empty-commit engine PR.
5. **Automatic cleanup**: Closing the engine PR triggers `TC Branch Finalize` (`tc-branch-finalize.yml`), which closes any remaining open draft TC PR (the unchanged repository's draft PR) and deletes `tc/pr-<N>` in both testcase repositories. Closing the engine PR before merging a changed TC PR closes that TC PR unmerged and deletes `tc/pr-<N>`, losing unlanded TC changes.
