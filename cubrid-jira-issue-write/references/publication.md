# Artifact and publication workflow

Read this reference before choosing the report path. Use its review and publication steps after the saved report passes the review in `SKILL.md`. Explicit requests for a local draft or another publication limit take precedence. Editing this skill or discussing issue-writing guidance is not a request to publish an issue.

## Artifact and output requirements

- **Repository and checkout**: Locate the existing repository at `/home/vimkim/gh/my-cubrid-jira`. If it is absent, stop and tell the user to clone/create it. Before creating report files or directories, follow [Document Git workflow](../../cubrid-common/references/document-git-workflow.md) and select `ARTIFACT_WORKTREE`. Require `origin` fetch and push URLs to resolve to `github.com/vimkim/my-cubrid-jira` in HTTPS or SSH form.
- **Save location**: `issues/CBRD-XXXXX-short-slug_<SHORT_SHA>_<AGENT>.md`, relative to `ARTIFACT_WORKTREE`. If no ticket number is known, ask whether one should be supplied; only after the user confirms this is a ticket-free draft, use `issues/descriptive-slug_<SHORT_SHA>_<AGENT>.md`.
- **Characters**: use BMP text and no emoji for JIRA compatibility. Korean/CJK, box-drawing characters, ordinary typography, and ASCII forms are allowed when they aid readability. Follow the language, heading, and audience rules in `SKILL.md`.

## Review and publication contract

A writing request starts local preparation: write, review, and commit the report in the selected task checkout. Present the proposed notes integration, push, and matching live JIRA description update together. Obtain the approval required by the user's Git workflow and authorization for the JIRA update before executing those operations. Reuse applicable authorization already established in the conversation; skill invocation alone does not replace it.

Keep publication inside these boundaries:

- Follow the Document Git workflow for task commits, approved rebase/fast-forward integration, push, and cleanup. Include required repository indexes alongside the report; preserve unrelated changes.
- Require the issue key derived from the filename to equal the JIRA target key.
- Push the Markdown commit successfully before the live JIRA update. If the push fails, stop before uploading.
- Use the `cubrid-jira` skill's publish-description workflow, including its dry-run, live update with `--yes`, and live read-back verification.
- If the live update fails after the push, keep the pushed commit, report the exact JIRA error and the partial-completion state, and do not claim success.

A ticket-free draft has no upload target. Prepare its local task commit and follow the same approval rules for integration and push, then report that no JIRA upload target exists. Creating a new JIRA issue is a separate workflow requiring the project, issue type, summary, and other required fields.

## Artifact Identity

Resolve the filename before writing the draft:

1. Set `SOURCE_COMMIT` to the specific CUBRID commit or PR head analyzed by the issue when one is supplied. Otherwise use `git rev-parse HEAD` in the current CUBRID worktree. Never use the `my-cubrid-jira` repository commit. If no relevant CUBRID commit or worktree can be identified, ask the user.
2. Validate `SOURCE_COMMIT` and take its first seven hexadecimal characters as `SHORT_SHA`.
3. Set `AGENT` from the active AI host's runtime identity. Use `codex` for Codex and `claude` for Claude Code. For another host, use its stable lowercase agent name. Do not infer the host from installed binaries because multiple AI CLIs may coexist; if runtime identity is unclear, ask the user.
4. Compute the repository-relative path once and resolve it under `ARTIFACT_WORKTREE` as `issue_file`. Reuse that report through revision. After integration, resolve the same relative path from the destination checkout for upload and final handoff. The basename must end with `_<SHORT_SHA>_<AGENT>.md`.

For example, Codex documenting `f5794fb...` writes `CBRD-26972-oos-show-heap-capacity_f5794fb_codex.md`; Claude Code writes `CBRD-26972-oos-show-heap-capacity_f5794fb_claude.md`.

## Review, integrate, and publish the report

1. Validate the notes repository, remote, target key, and reviewed report against this contract. Complete the Document Git workflow's local checks and task commit, including required repository indexes. Verify that the commit contains only intended task files.
2. Present the report path, source commit, agent name, recommended JIRA type and categories, Issue Triage block, task checkout/branch, local commit, checks, and proposed integration and publication operations. Ask once for any outstanding approval. For a draft-only request, hand back the local task commit within that limit. Otherwise continue when authorization covers the listed operations.
3. Integrate and push through the Document Git workflow. If the report is already committed or integrated, verify its reviewed contents and complete only the remaining authorized operations. Resolve `issue_file` from the destination checkout and verify that the pushed destination branch contains the reviewed report. A failure stops the workflow before the live JIRA update.
4. For an authorized keyed upload, hand off the matching ticket key and surviving absolute `issue_file` to the `cubrid-jira` skill's publish-description workflow with authorization established in the conversation. It performs the dry-run, target check, live `--yes` update, and read-back verification. A ticket-free draft or a user publication limit skips the upload.
5. Complete authorized publication verification and worktree cleanup. Report the surviving report path, local/integrated commit and pushed branch when applicable; for a published keyed report, include the live JIRA URL and read-back result. Distinguish a locally committed draft from completed publication. Report the exact error and completed stages on failure.
