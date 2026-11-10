# Artifact and publication workflow

Read this reference before choosing the report path. Use its review and publication steps after the saved report passes the review in `SKILL.md`. Review-only and local-draft requests stop at the requested result; other publication limits also take precedence. Editing this skill or discussing issue-writing guidance is not a request to publish an issue.

## Artifact and output requirements

- **Repository and checkout**: Locate the existing repository at `/home/vimkim/gh/my-cubrid-jira`. If it is absent, stop and tell the user to clone/create it. Before creating report files or directories, follow [Document Git workflow](../../cubrid-common/references/document-git-workflow.md) and select `ARTIFACT_WORKTREE`. Require `origin` fetch and push URLs to resolve to `github.com/vimkim/my-cubrid-jira` in HTTPS or SSH form.
- **Save location**: Reuse the matching issue file under `issues/` in `ARTIFACT_WORKTREE`. For a new keyed file, use `issues/CBRD-<number>-short-slug.md`; retain the complete issue key for upload validation. With no key, save a ticket-free local draft as `issues/descriptive-slug.md` without asking for a key merely to draft. Apply the shared document naming rules.
- **Characters**: use BMP text and no emoji for JIRA compatibility. Korean/CJK, box-drawing characters, ordinary typography, and ASCII forms are allowed when they aid readability. Follow the language, heading, and audience rules in `SKILL.md`.

## Review and publication contract

A writing request starts local preparation: write, review, and commit the report in the selected task checkout. Present the proposed notes integration, push, and matching live JIRA description update together. Obtain the approval required by the user's Git workflow and authorization for the JIRA update before executing those operations. Reuse applicable authorization already established in the conversation; skill invocation alone does not replace it.

Keep publication inside these boundaries:

- Follow the Document Git workflow for task commits, approved rebase/fast-forward integration, push, and cleanup. Include required repository indexes alongside the report; preserve unrelated changes.
- Extract the complete issue key from the basename and require exact equality with the JIRA target key, using the delimiter-aware check in `cubrid-jira`.
- Push the Markdown commit successfully before the live JIRA update. If the push fails, stop before uploading.
- Use the `cubrid-jira` skill's publish-description workflow, including its dry-run, live update with `--yes`, and live read-back verification.
- If the live update fails after the push, keep the pushed commit, report the exact JIRA error and the partial-completion state, and do not claim success.

A ticket-free draft has no upload target. Prepare its local task commit and follow the same approval rules for integration and push, then report that no JIRA upload target exists. Creating a new JIRA issue is a separate workflow requiring the project, issue type, summary, and other required fields.

## Artifact identity

Inspect existing issue files and the index before choosing the path. Reuse the matching issue file, preserving user edits, review state, and historical references under the shared naming rules. Compute the repository-relative path once and resolve it under `ARTIFACT_WORKTREE` as `issue_file`. After integration, resolve that same path from the destination checkout for upload and handoff.

Record a source revision only when the issue's evidence depends on it. Use the exact analyzed commit, PR head, or build identity from that evidence. Do not substitute an unrelated local `HEAD` or the notes repository commit. If a relevant revision is unresolved, state that limitation and keep claims bounded; revision-independent drafts, including administrative issues, do not require an engine SHA. Keep publication bookkeeping in the index or supporting context when it does not belong in the issue body.

## Review, integrate, and publish the report

1. Validate the notes repository, remote, target key, and reviewed report against this contract. Run the shared link check required by `SKILL.md` on the report and shared supporting documents before review and the local task commit. Complete the Document Git workflow's local checks and task commit, including required repository indexes. Verify that the commit contains only intended task files.
2. Present the report path, relevant source identity when available, recommended JIRA type and categories, the duplicate-check result from `SKILL.md` step 5, one-line summary and Issue Triage block, proposed title and existing live summary when applicable, task checkout/branch, local commit, checks, and proposed integration and publication operations. Ask once for any outstanding approval. For a draft-only request, hand back the local task commit within that limit. Otherwise continue when authorization covers the listed operations.
3. Before publishing, rerun the shared link check on the report and shared supporting documents without rewriting approved text; return necessary changes to review. Integrate and push through the Document Git workflow. If the report is already committed or integrated, verify its reviewed contents and complete only the remaining authorized operations. Resolve `issue_file` from the destination checkout and verify that the pushed destination branch contains the reviewed report. A failure stops the workflow before the live JIRA update.
4. For an authorized keyed upload, hand off the matching ticket key and surviving absolute `issue_file` to the `cubrid-jira` skill's publish-description workflow with authorization established in the conversation. It performs the dry-run, target check, live `--yes` update, and read-back verification. A ticket-free draft or a user publication limit skips the upload.
5. Complete authorized publication verification and worktree cleanup. Report the surviving report path, local/integrated commit and pushed branch when applicable; for a published keyed report, include the live JIRA URL and read-back result. Distinguish a locally committed draft from completed publication. Report the exact error and completed stages on failure.
