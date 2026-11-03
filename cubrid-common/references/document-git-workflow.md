# Git workflow for persistent documents

Apply the user's Git workflow separately to every repository that receives persistent documents. Drafts, analysis reports, warning reports, and planning sheets are meaningful task changes. An investigation can preserve source repositories while committing its report in a separate repository.

## Before the first document write

1. Use the calling skill's repository path to locate the destination repository. Require it to exist, and read its applicable `AGENTS.md`, `CLAUDE.md`, and referenced procedures. Inspect its branch, worktrees, and status; preserve unrelated changes.
2. Select the checkout using the user's Git workflow. From `main`, `develop`, or `feature/*`, create or reuse a sibling task worktree on a separate topic branch and record the starting branch as the merge destination. From another named branch, use that checkout and its documented or agreed integration destination.
3. Set `ARTIFACT_WORKTREE` to the selected checkout. Record its task branch and destination checkout/branch. Resolve every document path relative to `ARTIFACT_WORKTREE`. The calling skill's discovery path identifies which repository to use; checkout selection determines where to write. Read any additional instructions in the selected checkout before writing.

## Name and reuse human documents

Resolve the directory before choosing a basename. Match an existing ticket directory by its complete key regardless of case, then reuse its exact on-disk spelling, even when it is empty or has no README. Create a new directory only when no matching directory exists. Inspect the destination's README index and matching documents before choosing a document path.

For new human-authored documents, use short descriptive basenames such as `ci-analysis.md`, `pr-body.md`, `pr-context.md`, or `qa-analysis.md`, regardless of the authoring agent. Add a meaningful discriminator only to distinguish retained scopes, PRs, or snapshots. Source SHA and agent suffixes are not required.

Check scope, evidence identity, user edits, and review state before updating an existing file. Extend a matching ongoing report while keeping earlier observations distinguishable. Preserve existing names, links, and separately cited historical snapshots. When a distinct report or reviewed revision must be retained, choose a separate path and explain its scope in the index when the destination's indexing rules require it.

Record exact relevant identities, such as the issue key, PR, source revision, run/attempt, and observation date, in the report or companion context. Keep uploaded bodies free of bookkeeping that does not belong in the published text. Index important documents with their purpose and relevant identity under the destination's rules; supporting files need an index entry only when those rules require one. Keep the chosen repository-relative paths through review, integration, and upload.

Keep source revision identity separate from the document repository's commits. Record it when the evidence depends on a revision; an unrelated local `HEAD` does not establish that identity. Keep tool-owned raw evidence, caches, and disposable outputs in their designated locations and retain their filenames.

## Prepare a reviewable result

Review the documents, run proportionate checks, and update any indexes required by the destination repository. Stage only intended task files and commit meaningful changes locally before handing them back. Local task commits are separate from integration and external publication; a draft-only request still permits local task commits under the user's Git workflow.

Present the document paths, source revision when applicable, task checkout/branch, local commit, checks, unrelated dirt, and proposed integration and publication operations. Follow the user's approval requirements, reusing authorization already established in the conversation. Retain the task worktree while integration awaits approval.

## Integrate and finish

After approval, follow the user's Git workflow for destination checks, rebase, validation, and fast-forward merge with `git merge --ff-only`. Use its squash fallback when needed. Follow its push policy from the destination checkout; approval to integrate into `main` includes that workflow's configured-remote push. Other branches and external systems retain their own authorization requirements.

Verify that the destination contains the reviewed documents. Resolve surviving document paths from the destination checkout for downstream uploads and the final handoff. Complete authorized publication and verification, then follow the user's worktree and branch cleanup policy, preserving valuable local files and reporting obstacles.
