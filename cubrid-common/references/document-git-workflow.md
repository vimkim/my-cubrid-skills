# Git workflow for persistent documents

Apply the user's Git workflow separately to every repository that receives persistent documents. Drafts, analysis reports, warning reports, and planning sheets are meaningful task changes. An investigation can preserve source repositories while committing its report in a separate repository.

## Before the first document write

1. Use the calling skill's repository path to locate the destination repository. Require it to exist, and read its applicable `AGENTS.md`, `CLAUDE.md`, and referenced procedures. Inspect its branch, worktrees, and status; preserve unrelated changes.
2. Select the checkout using the user's Git workflow. From `main`, `develop`, or `feature/*`, create or reuse a sibling task worktree on a separate topic branch and record the starting branch as the merge destination. From another named branch, use that checkout and its documented or agreed integration destination.
3. Set `ARTIFACT_WORKTREE` to the selected checkout. Record its task branch and destination checkout/branch. Resolve every document path relative to `ARTIFACT_WORKTREE`. The calling skill's discovery path identifies which repository to use; checkout selection determines where to write. Read any additional instructions in the selected checkout before writing.

Keep source revision identity separate from the document repository's commits. Preserve each skill's filename and revision conventions. Keep tool-owned raw evidence, caches, and disposable outputs in their designated locations.

## Prepare a reviewable result

Review the documents, run proportionate checks, and update any indexes required by the destination repository. Stage only intended task files and commit meaningful changes locally before handing them back. Local task commits are separate from integration and external publication; a draft-only request still permits local task commits under the user's Git workflow.

Present the document paths, source revision when applicable, task checkout/branch, local commit, checks, unrelated dirt, and proposed integration and publication operations. Follow the user's approval requirements, reusing authorization already established in the conversation. Retain the task worktree while integration awaits approval.

## Integrate and finish

After approval, follow the user's Git workflow for destination checks, rebase, validation, and fast-forward merge with `git merge --ff-only`. Use its squash fallback when needed. Follow its push policy from the destination checkout; approval to integrate into `main` includes that workflow's configured-remote push. Other branches and external systems retain their own authorization requirements.

Verify that the destination contains the reviewed documents. Resolve surviving document paths from the destination checkout for downstream uploads and the final handoff. Complete authorized publication and verification, then follow the user's worktree and branch cleanup policy, preserving valuable local files and reporting obstacles.
